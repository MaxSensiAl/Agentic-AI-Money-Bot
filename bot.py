import os
import json
import random
import time
import requests
import feedparser
import re
from datetime import datetime

# --- CONFIGURATION (GitHub Secrets से डेटा उठाना) ---
BLOG_ID = os.getenv('BLOG_ID').strip() if os.getenv('BLOG_ID') else None
SHRINKME_API = os.getenv('SHRINKME_API').strip() if os.getenv('SHRINKME_API') else None

# Hugging Face Token
HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('GEMINI_API')
if HF_TOKEN:
    HF_TOKEN = HF_TOKEN.strip()

# Blogger OAuth Credentials
BC_CLIENT_ID = os.getenv('BC_CLIENT_ID').strip() if os.getenv('BC_CLIENT_ID') else None
BC_CLIENT_SECRET = os.getenv('BC_CLIENT_SECRET').strip() if os.getenv('BC_CLIENT_SECRET') else None
BC_REFRESH_TOKEN = os.getenv('BC_REFRESH_TOKEN').strip() if os.getenv('BC_REFRESH_TOKEN') else None

# 📌 MULTI-CATEGORY RSS FEEDS (Today's news from all categories)
RSS_FEEDS = [
    # 🚀 Technology
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://www.cnet.com/rss/news/",
    
    # 🎮 Gaming
    "https://www.ign.com/rss/articles/all",
    "https://www.gamespot.com/feeds/game-news/",
    "https://www.polygon.com/rss/index.xml",
    
    # 🎬 Entertainment
    "https://www.variety.com/feed/",
    "https://www.hollywoodreporter.com/feed/",
    "https://www.pinkvilla.com/feed",
    "https://www.eonline.com/news/rss",
    
    # 🚀 Space & Science
    "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "https://www.space.com/feeds/all",
    "https://www.science.org/rss/news_current.xml",
    
    # 💼 Business
    "https://www.bloomberg.com/feeds/markets.rss",
    "https://www.reuters.com/rss/reuters-business-news.rss",
    
    # 🌍 World News
    "https://feeds.npr.org/1001/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    
    # 🏏 Sports (Cricket)
    "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
    "https://sports.ndtv.com/rss/cricket-news",
    
    # 🎵 Music
    "https://www.rollingstone.com/music/music-news/feed/",
]

# --- FUNCTIONS ---

def get_entry_image(entry):
    """RSS फीड की खबर से मुख्य इमेज का URL निकालना"""
    try:
        # 1. Media content check
        media_content = entry.get('media_content')
        if media_content and isinstance(media_content, list):
            for media in media_content:
                if 'url' in media:
                    return media['url']
        
        # 2. Links check
        links = entry.get('links')
        if links:
            for link in links:
                if 'image' in link.get('type', ''):
                    return link.get('href')
        
        # 3. Enclosures check
        enclosures = entry.get('enclosures')
        if enclosures:
            for enc in enclosures:
                if enc.get('type', '').startswith('image'):
                    return enc.get('href')
        
        # 4. Summary image
        summary = entry.get('summary', '')
        if 'src=' in summary:
            match = re.search(r'src=["\'](https?://[^"\']+)["\']', summary)
            if match:
                return match.group(1)
        
        # 5. Content image
        content = entry.get('content', [])
        if content:
            for item in content:
                if isinstance(item, dict) and 'value' in item:
                    match = re.search(r'src=["\'](https?://[^"\']+)["\']', item['value'])
                    if match:
                        return match.group(1)
    except Exception as e:
        print(f"Image extraction warning: {e}")
    return None

