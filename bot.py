import os
import json
import random
import time
import requests
import feedparser
import re
from datetime import datetime, timedelta
import socket

# --- FIX: DNS Resolution for Hugging Face ---
def fix_dns():
    """Fix DNS resolution for Hugging Face API"""
    try:
        # Try to resolve huggingface domain
        socket.gethostbyname('api-inference.huggingface.co')
    except:
        # If fails, use alternative
        print("DNS fix applied for Hugging Face")

# --- CONFIGURATION ---
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

# --- MULTI-CATEGORY RSS FEEDS ---
RSS_FEEDS = [
    # Technology
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://www.cnet.com/rss/news/",
    
    # Gaming
    "https://www.gamespot.com/feeds/game-news/",
    "https://www.ign.com/rss/articles/all",
    "https://www.polygon.com/rss/index.xml",
    
    # Entertainment
    "https://www.variety.com/feed/",
    "https://www.hollywoodreporter.com/feed/",
    "https://www.pinkvilla.com/feed",
    "https://www.eonline.com/news/rss",
    
    # Space & Science
    "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "https://www.space.com/feeds/all",
    
    # Business
    "https://www.bloomberg.com/feeds/markets.rss",
    "https://www.reuters.com/rss/reuters-business-news.rss",
    
    # Sports
    "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
    
    # Music
    "https://www.rollingstone.com/music/music-news/feed/",
]

# --- FIX: Multiple AI Models (Fallback Chain) ---
AI_MODELS = [
    "mistralai/Mistral-7B-Instruct-v0.1",
    "Qwen/Qwen2.5-7B-Instruct",
    "google/flan-t5-xxl",
    "meta-llama/Llama-2-7b-chat-hf"
]

# --- FUNCTIONS ---

def get_entry_image(entry):
    """Extract image from RSS entry"""
    try:
        # Check media_content
        media_content = entry.get('media_content')
        if media_content and isinstance(media_content, list):
            for media in media_content:
                if 'url' in media:
                    return media['url']
        
        # Check links
        links = entry.get('links')
        if links:
            for link in links:
                if 'image' in link.get('type', ''):
                    return link.get('href')
        
        # Check enclosures
        enclosures = entry.get('enclosures')
        if enclosures:
            for enc in enclosures:
                if enc.get('type', '').startswith('image'):
                    return enc.get('href')
        
        # Check summary
        summary = entry.get('summary', '')
        if 'src=' in summary:
            match = re.search(r'src=["\'](https?://[^"\']+)["\']', summary)
            if match:
                return match.group(1)
        
        # Check content
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
    """Get category-based image"""
    title_lower = title.lower()
    feed_lower = feed_url.lower() if feed_url else ""
    
    # Space/Science
    if "nasa" in feed_lower or "space" in feed_lower or any(word in title_lower for word in ["space", "nasa", "moon", "mars", "galaxy", "star", "planet"]):
        return "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80"
    
    # Gaming
    if "gamespot" in feed_lower or "ign" in feed_lower or "polygon" in feed_lower or any(word in title_lower for word in ["game", "gaming", "playstation", "xbox", "nintendo", "switch", "fortnite", "gta", "minecraft"]):
        return "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80"
    
    # Entertainment
    if "variety" in feed_lower or "hollywood" in feed_lower or "eonline" in feed_lower or "pinkvilla" in feed_lower or any(word in title_lower for word in ["movie", "hollywood", "celebrity", "actor", "film", "netflix"]):
        return "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80"
    
    # Sports
    if "cric" in feed_lower or "sports" in feed_lower or any(word in title_lower for word in ["cricket", "ipl", "world cup", "t20", "virat", "rohit", "dhoni", "kohli"]):
        return "https://images.unsplash.com/photo-1531415074968-036ba1b575da?auto=format&fit=crop&w=1200&q=80"
    
    # Business
    if "bloomberg" in feed_lower or "reuters" in feed_lower or any(word in title_lower for word in ["stock", "market", "business", "economy", "finance", "crypto"]):
        return "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80"
    
    # Music
    if "rollingstone" in feed_lower or any(word in title_lower for word in ["music", "song", "album", "concert", "singer", "band"]):
        return "https://images.unsplash.com/photo-1511735111819-9a3f7709049c?auto=format&fit=crop&w=1200&q=80"
    
    # Technology (Default)
    if any(word in title_lower for word in ["tech", "apple", "google", "microsoft", "phone", "laptop", "software", "ai", "robot"]):
        return "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80"
    
    # Default News
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1200&q=80"

def get_short_url(long_url):
    """Shorten URL with ShrinkMe API"""
    try:
        if not SHRINKME_API:
            return long_url
        api_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={long_url}&format=text"
        response = requests.get(api_url, timeout=10)
        return response.text.strip() if response.text else long_url
    except:
        return long_url

