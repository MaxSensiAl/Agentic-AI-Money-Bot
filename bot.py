import os
import json
import random
import time
import requests
import feedparser
import re
from datetime import datetime, timedelta
import socket
import base64

# --- FIX: DNS Resolution for Hugging Face ---
def fix_dns():
    """Fix DNS resolution for Hugging Face API"""
    try:
        socket.gethostbyname('api-inference.huggingface.co')
    except:
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

# --- MULTI-CATEGORY RSS FEEDS (Expanded) ---
RSS_FEEDS = [
    # Technology
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://www.cnet.com/rss/news/",
    "https://arstechnica.com/feed/",
    
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

# --- FUNCTIONS ---

def get_seo_title(title):
    """Generate SEO optimized title in Hinglish style"""
    clean_title = re.sub(r'[^\w\s-]', '', title)
    words = clean_title.split()
    seo_title = " ".join(words[:12])
    if len(seo_title) > 70:
        seo_title = seo_title[:67] + "..."
    year = datetime.now().strftime("%Y")
    return f"{seo_title} - {year}"

def get_full_content(entry):
    """Extract FULL content from RSS entry"""
    try:
        # Try to get full content first
        content = entry.get('content')
        if content and isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and 'value' in item:
                    text = item['value']
                    # Remove HTML tags for clean text
                    clean_text = re.sub(r'<[^>]+>', '', text)
                    if len(clean_text) > 200:
                        return clean_text[:1500]
        
        # If no content, use summary
        summary = entry.get('summary', '')
        if summary:
            clean_summary = re.sub(r'<[^>]+>', '', summary)
            return clean_summary[:1500]
            
    except:
        pass
    return entry.get('summary', 'No full content available')

def get_entry_image(entry):
    """Extract image from RSS entry with fallback"""
    try:
        # 1. Check media_content
        media_content = entry.get('media_content')
        if media_content and isinstance(media_content, list):
            for media in media_content:
                if 'url' in media:
                    return media['url']
        
        # 2. Check links
        links = entry.get('links')
        if links:
            for link in links:
                if 'image' in link.get('type', ''):
                    return link.get('href')
        
        # 3. Check enclosures
        enclosures = entry.get('enclosures')
        if enclosures:
            for enc in enclosures:
                if enc.get('type', '').startswith('image'):
                    return enc.get('href')
        
        # 4. Check summary
        summary = entry.get('summary', '')
        if 'src=' in summary:
            match = re.search(r'src=["\'](https?://[^"\']+)["\']', summary)
            if match:
                return match.group(1)
        
        # 5. Check content
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

def get_high_quality_image(feed_url, title, category):
    """Get high quality image with multiple fallbacks"""
    title_lower = title.lower()
    feed_lower = feed_url.lower() if feed_url else ""
    
    # Category based high-quality images
    image_map = {
        "Technology": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
        "Gaming": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80",
        "Entertainment": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80",
        "Space & Science": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
        "Sports": "https://images.unsplash.com/photo-1531415074968-036ba1b575da?auto=format&fit=crop&w=1200&q=80",
        "Business": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80",
        "Music": "https://images.unsplash.com/photo-1511735111819-9a3f7709049c?auto=format&fit=crop&w=1200&q=80",
    }
    
    # Check if any keyword matches
    for key, url in image_map.items():
        if key in category or any(word in title_lower for word in key.lower().split()):
            return url
    
    # Fallback to category based
    if "nasa" in feed_lower or "space" in feed_lower:
        return "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80"
    
    if "gamespot" in feed_lower or "ign" in feed_lower:
        return "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80"
    
    if "variety" in feed_lower or "hollywood" in feed_lower:
        return "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80"
    
    # Default high quality image
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

def generate_hinglish_content(title, full_content, category):
    """Generate Hinglish (Hindi+English) content with AI or fallback"""
    if not HF_TOKEN:
        print("❌ HF_TOKEN is empty, using fallback")
        return None

    today = datetime.now().strftime("%B %d, %Y")
    
    # Hinglish prompt
    prompt = f"""Write a comprehensive news article in HINGLISH (Hindi + English mix) about: {title}

Published on: {today}
Category: {category}

Full Content Context: {full_content[:800]}

Format Requirements:
1. Use Hinglish language (mix of Hindi and English)
2. Article length: 500-800 words
3. Use HTML tags: <h2>, <h3>, <p>, <ul>, <li>
4. Add 'Key Highlights' with bullet points in Hinglish
5. Add 'Full Story' section
6. Add 'What's Next' section
7. Include a disclaimer

Make it engaging, easy to read, and SEO friendly."""

    AI_MODELS = [
        "mistralai/Mistral-7B-Instruct-v0.1",
        "Qwen/Qwen2.5-7B-Instruct",
        "google/flan-t5-xxl",
    ]
    
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
                    "max_new_tokens": 1200,
                    "temperature": 0.8,
                    "do_sample": True,
                    "top_p": 0.95
                }
            }
            
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            
            if response.status_code == 503:
                print(f"⏳ Model {model} loading, waiting...")
                time.sleep(40)
                response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get('generated_text', '')
                    if prompt in text:
                        text = text.replace(prompt, '').strip()
                    if len(text) > 200:
                        print(f"✅ Success with model: {model}")
                        return text
        except:
            continue
    
    print("⚠️ All AI models failed, using Hinglish fallback")
    return None