def get_category_image(feed_url, title):
    """फीड कैटेगरी के अनुसार डायनामिक हाई-डेफिनेशन इमेज देना"""
    title_lower = title.lower()
    feed_lower = feed_url.lower() if feed_url else ""
    
    # 🚀 Space/Science
    if "nasa" in feed_lower or "space" in feed_lower or "science" in feed_lower or any(word in title_lower for word in ["space", "nasa", "moon", "mars", "galaxy", "star", "planet", "eclipse", "astronaut", "rocket"]):
        return "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80"
    
    # 🎮 Gaming
    if "ign" in feed_lower or "gamespot" in feed_lower or "polygon" in feed_lower or any(word in title_lower for word in ["game", "gaming", "playstation", "xbox", "nintendo", "switch", "fortnite", "cod", "gta", "minecraft", "valorant", "pubg"]):
        return "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80"
    
    # 🎬 Entertainment/Hollywood
    if "variety" in feed_lower or "hollywood" in feed_lower or "eonline" in feed_lower or "pinkvilla" in feed_lower or any(word in title_lower for word in ["movie", "hollywood", "celebrity", "actor", "actress", "film", "box office", "oscar", "netflix", "amazon prime"]):
        return "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80"
    
    # 🏏 Sports (Cricket)
    if "cric" in feed_lower or "sports" in feed_lower or any(word in title_lower for word in ["cricket", "ipl", "world cup", "t20", "virat", "rohit", "dhoni", "kohli", "match", "test", "odi"]):
        return "https://images.unsplash.com/photo-1531415074968-036ba1b575da?auto=format&fit=crop&w=1200&q=80"
    
    # 💼 Business
    if "bloomberg" in feed_lower or "reuters" in feed_lower or any(word in title_lower for word in ["stock", "market", "business", "economy", "finance", "crypto", "bitcoin", "investment", "trade"]):
        return "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80"
    
    # 🎵 Music
    if "rollingstone" in feed_lower or any(word in title_lower for word in ["music", "song", "album", "concert", "singer", "band", "bts", "ariana", "taylor", "justin"]):
        return "https://images.unsplash.com/photo-1511735111819-9a3f7709049c?auto=format&fit=crop&w=1200&q=80"
    
    # 📱 Technology (Default)
    if any(word in title_lower for word in ["tech", "apple", "google", "microsoft", "phone", "laptop", "software", "ai", "robot", "cyber"]):
        return "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80"
    
    # 🌍 World News (Default News)
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1200&q=80"

def get_short_url(long_url):
    """ShrinkMe API के जरिए लिंक छोटा करना"""
    try:
        if not SHRINKME_API:
            return long_url
        api_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={long_url}&format=text"
        response = requests.get(api_url, timeout=10)
        return response.text.strip() if response.text else long_url
    except:
        return long_url

def generate_ai_content(title, source_text, category):
    """Hugging Face API से TODAY'S NEWS article generate karna"""
    if not HF_TOKEN:
        print("❌ HF_TOKEN is empty")
        return None

    # Current date
    today = datetime.now().strftime("%B %d, %Y")
    
    prompt = f"""Write a 500-word SEO optimized professional news article in English about: {title} (published on {today}).

Context: {source_text[:500]}.

Category: {category}

Instructions:
1. Use HTML tags: <h2>, <h3>, <p>, <blockquote>
2. Add 'Key Highlights' section with <ul><li>
3. Make it sound like breaking news from TODAY
4. Include quotes where possible
5. End with a disclaimer

Write in a professional news style with proper HTML formatting."""

    # Using Mistral model for better quality
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 800,
            "temperature": 0.8,
            "do_sample": True,
            "top_p": 0.95
        }
    }
    
    try:
        print("⏳ Calling Hugging Face API...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 503:
            print("⏳ Model loading, waiting 30 seconds...")
            time.sleep(30)
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('generated_text', '')
                if prompt in text:
                    text = text.replace(prompt, '').strip()
                return text if len(text) > 100 else None
        else:
            print(f"❌ API Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Hugging Face Error: {e}")
        return None

def generate_fallback_content(title, source_text, image_html, category):
    """Fallback content without AI"""
    today = datetime.now().strftime("%B %d, %Y")
    
    highlights = [
        f"• {title} - Breaking news for {today}",
        "• Industry experts are closely monitoring developments",
        "• Significant impact expected in the coming days",
        "• Public reaction and global response"
    ]
    
    article = f"""
    {image_html}
    
    <h2>BREAKING: {title}</h2>
    
    <p><strong>Published: {today}</strong></p>
    
    <p>In a significant development today ({today}), {title} has captured global attention. This breaking news story is making headlines across major news platforms worldwide.</p>
    
    <h3>Key Highlights</h3>
    <ul>
        {''.join([f'<li>{h}</li>' for h in highlights])}
    </ul>
    
    <h3>Details</h3>
    <p>{source_text[:400]}... [Full story continues]</p>
    
    <blockquote style="border-left: 5px solid #ff5722; padding-left: 20px; margin: 20px 0; background: #f9f9f9; padding: 15px; border-radius: 5px;">
    <p style="font-style: italic; color: #555;">"This is a developing story. Stay tuned for updates as more information becomes available."</p>
    </blockquote>
    """
    return article

def post_to_blogger(title, content):
    """Blogger OAuth से पोस्ट करना"""
    if not all([BC_CLIENT_ID, BC_CLIENT_SECRET, BC_REFRESH_TOKEN]):
        print("❌ Blogger OAuth Secrets missing.")
        return False
        
    try:
        # Refresh Token से नया Access Token
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": BC_CLIENT_ID,
            "client_secret": BC_CLIENT_SECRET,
            "refresh_token": BC_REFRESH_TOKEN,
            "grant_type": "refresh_token"
        }
        res = requests.post(token_url, data=payload, timeout=15)
        res_json = res.json()
        
        if "access_token" not in res_json:
            print(f"❌ Failed to refresh Blogger token: {res_json}")
            return False
            
        access_token = res_json["access_token"]
        
        # Blogger पर पोस्ट
        post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        post_body = {
            "kind": "blogger#post",
            "title": title,
            "content": content,
            "labels": ["Breaking News", "Today's News", "AI-Generated"]
        }
        
        post_res = requests.post(post_url, headers=headers, json=post_body, timeout=20)
        
        if post_res.status_code in [200, 201]:
            result = post_res.json()
            print(f"✅ Successfully Posted!")
            print(f"🔗 URL: {result.get('url', 'N/A')}")
            return True
        else:
            print(f"❌ Blogger Post Failed - Status: {post_res.status_code}")
            print(post_res.text)
            return False
            
    except Exception as e:
        print(f"❌ Blogger OAuth Error: {e}")
        return False

