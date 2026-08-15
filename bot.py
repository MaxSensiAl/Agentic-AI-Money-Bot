import os
import json
import random
import time
import requests
import feedparser
import re
from datetime import datetime, timedelta
import socket

# --- DNS FIX ---
def fix_dns():
    try:
        socket.gethostbyname('api-inference.huggingface.co')
    except:
        print("DNS fix applied")

# --- CONFIGURATION ---
BLOG_ID = os.getenv('BLOG_ID')
SHRINKME_API = os.getenv('SHRINKME_API')
HF_TOKEN = os.getenv('HF_TOKEN')

BC_CLIENT_ID = os.getenv('BC_CLIENT_ID')
BC_CLIENT_SECRET = os.getenv('BC_CLIENT_SECRET')
BC_REFRESH_TOKEN = os.getenv('BC_REFRESH_TOKEN')

# --- RSS FEEDS ---
RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.cnet.com/rss/news/",
    "https://www.gamespot.com/feeds/game-news/",
    "https://www.ign.com/rss/articles/all",
    "https://www.variety.com/feed/",
    "https://www.hollywoodreporter.com/feed/",
    "https://www.pinkvilla.com/feed",
    "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "https://www.space.com/feeds/all",
    "https://www.bloomberg.com/feeds/markets.rss",
    "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
    "https://www.rollingstone.com/music/music-news/feed/",
]

# --- IMAGE SOURCES ---
UNSPLASH_IMAGES = {
    "Technology": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
    "Gaming": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80",
    "Entertainment": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80",
    "Space": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
    "Sports": "https://images.unsplash.com/photo-1531415074968-036ba1b575da?auto=format&fit=crop&w=1200&q=80",
    "Business": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80",
    "Music": "https://images.unsplash.com/photo-1511735111819-9a3f7709049c?auto=format&fit=crop&w=1200&q=80",
}

# --- POSTED NEWS TRACKING ---
POSTED_FILE = 'posted_news.txt'

def clean_and_format_title(title):
    """Clean title - keep year, remove duplicates"""
    if not title:
        return ""
    clean = re.sub(r'\s+', ' ', title).strip()
    # Remove duplicate year patterns
    clean = re.sub(r'202[0-9]\s*[-|]\s*202[0-9]', '2026', clean)
    clean = re.sub(r'\s*[-|]\s*$', '', clean)
    return clean[:70].strip()

def load_posted_news():
    try:
        if os.path.exists(POSTED_FILE):
            with open(POSTED_FILE, 'r', encoding='utf-8') as f:
                return set(clean_and_format_title(line.strip()).lower() for line in f if line.strip())
    except:
        pass
    return set()

def save_posted_news(title):
    try:
        cleaned = clean_and_format_title(title)
        with open(POSTED_FILE, 'a', encoding='utf-8') as f:
            f.write(cleaned + '\n')
    except:
        pass

# --- FUNCTIONS ---

def get_blogger_access_token():
    try:
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": BC_CLIENT_ID,
            "client_secret": BC_CLIENT_SECRET,
            "refresh_token": BC_REFRESH_TOKEN,
            "grant_type": "refresh_token"
        }
        res = requests.post(token_url, data=payload, timeout=15)
        return res.json().get("access_token")
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_all_blogger_titles(access_token):
    existing_titles = set()
    if not access_token:
        return existing_titles
    try:
        page_token = None
        total = 0
        while True:
            url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?maxResults=100"
            if page_token:
                url += f"&pageToken={page_token}"
            headers = {"Authorization": f"Bearer {access_token}"}
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                break
            data = res.json()
            posts = data.get("items", [])
            for post in posts:
                title = clean_and_format_title(post.get("title", "")).lower().strip()
                if title:
                    existing_titles.add(title)
                    total += 1
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        print(f"📥 Total {total} posts loaded")
        return existing_titles
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return existing_titles

def is_duplicate_title(new_title, existing_titles):
    """Smart duplicate - 80% similarity"""
    new_clean = clean_and_format_title(new_title).lower().strip()
    new_words = set(new_clean.split())
    
    for existing in existing_titles:
        if existing == new_clean:
            return True
        
        existing_words = set(existing.split())
        if len(new_words) > 4 and len(existing_words) > 4:
            common = new_words.intersection(existing_words)
            if len(common) / len(new_words) > 0.8:
                return True
        
        if len(new_clean) > 30 and new_clean[:30] in existing:
            return True
    
    return False