def generate_hinglish_fallback(title, full_content, image_html, category, short_link):
    """Generate Hinglish fallback content"""
    today = datetime.now().strftime("%B %d, %Y")
    seo_title = get_seo_title(title)
    
    # Clean content
    clean_text = re.sub(r'https?://[^\s]+', '', full_content)
    
    # Generate Hinglish highlights
    highlights = [
        f"• {title} - आज की बड़ी खबर",
        f"• {category} सेक्टर में बड़ा बदलाव",
        f"• विशेषज्ञों की राय - Expert Opinion",
        f"• पूरी कहानी - Full Story नीचे",
    ]
    
    article = f"""
    {image_html}
    
    <h1>{seo_title}</h1>
    
    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <p><strong>📅 Published:</strong> {today} | <strong>📂 Category:</strong> {category}</p>
        <p><strong>🌐 Language:</strong> Hinglish (Hindi + English)</p>
    </div>
    
    <h2>🚨 Breaking News: {title}</h2>
    
    <p><strong>आज की बड़ी खबर - {today}</strong></p>
    
    <p>{title} - यह खबर {category} सेक्टर में तहलका मचा रही है। आइए जानते हैं पूरी कहानी...</p>
    
    <p>{clean_text[:500]}...</p>
    
    <h3>🎯 Key Highlights - मुख्य बातें</h3>
    <ul>
        {''.join([f'<li>{h}</li>' for h in highlights])}
    </ul>
    
    <h3>📝 पूरी कहानी - Full Story</h3>
    <p>{clean_text[:700]}...</p>
    
    <h3>🔮 What's Next - आगे क्या?</h3>
    <p>इस खबर का आगे का अपडेट जल्द ही आएगा। नीचे दिए गए बटन पर क्लिक करें पूरी जानकारी के लिए।</p>
    
    <!-- READ FULL STORY BUTTON -->
    <div style="text-align: center; margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 12px;">
        <a href="{short_link}" 
           target="_blank" 
           rel="nofollow sponsored"
           style="background: linear-gradient(135deg, #ff5722, #ff6f00); 
                  color: white; 
                  padding: 18px 50px; 
                  text-decoration: none; 
                  font-size: 20px; 
                  font-weight: bold; 
                  border-radius: 50px; 
                  box-shadow: 0 8px 25px rgba(255,87,34,0.4); 
                  display: inline-block; 
                  transition: all 0.3s;
                  text-transform: uppercase;
                  letter-spacing: 1px;">
            📖 पूरी खबर पढ़ें - READ FULL STORY
        </a>
        <p style="font-size: 12px; color: #999; margin-top: 10px;">Click to read the complete story on the original source</p>
    </div>
    
    <hr style="border: 0; border-top: 2px solid #f0f0f0; margin: 30px 0;">
    
    <div style="text-align: center; color: #999; font-size: 14px;">
        <p>📅 Published: {today}</p>
        <p>📂 Category: {category}</p>
        <p>🤖 AI-Generated Hinglish News Summary</p>
        <p>© Viral News AI - All Rights Reserved</p>
    </div>
    
    <div style="font-size: 12px; color: #ccc; text-align: center; margin-top: 10px;">
        <p>⚠️ Disclaimer: This is an AI-generated summary. Please refer to the original source for complete details.</p>
    </div>
    """
    return article