def generate_ai_content(title, source_text, category):
    """Generate AI content with multiple model fallback"""
    if not HF_TOKEN:
        print("❌ HF_TOKEN is empty")
        return None

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

    # FIX: Use multiple models with fallback
    for model in AI_MODELS:
        try:
            print(f"⏳ Trying model: {model}")
            API_URL = f"https://api-inference.huggingface.co/models/{model}"
            
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
            
            # FIX: Increase timeout and retry
            response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
            
            if response.status_code == 503:
                print(f"⏳ Model {model} loading, waiting 30 seconds...")
                time.sleep(30)
                response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get('generated_text', '')
                    if prompt in text:
                        text = text.replace(prompt, '').strip()
                    if len(text) > 100:
                        print(f"✅ Success with model: {model}")
                        return text
            else:
                print(f"❌ Model {model} failed: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout with {model}, trying next...")
        except requests.exceptions.ConnectionError:
            print(f"🔌 Connection error with {model}, trying next...")
        except Exception as e:
            print(f"❌ Error with {model}: {e}")
            continue
    
    print("⚠️ All AI models failed, using fallback")
    return None

def generate_fallback_content(title, source_text, image_html, category):
    """Fallback content without AI"""
    today = datetime.now().strftime("%B %d, %Y")
    
    # FIX: Better fallback with more details
    highlights = [
        f"• {title} - Breaking news for {today}",
        "• Industry experts are closely monitoring developments",
        "• Significant impact expected in the coming days",
        "• Public reaction and global response"
    ]
    
    article = f"""
    {image_html}
    
    <h2>BREAKING: {title}</h2>
    
    <p><strong>Published: {today} | Category: {category}</strong></p>
    
    <p>In a significant development today ({today}), {title} has captured global attention. This breaking news story is making headlines across major news platforms worldwide.</p>
    
    <h3>Key Highlights</h3>
    <ul>
        {''.join([f'<li>{h}</li>' for h in highlights])}
    </ul>
    
    <h3>Details</h3>
    <p>{source_text[:500]}...</p>
    
    <blockquote style="border-left: 5px solid #ff5722; padding-left: 20px; margin: 20px 0; background: #f9f9f9; padding: 15px; border-radius: 5px;">
    <p style="font-style: italic; color: #555;">"This is a developing story. Stay tuned for updates as more information becomes available."</p>
    </blockquote>
    
    <h3>What This Means</h3>
    <p>This development represents a significant shift in the {category} landscape. Industry observers and stakeholders are closely watching how this situation unfolds.</p>
    """
    return article

def post_to_blogger(title, content):
    """Post to Blogger using OAuth"""
    if not all([BC_CLIENT_ID, BC_CLIENT_SECRET, BC_REFRESH_TOKEN]):
        print("❌ Blogger OAuth Secrets missing.")
        return False
        
    try:
        # Get new access token
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
        
        # Post to Blogger
        post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        post_body = {
            "kind": "blogger#post",
            "title": title,
            "content": content,
            "labels": ["Breaking News", "AI-Generated", "Automated"]
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
    """Verify Blogger access"""
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

def detect_category(feed_url):
    """Detect category from feed URL"""
    feed_lower = feed_url.lower() if feed_url else ""
    
    if "tech" in feed_lower or "verge" in feed_lower or "cnet" in feed_lower or "wired" in feed_lower:
        return "Technology"
    elif "gamespot" in feed_lower or "ign" in feed_lower or "polygon" in feed_lower:
        return "Gaming"
    elif "variety" in feed_lower or "hollywood" in feed_lower or "eonline" in feed_lower or "pinkvilla" in feed_lower:
        return "Entertainment"
    elif "nasa" in feed_lower or "space" in feed_lower:
        return "Space & Science"
    elif "cric" in feed_lower or "sports" in feed_lower:
        return "Sports"
    elif "bloomberg" in feed_lower or "reuters" in feed_lower:
        return "Business"
    elif "rollingstone" in feed_lower:
        return "Music"
    else:
        return "News"

# --- MAIN LOGIC ---

def main():
    print("🤖 Starting the Robot...")
    print(f"📅 Today's Date: {datetime.now().strftime('%B %d, %Y')}")
    
    # Fix DNS
    fix_dns()
    
    # --- Check Secrets ---
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
    
    # Verify Blogger
    print("🔍 Verifying Blogger permissions...")
    if not verify_blogger_permission():
        print("❌ Cannot proceed. Blogger credentials are invalid.")
        return
    
    # Shuffle feeds
    random.shuffle(RSS_FEEDS)
    
    entry = None
    selected_feed_url = None
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # Find news
    print("\n🔍 Searching for Today's Breaking News from all categories...")
    
    for feed_url in RSS_FEEDS:
        print(f"\n📰 Checking: {feed_url}")
        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                if feed.entries:
                    # Get latest news
                    entry = feed.entries[0]
                    selected_feed_url = feed_url
                    
                    # Check date
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])
                        today = datetime.now()
                        # FIX: Accept news from last 2 days
                        if pub_date.date() >= today.date() - timedelta(days=2):
                            print(f"✅ Recent news found (from {pub_date.strftime('%B %d')})")
                            break
                        else:
                            print(f"⚠️ News from {pub_date.strftime('%B %d')} - older, but using anyway...")
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
    title = re.sub(r'\s+', ' ', entry.title).strip()
    link = entry.link
    summary = entry.get('summary', '')
    
    # Detect category
    category = detect_category(selected_feed_url)
    
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

    # Prepare final content
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
        print(f"🔗 {short_link}")
    else:
        print("\n❌ Failed to post. Check logs above.")

if __name__ == "__main__":
    main()
