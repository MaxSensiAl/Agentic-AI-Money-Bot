import os
import json
import random
import time
import requests
import feedparser
import re
import hashlib
import pickle
from datetime import datetime, timedelta
import threading
import socket

# ============================================
# CONFIGURATION
# ============================================

BLOG_ID = os.getenv('BLOG_ID')
SHRINKME_API = os.getenv('SHRINKME_API')
HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('GEMINI_API')

BC_CLIENT_ID = os.getenv('BC_CLIENT_ID')
BC_CLIENT_SECRET = os.getenv('BC_CLIENT_SECRET')
BC_REFRESH_TOKEN = os.getenv('BC_REFRESH_TOKEN')

# ============================================
# FILES FOR STORAGE
# ============================================

POST_QUEUE_FILE = 'post_queue.pkl'
POST_HISTORY_FILE = 'post_history.json'
NEXT_POST_FILE = 'next_post.pkl'
LAST_FETCH_TIME = 'last_fetch.txt'

# ============================================
# RSS SOURCES (30+ Categories)
# ============================================

RSS_SOURCES = [
    # Technology
    {"url": "https://techcrunch.com/feed/", "category": "Technology"},
    {"url": "https://www.theverge.com/rss/index.xml", "category": "Technology"},
    {"url": "https://www.cnet.com/rss/news/", "category": "Technology"},
    {"url": "https://www.wired.com/feed/rss", "category": "Technology"},
    {"url": "https://arstechnica.com/feed/", "category": "Technology"},
    
    # Gaming
    {"url": "https://www.gamespot.com/feeds/game-news/", "category": "Gaming"},
    {"url": "https://www.ign.com/rss/articles/all", "category": "Gaming"},
    {"url": "https://www.polygon.com/rss/index.xml", "category": "Gaming"},
    
    # Entertainment
    {"url": "https://www.variety.com/feed/", "category": "Entertainment"},
    {"url": "https://www.hollywoodreporter.com/feed/", "category": "Entertainment"},
    {"url": "https://www.pinkvilla.com/feed", "category": "Bollywood"},
    {"url": "https://www.eonline.com/news/rss", "category": "Entertainment"},
    
    # Space
    {"url": "https://www.nasa.gov/rss/dyn/breaking_news.rss", "category": "Space"},
    {"url": "https://www.space.com/feeds/all", "category": "Space"},
    
    # Business
    {"url": "https://www.bloomberg.com/feeds/markets.rss", "category": "Business"},
    {"url": "https://www.reuters.com/rss/reuters-business-news.rss", "category": "Business"},
    
    # Sports
    {"url": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml", "category": "Sports"},
    
    # Music
    {"url": "https://www.rollingstone.com/music/music-news/feed/", "category": "Music"},
    {"url": "https://www.billboard.com/feed/", "category": "Music"},
    
    # World News
    {"url": "https://feeds.npr.org/1001/rss.xml", "category": "World News"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "World News"},
    
    # AI
    {"url": "https://www.artificialintelligence-news.com/feed/", "category": "AI"},
]

# ============================================
# POST QUEUE SYSTEM
# ============================================

class PostQueue:
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()
        self.load()
    
    def load(self):
        try:
            if os.path.exists(POST_QUEUE_FILE):
                with open(POST_QUEUE_FILE, 'rb') as f:
                    self.queue = pickle.load(f)
        except:
            self.queue = []
    
    def save(self):
        try:
            with open(POST_QUEUE_FILE, 'wb') as f:
                pickle.dump(self.queue, f)
        except:
            pass
    
    def add(self, post_data):
        with self.lock:
            # Check duplicate in queue
            for q in self.queue:
                if q.get('title') == post_data.get('title'):
                    return False
            self.queue.append(post_data)
            self.save()
            return True
    
    def get(self):
        with self.lock:
            if self.queue:
                post = self.queue.pop(0)
                self.save()
                return post
            return None
    
    def size(self):
        return len(self.queue)
    
    def peek(self):
        if self.queue:
            return self.queue[0]
        return None

post_queue = PostQueue()

# ============================================
# POST HISTORY (Duplicate Check)
# ============================================

def load_history():
    try:
        if os.path.exists(POST_HISTORY_FILE):
            with open(POST_HISTORY_FILE, 'r') as f:
                return json.load(f)
        return []
    except:
        return []

def save_history(title):
    history = load_history()
    if title not in history:
        history.append(title)
        if len(history) > 1000:
            history = history[-1000:]
        with open(POST_HISTORY_FILE, 'w') as f:
            json.dump(history, f)

def is_posted_before(title):
    history = load_history()
    title_hash = hashlib.md5(title.lower().encode()).hexdigest()
    for old_title in history:
        if hashlib.md5(old_title.lower().encode()).hexdigest() == title_hash:
            return True
    return False

# ============================================
# NEXT POST TRACKING
# ============================================

def save_next_post_time(post_time):
    try:
        with open(NEXT_POST_FILE, 'wb') as f:
            pickle.dump(post_time, f)
    except:
        pass

def get_next_post_time():
    try:
        if os.path.exists(NEXT_POST_FILE):
            with open(NEXT_POST_FILE, 'rb') as f:
                return pickle.load(f)
    except:
        pass
    return None

# ============================================
# TRENDING NEWS FETCHER
# ============================================

def fetch_trending_news():
    """Background mein trending news fetch karega"""
    print("🔍 [FETCHER] Starting background fetcher...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    while True:
        try:
            # Check if queue needs more posts
            queue_size = post_queue.size()
            print(f"📊 [FETCHER] Queue size: {queue_size}")
            
            # Agar queue 10 se kam hai toh fetch karo
            if queue_size < 10:
                print("🔄 [FETCHER] Queue low, fetching fresh news...")
                
                random.shuffle(RSS_SOURCES)
                
                for source in RSS_SOURCES:
                    try:
                        response = requests.get(source["url"], headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            feed = feedparser.parse(response.content)
                            if feed.entries:
                                for entry in feed.entries[:5]:
                                    title = re.sub(r'\s+', ' ', entry.title).strip()
                                    
                                    # Check if already posted
                                    if is_posted_before(title):
                                        continue
                                    
                                    # Check if already in queue
                                    in_queue = False
                                    for q in post_queue.queue:
                                        if q.get('title') == title:
                                            in_queue = True
                                            break
                                    
                                    if in_queue:
                                        continue
                                    
                                    # Add to queue
                                    post_data = {
                                        'title': title,
                                        'link': entry.link,
                                        'summary': entry.get('summary', ''),
                                        'category': source["category"],
                                        'fetched_at': datetime.now().isoformat(),
                                        'entry': entry
                                    }
                                    
                                    post_queue.add(post_data)
                                    print(f"✅ [FETCHER] Added: {title[:50]}... ({source['category']})")
                                    
                                    if post_queue.size() >= 15:
                                        break
                            
                            if post_queue.size() >= 15:
                                break
                    except:
                        continue
                
                # Save last fetch time
                with open(LAST_FETCH_TIME, 'w') as f:
                    f.write(datetime.now().isoformat())
                
                print(f"📊 [FETCHER] Queue now: {post_queue.size()} posts ready")
            else:
                print(f"✅ [FETCHER] Queue full ({queue_size} posts), sleeping...")
            
            # 2 minute wait before checking again
            time.sleep(120)
            
        except Exception as e:
            print(f"❌ [FETCHER Error] {e}")
            time.sleep(60)

# ============================================
# BLOGGER POST FUNCTION
# ============================================

def post_to_blogger(title, content, category):
    """Post to Blogger"""
    try:
        # Refresh token
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": BC_CLIENT_ID,
            "client_secret": BC_CLIENT_SECRET,
            "refresh_token": BC_REFRESH_TOKEN,
            "grant_type": "refresh_token"
        }
        res = requests.post(token_url, data=payload, timeout=15)
        access_token = res.json().get("access_token")
        
        if not access_token:
            return False
        
        # Post
        post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        post_body = {
            "kind": "blogger#post",
            "title": title[:60],
            "content": content,
            "labels": ["Breaking News", category, "Trending", datetime.now().strftime("%Y")]
        }
        
        post_res = requests.post(post_url, headers=headers, json=post_body, timeout=20)
        
        if post_res.status_code in [200, 201]:
            result = post_res.json()
            print(f"✅ POSTED! URL: {result.get('url')}")
            save_history(title)
            return True
        
        return False
    except Exception as e:
        print(f"❌ Post Error: {e}")
        return False

# ============================================
# GENERATE CONTENT
# ============================================

def generate_content(title, summary, category):
    """Generate SEO content (AI or Fallback)"""
    # Try AI first
    if HF_TOKEN:
        try:
            prompt = f"""Write a 500-word news article about: {title}. 
            Category: {category}. Use HTML tags: h2, h3, p, ul, li.
            Include Key Highlights section."""
            
            API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
            headers = {
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {
                "inputs": prompt,
                "parameters": {"max_new_tokens": 600, "temperature": 0.7}
            }
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get('generated_text', '')
                    if len(text) > 100:
                        return text
        except:
            pass
    
    # Fallback content
    today = datetime.now().strftime("%B %d, %Y")
    return f"""
    <h2>Breaking News: {title}</h2>
    
    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
        <p><strong>📅 Published:</strong> {today} | <strong>📂 Category:</strong> {category}</p>
    </div>
    
    <p>{summary[:500]}...</p>
    
    <h3>Key Highlights</h3>
    <ul>
        <li>🔴 Major development in {category}</li>
        <li>📈 Trending story today</li>
        <li>🌍 Global attention</li>
        <li>📰 Full details inside</li>
    </ul>
    
    <blockquote style="border-left: 5px solid #ff5722; padding: 20px; background: #f9f9f9; border-radius: 8px;">
        <p>This is a developing story. Click the button below for complete coverage.</p>
    </blockquote>
    """

def get_short_url(long_url):
    """Shorten URL"""
    try:
        if not SHRINKME_API:
            return long_url
        url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={long_url}&format=text"
        response = requests.get(url, timeout=10)
        return response.text.strip() if response.text else long_url
    except:
        return long_url

# ============================================
# PROCESS POST (Complete - 1 Hour)
# ============================================

def process_and_post():
    """Ek post process karega aur post karega"""
    
    print("\n" + "="*60)
    print(f"⏰ POSTING TIME: {datetime.now().strftime('%H:%M:%S - %B %d, %Y')}")
    print("="*60)
    
    # Check if queue has posts
    if post_queue.size() == 0:
        print("⚠️ Queue empty! Running emergency fetch...")
        emergency_fetch()
        
        # Wait for fetch to complete
        time.sleep(10)
        
        if post_queue.size() == 0:
            print("❌ No posts available in queue!")
            return
    
    # Get post from queue
    post_data = post_queue.get()
    
    if not post_data:
        print("❌ No post data available")
        return
    
    title = post_data['title']
    link = post_data['link']
    summary = post_data['summary']
    category = post_data['category']
    
    # Double-check duplicate
    if is_posted_before(title):
        print(f"⚠️ Duplicate found, trying next post...")
        # Try next post from queue
        process_and_post()
        return
    
    print(f"\n📰 POSTING: {title}")
    print(f"📂 Category: {category}")
    print(f"📊 Queue remaining: {post_queue.size()} posts")
    
    # Generate content
    print("🤖 Generating content...")
    content = generate_content(title, summary, category)
    
    # Short link
    print("🔗 Shortening link...")
    short_link = get_short_url(link)
    print(f"✅ Short link: {short_link}")
    
    # Earning Button
    button = f"""
    <div style="text-align: center; margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #fff5f0, #fff); border-radius: 12px;">
        <a href="{short_link}" target="_blank" 
           style="background: linear-gradient(135deg, #ff5722, #ff6f00); 
                  color: white; padding: 18px 50px; font-size: 20px; 
                  font-weight: bold; border-radius: 50px; 
                  text-decoration: none; display: inline-block;
                  box-shadow: 0 8px 25px rgba(255,87,34,0.4);">
            📖 READ FULL STORY HERE
        </a>
        <p style="font-size: 12px; color: #999; margin-top: 10px;">
            Click to read the complete story on the original source
        </p>
    </div>
    """
    
    final_content = f"{content}{button}"
    
    # Post
    print("📝 Posting to Blogger...")
    if post_to_blogger(title, final_content, category):
        print("\n" + "="*60)
        print("✅ PROCESS COMPLETED SUCCESSFULLY!")
        print(f"📰 Title: {title[:60]}")
        print(f"📂 Category: {category}")
        print(f"🔗 Short Link: {short_link}")
        print(f"📊 Queue remaining: {post_queue.size()}")
        print("="*60 + "\n")
        return True
    else:
        print("❌ Failed to post, putting back in queue")
        post_queue.add(post_data)
        return False

def emergency_fetch():
    """Emergency fetch if queue empty"""
    print("🚨 EMERGENCY FETCH in progress...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for source in RSS_SOURCES[:15]:
        try:
            response = requests.get(source["url"], headers=headers, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                if feed.entries:
                    for entry in feed.entries[:3]:
                        title = re.sub(r'\s+', ' ', entry.title).strip()
                        if not is_posted_before(title):
                            post_data = {
                                'title': title,
                                'link': entry.link,
                                'summary': entry.get('summary', ''),
                                'category': source["category"],
                                'entry': entry
                            }
                            post_queue.add(post_data)
                            print(f"✅ Emergency: {title[:50]}...")
                            if post_queue.size() >= 5:
                                return
        except:
            continue
    
    print("⚠️ Emergency fetch done, adding default fallback...")
    # Fallback - Add a default post
    post_data = {
        'title': f"Latest {random.choice(['Technology', 'Gaming', 'Entertainment', 'Space', 'Business'])} News Update - {datetime.now().strftime('%B %d, %Y')}",
        'link': 'https://example.com',
        'summary': 'Latest news update for today.',
        'category': random.choice(['Technology', 'Gaming', 'Entertainment', 'Space', 'Business']),
        'entry': None
    }
    post_queue.add(post_data)

# ============================================
# START BACKGROUND FETCHER
# ============================================

def start_background_fetcher():
    """Start background fetcher thread"""
    print("🚀 Starting background news fetcher...")
    thread = threading.Thread(target=fetch_trending_news, daemon=True)
    thread.start()
    return thread

# ============================================
# MAIN FUNCTION
# ============================================

def main():
    print("="*60)
    print("🤖 TRENDING NEWS AUTO-POST SYSTEM")
    print("="*60)
    print("📋 Features:")
    print("   ✅ 1 post per hour")
    print("   ✅ Background news fetch")
    print("   ✅ Auto queue management")
    print("   ✅ No duplicates")
    print("   ✅ 30+ categories")
    print("="*60 + "\n")
    
    # Start background fetcher
    fetcher_thread = start_background_fetcher()
    
    # Initial fetch - Fill queue
    print("⏳ Initial fetch in progress...")
    time.sleep(5)
    
    # First post - Check if queue has posts
    if post_queue.size() == 0:
        print("📥 Queue empty, fetching initial news...")
        emergency_fetch()
    
    print(f"📊 Initial queue size: {post_queue.size()} posts ready\n")
    
    # Main loop - Post every hour
    post_count = 0
    
    while True:
        try:
            # Process and post
            success = process_and_post()
            
            if success:
                post_count += 1
                print(f"📊 Total posts today: {post_count}")
            
            # Next post time calculation
            now = datetime.now()
            next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            wait_seconds = (next_hour - now).total_seconds()
            
            print(f"⏰ Next post at: {next_hour.strftime('%H:%M:%S')}")
            print(f"⏳ Waiting {int(wait_seconds)} seconds...\n")
            
            # Sleep until next hour
            time.sleep(wait_seconds)
            
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
            break
        except Exception as e:
            print(f"❌ Main loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