def get_full_content(entry):
    try:
        content = entry.get('content')
        if content and isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and 'value' in item:
                    text = re.sub(r'<[^>]+>', '', item['value'])
                    if len(text) > 500:
                        return text[:3000]
        summary = entry.get('summary', '')
        if summary:
            return re.sub(r'<[^>]+>', '', summary)[:3000]
    except:
        pass
    return entry.get('summary', '')

def get_entry_image(entry):
    try:
        media_content = entry.get('media_content')
        if media_content and isinstance(media_content, list):
            for media in media_content:
                if 'url' in media:
                    return media['url']
        links = entry.get('links')
        if links:
            for link in links:
                if 'image' in link.get('type', ''):
                    return link.get('href')
        summary = entry.get('summary', '')
        if 'src=' in summary:
            match = re.search(r'src=["\'](https?://[^"\']+)["\']', summary)
            if match:
                return match.group(1)
        content = entry.get('content', [])
        if content:
            for item in content:
                if isinstance(item, dict) and 'value' in item:
                    match = re.search(r'src=["\'](https?://[^"\']+)["\']', item['value'])
                    if match:
                        return match.group(1)
    except:
        pass
    return None

def generate_ai_image(prompt, category):
    try:
        print("🎨 Generating AI image...")
        clean = prompt.replace('"', '').replace("'", '')[:60]
        url = f"https://image.pollinations.ai/prompt/{clean.replace(' ', '%20')}?width=1200&height=630&nologo=true&seed={random.randint(1, 9999)}"
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            return url
    except:
        pass
    return None

def get_hd_image_strict(entry, title, category):
    """Always returns an image"""
    print("📸 Getting HD image...")
    
    # 1️⃣ RSS
    image = get_entry_image(entry)
    if image and image.startswith('http'):
        print("✅ RSS image!")
        return image
    
    # 2️⃣ AI
    image = generate_ai_image(title, category)
    if image:
        print("✅ AI image!")
        return image
    
    # 3️⃣ Category
    if category in UNSPLASH_IMAGES:
        print("✅ Category image!")
        return UNSPLASH_IMAGES[category]
    
    # 4️⃣ Ultimate
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1200&q=80"

def get_short_url(long_url):
    try:
        if not SHRINKME_API:
            return long_url
        api_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={long_url}&format=text"
        response = requests.get(api_url, timeout=10)
        return response.text.strip() if response.text else long_url
    except:
        return long_url

def detect_category(feed_url, title):
    feed_lower = feed_url.lower()
    title_lower = title.lower()
    
    if "space" in feed_lower or "nasa" in feed_lower:
        if "fusion" in title_lower:
            return "Technology"
        return "Space"
    if any(x in feed_lower for x in ["tech", "verge", "cnet"]):
        return "Technology"
    if any(x in feed_lower for x in ["gamespot", "ign"]):
        return "Gaming"
    if any(x in feed_lower for x in ["variety", "hollywood", "pinkvilla"]):
        return "Entertainment"
    if any(x in feed_lower for x in ["rollingstone"]):
        return "Music"
    if "cric" in feed_lower:
        return "Sports"
    if any(x in feed_lower for x in ["bloomberg", "reuters"]):
        return "Business"
    return "News"

def generate_long_content(title, full_content, category):
    if HF_TOKEN:
        models = ["mistralai/Mistral-7B-Instruct-v0.1", "Qwen/Qwen2.5-7B-Instruct"]
        for model in models:
            try:
                print(f"🤖 Trying: {model}")
                prompt = f"""Write a DETAILED 1000-1500 word news article in Hinglish about: {title}
Context: {full_content[:1000]}
Category: {category}
Structure: Introduction, Key Highlights, Detailed Analysis, Expert Opinions, Impact, What's Next, Conclusion
Use HTML tags: <h2>, <h3>, <p>, <ul>, <li>"""

                API_URL = f"https://api-inference.huggingface.co/models/{model}"
                headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                payload = {"inputs": prompt, "parameters": {"max_new_tokens": 1500, "temperature": 0.7}}
                
                response = requests.post(API_URL, headers=headers, json=payload, timeout=180)
                if response.status_code == 503:
                    print("⏳ Loading...")
                    time.sleep(45)
                    response = requests.post(API_URL, headers=headers, json=payload, timeout=180)
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        text = result[0].get('generated_text', '')
                        if prompt in text:
                            text = text.replace(prompt, '').strip()
                        if len(text) > 500:
                            return text
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout, trying next...")
                continue
            except:
                continue
    
    today = datetime.now().strftime("%B %d, %Y")
    return f"""
<h2>🚨 BREAKING NEWS: {title}</h2>
<p><strong>📅 {today} | 📂 {category}</strong></p>
<h3>📝 Introduction</h3>
<p>{title} - आज की बड़ी खबर। {category} सेक्टर में चर्चा।</p>
<p>{full_content[:800]}...</p>
<p><em>Disclaimer: AI-generated summary. Refer to original source.</em></p>
"""