def post_to_blogger(title, content, category):
    """Post to Blogger with SEO optimization"""
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
        
        # SEO-optimized post with Hinglish labels
        post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        labels = [
            "Breaking News",
            category,
            "Hinglish",
            datetime.now().strftime("%Y"),
            "AI-Generated"
        ]
        
        post_body = {
            "kind": "blogger#post",
            "title": title[:70],
            "content": content,
            "labels": labels
        }
        
        post_res = requests.post(post_url, headers=headers, json=post_body, timeout=20)
        
        if post_res.status_code in [200, 201]:
            result = post_res.json()
            print(f"✅ Successfully Posted!")
            print(f"🔗 URL: {result.get('url', 'N/A')}")
            print(f"🏷️ Labels: {', '.join(labels)}")
            return True
        else:
            print(f"❌ Blogger Post Failed - Status: {post_res.status_code}")
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
            print(f"❌ Blog Verification Failed")
            return False
    except Exception as e:
        print(f"❌ Verification Error: {e}")
        return False

def detect_category(feed_url, title=""):
    """Detect category from feed URL and title"""
    feed_lower = feed_url.lower() if feed_url else ""
    title_lower = title.lower()
    
    # Technology
    if any(x in feed_lower for x in ["tech", "verge", "cnet", "wired", "arstechnica"]):
        return "Technology"
    
    # Gaming
    if any(x in feed_lower for x in ["gamespot", "ign", "polygon"]):
        return "Gaming"
    
    # Entertainment
    if any(x in feed_lower for x in ["variety", "hollywood", "eonline", "pinkvilla"]):
        return "Entertainment"
    
    # Space & Science
    if any(x in feed_lower for x in ["nasa", "space"]):
        if "binocular" in title_lower or "camera" in title_lower:
            return "Technology"
        return "Space & Science"
    
    # Sports
    if any(x in feed_lower for x in ["cric", "espn"]):
        return "Sports"
    
    # Business
    if any(x in feed_lower for x in ["bloomberg", "reuters"]):
        return "Business"
    
    # Music
    if any(x in feed_lower for x in ["rollingstone", "billboard"]):
        return "Music"
    
    return "News"

# --- MAIN FUNCTION ---