def verify_blogger_permission():
    """Blogger Access Verify"""
    if not all([BC_CLIENT_ID, BC_CLIENT_SECRET, BC_REFRESH_TOKEN]):
        print("❌ Blogger OAuth Secrets missing.")
        return False
    try:
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
            print("❌ Cannot retrieve access token.")
            return False
            
        blog_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}"
        headers = {"Authorization": f"Bearer {access_token}"}
        blog_res = requests.get(blog_url, headers=headers, timeout=15)
        
        if blog_res.status_code == 200:
            print(f"✅ Blogger access verified! Blog: {blog_res.json().get('name')}")
            return True
        else:
            print(f"❌ Blog Verification Failed - Status: {blog_res.status_code}")
            return False
    except Exception as e:
        print(f"❌ Verification Error: {e}")
        return False

# --- MAIN LOGIC ---

def main():
    print("🤖 Starting the Robot...")
    print(f"📅 Today's Date: {datetime.now().strftime('%B %d, %Y')}")
    
    # --- Checking GitHub Secrets ---
    print("\n--- Checking GitHub Secrets Status ---")
    print(f"BLOG_ID: {'✅ LOADED' if BLOG_ID else '❌ MISSING'}")
    print(f"BC_CLIENT_ID: {'✅ LOADED' if BC_CLIENT_ID else '❌ MISSING'}")
    print(f"BC_CLIENT_SECRET: {'✅ LOADED' if BC_CLIENT_SECRET else '❌ MISSING'}")
    print(f"BC_REFRESH_TOKEN: {'✅ LOADED' if BC_REFRESH_TOKEN else '❌ MISSING'}")
    print(f"HF_TOKEN: {'✅ LOADED' if HF_TOKEN else '❌ MISSING'}")
    print(f"SHRINKME_API: {'✅ LOADED' if SHRINKME_API else '❌ MISSING'}")
    print("--------------------------------------\n")
    
    # Verify required secrets
    required = [BLOG_ID, HF_TOKEN, BC_CLIENT_ID, BC_CLIENT_SECRET, BC_REFRESH_TOKEN]
    if not all(required):
        print("❌ Required secrets missing. Exiting...")
        return
    
    # Verify Blogger access
    print("🔍 Verifying Blogger permissions...")
    if not verify_blogger_permission():
        print("❌ Cannot proceed. Blogger credentials are invalid.")
        return
    
    # Shuffle feeds for variety
    random.shuffle(RSS_FEEDS)
    
    entry = None
    selected_feed_url = None
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # 🔥 Find TODAY's news from any category
    print("\n🔍 Searching for Today's Breaking News from all categories...")
    
    for feed_url in RSS_FEEDS:
        print(f"\n📰 Checking: {feed_url}")
        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                if feed.entries:
                    # Pick latest news (first entry)
                    entry = feed.entries[0]
                    selected_feed_url = feed_url
                    
                    # Check if it's today's news
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])
                        today = datetime.now()
                        if pub_date.date() == today.date():
                            print(f"✅ TODAY'S news found in: {feed_url}")
                            break
                        else:
                            print(f"⚠️ News from {pub_date.strftime('%B %d')} - not today, but using anyway...")
                            # Still use it if not found better
                            break
                    else:
                        print(f"✅ Found news in: {feed_url}")
                        break
                else:
                    print(f"❌ No entries found")
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

    if not entry:
        print("❌ No news found in any RSS feed!")
        return

    # Process article
    title = entry.title
    link = entry.link
    summary = entry.get('summary', '')
    
    # Clean title
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Detect category
    category = "News"
    if "tech" in selected_feed_url.lower() or "verge" in selected_feed_url.lower():
        category = "Technology"
    elif "ign" in selected_feed_url.lower() or "gamespot" in selected_feed_url.lower():
        category = "Gaming"
    elif "variety" in selected_feed_url.lower() or "hollywood" in selected_feed_url.lower():
        category = "Entertainment"
    elif "nasa" in selected_feed_url.lower() or "space" in selected_feed_url.lower():
        category = "Space & Science"
    elif "cric" in selected_feed_url.lower() or "sports" in selected_feed_url.lower():
        category = "Sports"
    elif "bloomberg" in selected_feed_url.lower() or "reuters" in selected_feed_url.lower():
        category = "Business"
    elif "rollingstone" in selected_feed_url.lower():
        category = "Music"
    
    print(f"\n📰 Processing: {title}")
    print(f"📂 Category: {category}")
    
    # Get image
    image_url = get_entry_image(entry)
    if not image_url:
        print("🖼️ No image in feed - using category-based image")
        image_url = get_category_image(selected_feed_url, title)
        
    image_html = f"""
    <img src='{image_url}' 
         style='width: 100%; max-height: 500px; object-fit: cover; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); margin-bottom: 25px;' 
         alt='{title}'>
    <br>
    """
    print(f"📸 Image: {image_url}")
    
    # Shorten link
    short_link = get_short_url(link)
    print(f"🔗 Short link: {short_link}")

    # Generate content
    print("🤖 Generating AI content...")
    ai_content = generate_ai_content(title, summary, category)
    
    # Earning Button
    earning_button = f"""
    <div style="text-align: center; margin: 30px 0;">
        <a href="{short_link}" 
           target="_blank" 
           style="background: linear-gradient(135deg, #ff5722, #ff6f00); 
                  color: white; 
                  padding: 16px 40px; 
                  text-decoration: none; 
                  font-size: 20px; 
                  font-weight: bold; 
                  border-radius: 50px; 
                  box-shadow: 0 8px 25px rgba(255,87,34,0.4); 
                  display: inline-block; 
                  transition: all 0.3s;
                  text-transform: uppercase;
                  letter-spacing: 1px;">
            📖 READ FULL STORY HERE
        </a>
    </div>
    """

    if ai_content and len(ai_content) > 150:
        print("✅ AI content generated successfully")
        final_content = f"""
        {image_html}
        {ai_content}
        
        {earning_button}
        
        <hr style="border: 0; border-top: 2px solid #f0f0f0; margin: 30px 0;">
        <p style="color: #999; font-size: 14px; font-style: italic; text-align: center;">
            🤖 AI-Generated News Summary • {datetime.now().strftime('%B %d, %Y')}
        </p>
        <p style="color: #999; font-size: 12px; text-align: center;">
            Click the button above to read the complete story on the original source.
        </p>
        """
    else:
        print("⚠️ Using fallback content")
        fallback = generate_fallback_content(title, summary, image_html, category)
        final_content = f"""
        {fallback}
        
        {earning_button}
        
        <hr style="border: 0; border-top: 2px solid #f0f0f0; margin: 30px 0;">
        <p style="color: #999; font-size: 14px; font-style: italic; text-align: center;">
            📰 Auto-Generated News Summary • {datetime.now().strftime('%B %d, %Y')}
        </p>
        """

    # Post to Blogger
    print("\n📝 Posting to Blogger...")
    if post_to_blogger(title, final_content):
        print("\n✅ PROCESS COMPLETED SUCCESSFULLY!")
        print(f"📰 Today's News Posted: {title}")
        print(f"📂 Category: {category}")
    else:
        print("\n❌ Failed to post. Check logs above.")

if __name__ == "__main__":
    main()