def post_to_blogger(access_token, title, content, category):
    try:
        post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        cleaned = clean_and_format_title(title)
        post_body = {
            "kind": "blogger#post",
            "title": cleaned,
            "content": content,
            "labels": ["Breaking News", category, "Hinglish", datetime.now().strftime("%Y")]
        }
        post_res = requests.post(post_url, headers=headers, json=post_body, timeout=20)
        return post_res.status_code in [200, 201]
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# --- MAIN ---

def main():
    print("🤖 Starting Blogger Bot...")
    fix_dns()
    
    access_token = get_blogger_access_token()
    if not access_token:
        print("❌ Invalid token.")
        return
    
    existing_titles = get_all_blogger_titles(access_token)
    local_posted = load_posted_news()
    all_posted = existing_titles.union(local_posted)
    print(f"📊 Total tracked: {len(all_posted)}")
    
    found_news = False
    entry = None
    selected_feed = None
    image_url = None
    
    shuffled_feeds = RSS_FEEDS.copy()
    random.shuffle(shuffled_feeds)
    
    for feed_url in shuffled_feeds:
        print(f"📰 Checking: {feed_url}")
        try:
            response = requests.get(feed_url, timeout=15)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                for i in range(min(15, len(feed.entries))):
                    temp_entry = feed.entries[i]
                    temp_title = temp_entry.title
                    
                    if hasattr(temp_entry, 'published_parsed'):
                        pub_date = datetime(*temp_entry.published_parsed[:6])
                        if pub_date.date() < datetime.now().date() - timedelta(days=2):
                            continue
                    
                    if is_duplicate_title(temp_title, all_posted):
                        print(f"⏭️ SKIP: {temp_title[:40]}...")
                        continue
                    
                    category = detect_category(feed_url, temp_title)
                    image_url = get_hd_image_strict(temp_entry, temp_title, category)
                    
                    if image_url:
                        entry = temp_entry
                        selected_feed = feed_url
                        found_news = True
                        break
                if found_news:
                    break
        except Exception as e:
            print(f"⚠️ Error: {e}")
    
    if not found_news or not entry:
        print("❌ No new news found!")
        return
    
    raw_title = entry.title
    title = clean_and_format_title(raw_title)
    link = entry.link
    full_content = get_full_content(entry)
    category = detect_category(selected_feed, title)
    
    image_html = f"""
    <div style="text-align:center;margin-bottom:25px;">
        <img src='{image_url}' alt='{title}' style='width:100%;max-width:700px;height:auto;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.15);'>
    </div>
    """
    
    short_link = get_short_url(link)
    ai_content = generate_long_content(title, full_content, category)
    
    earning_button = f"""
    <div style="text-align:center;margin:30px 0;padding:20px;background:#f5f5f5;border-radius:12px;">
        <a href="{short_link}" target="_blank" style="background:linear-gradient(135deg,#ff5722,#ff6f00);color:white;padding:18px 50px;text-decoration:none;font-size:20px;font-weight:bold;border-radius:50px;display:inline-block;text-transform:uppercase;">
            📖 पूरी खबर पढ़ें - READ FULL STORY
        </a>
    </div>
    """
    
    final_content = f"{image_html}{ai_content}{earning_button}"
    
    print(f"\n📝 Posting: {title}")
    if post_to_blogger(access_token, title, final_content, category):
        save_posted_news(title)
        print("✅ SUCCESS!")
        print(f"🔗 {short_link}")
    else:
        print("❌ Failed!")

if __name__ == "__main__":
    main()