def main():
    print("🤖 Starting SEO-Optimized Hinglish Blogger Bot...")
    print(f"📅 Today's Date: {datetime.now().strftime('%B %d, %Y')}")
    
    fix_dns()
    
    # --- Check Secrets ---
    print("\n--- Checking GitHub Secrets Status ---")
    print(f"BLOG_ID: {'✅ LOADED' if BLOG_ID else '❌ MISSING'}")
    print(f"BC_CLIENT_ID: {'✅ LOADED' if BC_CLIENT_ID else '❌ MISSING'}")
    print(f"BC_CLIENT_SECRET: {'✅ LOADED' if BC_CLIENT_SECRET else '❌ MISSING'}")
    print(f"BC_REFRESH_TOKEN: {'✅ LOADED' if BC_REFRESH_TOKEN else '❌ MISSING'}")
    print(f"SHRINKME_API: {'✅ LOADED' if SHRINKME_API else '❌ MISSING'}")
    print("--------------------------------------\n")
    
    # Verify required secrets
    required = [BLOG_ID, BC_CLIENT_ID, BC_CLIENT_SECRET, BC_REFRESH_TOKEN]
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
                    entry = feed.entries[0]
                    selected_feed_url = feed_url
                    
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])
                        today = datetime.now()
                        if pub_date.date() >= today.date() - timedelta(days=2):
                            print(f"✅ Recent news found (from {pub_date.strftime('%B %d')})")
                            break
                        else:
                            print(f"⚠️ News from {pub_date.strftime('%B %d')} - using anyway...")
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
    
    # Get FULL content (not just summary)
    full_content = get_full_content(entry)
    
    seo_title = get_seo_title(title)
    category = detect_category(selected_feed_url, title)
    
    print(f"\n📰 Processing: {seo_title}")
    print(f"📂 Category: {category}")
    print(f"📝 Content length: {len(full_content)} characters")
    
    # Get image (try RSS first, then fallback)
    image_url = get_entry_image(entry)
    if not image_url:
        print("🖼️ No image in RSS - using category-based image")
        image_url = get_high_quality_image(selected_feed_url, title, category)
        
    image_html = f"""
    <img src='{image_url}' 
         alt='{seo_title}' 
         style='width: 100%; max-height: 600px; object-fit: cover; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); margin-bottom: 25px;' 
         loading='lazy'>
    """
    print(f"📸 Image URL: {image_url}")
    
    # Shorten link
    short_link = get_short_url(link)
    print(f"🔗 Short link: {short_link}")

    # Generate Hinglish content
    print("🤖 Generating Hinglish SEO-optimized content...")
    ai_content = generate_hinglish_content(title, full_content, category)
    
    # Prepare final content
    if ai_content and len(ai_content) > 300:
        print("✅ Hinglish content generated successfully")
        final_content = f"""
        {image_html}
        {ai_content}
        
        <!-- Earning Button -->
        <div style="text-align: center; margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #fff5f0, #fff); border-radius: 12px;">
            <a href="{short_link}" 
               target="_blank" 
               rel="nofollow sponsored"
               style="background: linear-gradient(135deg, #ff5722, #ff6f00); 
                      color: white; 
                      padding: 18px 50px; 
                      text-decoration: none; 
                      font-size: 20px; 
                      font-weight: bold; 
                      border-radius: 50px; 
                      box-shadow: 0 8px 25px rgba(255,87,34,0.4); 
                      display: inline-block; 
                      transition: all 0.3s;
                      text-transform: uppercase;
                      letter-spacing: 1px;">
                📖 पूरी खबर पढ़ें - READ FULL STORY
            </a>
            <p style="font-size: 12px; color: #999; margin-top: 10px;">Click to read the complete story on the original source</p>
        </div>
        
        <hr style="border: 0; border-top: 2px solid #f0f0f0; margin: 30px 0;">
        
        <div style="text-align: center; color: #999; font-size: 14px;">
            <p>📅 Published: {datetime.now().strftime('%B %d, %Y')}</p>
            <p>📂 Category: {category}</p>
            <p>🌐 Language: Hinglish (Hindi + English)</p>
            <p>🤖 AI-Generated News Summary</p>
        </div>
        """
    else:
        print("⚠️ Using Hinglish fallback content")
        final_content = generate_hinglish_fallback(title, full_content, image_html, category, short_link)

    # Post to Blogger
    print("\n📝 Posting to Blogger...")
    if post_to_blogger(seo_title, final_content, category):
        print("\n✅ PROCESS COMPLETED SUCCESSFULLY!")
        print(f"📰 Title: {seo_title}")
        print(f"📂 Category: {category}")
        print(f"🌐 Language: Hinglish (Hindi + English)")
        print(f"🔗 Short Link: {short_link}")
        print(f"📝 Content Length: {len(final_content)} characters")
        print(f"🖼️ Image Included: Yes")
    else:
        print("\n❌ Failed to post. Check logs above.")

if __name__ == "__main__":
    main()
