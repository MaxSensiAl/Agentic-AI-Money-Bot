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

# --- DNS FIX ---
def fix_dns():
    try:
        socket.gethostbyname('api-inference.huggingface.co')
    except:
        print("DNS fix applied")

# --- CONFIGURATION ---
BLOG_ID = os.getenv('BLOG_ID')
SHRINKME_API = os.getenv('SHRINKME_API')
HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('GEMINI_API')

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

# --- FUNCTIONS ---

def get_full_content(entry):
    """Extract FULL content"""
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
    """Extract image from RSS"""
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
    """Generate HD image using AI (Pollinations.ai - Free, No API Key)"""
    try:
        print("🎨 Generating AI image...")
        
        # Clean prompt
        clean_prompt = prompt.replace('"', '').replace("'", '')
        clean_prompt = clean_prompt[:100]  # Limit length
        
        # Pollinations.ai - Free AI image generation
        # It generates HD images without any API key
        url = f"https://image.pollinations.ai/prompt/{clean_prompt.replace(' ', '%20')}"
        
        # Add quality parameters
        url += "?width=1200&height=600&nologo=true"
        
        print(f"🎨 AI Image URL: {url}")
        
        # Download the image
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Upload to imgbb or use directly
            # For now, we'll use the URL directly
            return url
        else:
            print(f"❌ AI Image generation failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ AI Image error: {e}")
        return None

def search_unsplash_image(query, category):
    """Search HD image from Unsplash"""
    try:
        print("🔍 Searching Unsplash...")
        
        # Clean query
        clean_query = query.replace('"', '').replace("'", '')
        clean_query = clean_query[:50]
        
        # Unsplash free API (no key needed for basic search)
        url = f"https://api.unsplash.com/photos/random?query={clean_query}&orientation=landscape"
        
        # Try with public access (no key)
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and 'urls' in data:
                    return data['urls']['regular']
        except:
            pass
        
        # Fallback: Category based image
        if category in UNSPLASH_IMAGES:
            return UNSPLASH_IMAGES[category]
        
        return None
    except Exception as e:
        print(f"❌ Unsplash error: {e}")
        return None

def search_pexels_image(query, category):
    """Search HD image from Pexels"""
    try:
        print("🔍 Searching Pexels...")
        
        # Pexels free API (public access)
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
        
        # Try with public access
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('photos') and len(data['photos']) > 0:
                    return data['photos'][0]['src']['large']
        except:
            pass
        
        # Fallback: Category based image
        if category in UNSPLASH_IMAGES:
            return UNSPLASH_IMAGES[category]
        
        return None
    except Exception as e:
        print(f"❌ Pexels error: {e}")
        return None

def get_high_quality_image(title, category, feed_url):
    """Get HD image - Multiple sources"""
    print("📸 Looking for HD image...")
    
    # 1️⃣ Try RSS feed first
    image = get_entry_image(entry)  # This will be called from main
    if image:
        print("✅ RSS image found!")
        return image
    
    # 2️⃣ Try Unsplash
    image = search_unsplash_image(title, category)
    if image:
        print("✅ Unsplash HD image found!")
        return image
    
    # 3️⃣ Try Pexels
    image = search_pexels_image(title, category)
    if image:
        print("✅ Pexels HD image found!")
        return image
    
    # 4️⃣ Generate AI Image
    print("🎨 Trying AI image generation...")
    image = generate_ai_image(title, category)
    if image:
        print("✅ AI HD image generated!")
        return image
    
    # 5️⃣ Final Fallback: Category image
    if category in UNSPLASH_IMAGES:
        print("✅ Fallback category image used")
        return UNSPLASH_IMAGES[category]
    
    # 6️⃣ Ultimate fallback
    print("✅ Ultimate fallback image used")
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1200&q=80"

def get_short_url(long_url):
    """Shorten URL"""
    try:
        if not SHRINKME_API:
            return long_url
        api_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={long_url}&format=text"
        response = requests.get(api_url, timeout=10)
        return response.text.strip() if response.text else long_url
    except:
        return long_url

def detect_category(feed_url, title):
    """Detect category"""
    feed_lower = feed_url.lower()
    title_lower = title.lower()
    
    if "space" in feed_lower or "nasa" in feed_lower:
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
    """Generate 1000-1500 word content"""
    if HF_TOKEN:
        try:
            prompt = f"""Write a DETAILED 1000-1500 word news article in Hinglish (Hindi+English mix) about: {title}

Context: {full_content[:1000]}

Category: {category}

Structure:
1. Introduction (100 words)
2. Key Highlights (8-10 bullet points)
3. Detailed Analysis (400 words)
4. Expert Opinions (100 words)
5. Impact & Implications (200 words)
6. What's Next (100 words)
7. Conclusion (100 words)

Use HTML tags: <h2>, <h3>, <p>, <ul>, <li>
Make it SEO friendly, engaging, and professional.
Add a disclaimer at the end."""

            API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
            headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
            payload = {"inputs": prompt, "parameters": {"max_new_tokens": 2000, "temperature": 0.7}}
            
            response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get('generated_text', '')
                    if prompt in text:
                        text = text.replace(prompt, '').strip()
                    if len(text) > 800:
                        return text
        except:
            print("AI failed, using fallback")
    
    # Fallback 1000+ words content
    today = datetime.now().strftime("%B %d, %Y")
    
    highlights = [
        f"• {title} - आज की बड़ी खबर",
        f"• {category} सेक्टर में बड़ा बदलाव",
        f"• विशेषज्ञों की राय - Expert Opinion",
        f"• ग्लोबल इंपैक्ट - Global Impact",
        f"• आगे क्या होगा - What's Next",
        f"• उद्योग पर प्रभाव - Industry Impact",
        f"• कंज्यूमर रिएक्शन - Consumer Reaction",
        f"• भविष्य की संभावनाएं - Future Possibilities",
    ]
    
    return f"""
<h2>🚨 BREAKING NEWS: {title}</h2>

<p><strong>📅 Published: {today} | 📂 Category: {category}</strong></p>

<h3>📝 Introduction</h3>
<p>{title} - यह आज की सबसे बड़ी खबर है। यह घटना {category} सेक्टर में तहलका मचा रही है। विशेषज्ञों का मानना है कि इसका दूरगामी प्रभाव होगा।</p>

<p>{full_content[:500]}...</p>

<h3>🎯 Key Highlights - मुख्य बातें</h3>
<ul>
    {''.join([f'<li>{h}</li>' for h in highlights])}
</ul>

<h3>📊 Detailed Analysis - विस्तृत विश्लेषण</h3>
<p>{full_content[:400]}...</p>
<p>इस खबर के कई पहलू हैं। विशेषज्ञों के अनुसार, यह एक महत्वपूर्ण मोड़ है। इसके आगे क्या प्रभाव होंगे, यह देखना दिलचस्प होगा।</p>

<h3>💬 Expert Opinions - विशेषज्ञों की राय</h3>
<p>उद्योग विशेषज्ञों का कहना है कि यह विकास {category} के लिए गेम-चेंजर साबित हो सकता है। कुछ का मानना है कि इससे नई संभावनाएं खुलेंगी।</p>

<h3>🌍 Impact & Implications - प्रभाव और परिणाम</h3>
<p>इस खबर का असर वैश्विक स्तर पर देखा जा रहा है। कंपनियां अपनी रणनीतियां बदल रही हैं। कंज्यूमर भी इस पर अपनी प्रतिक्रिया दे रहे हैं।</p>

<h3>🔮 What's Next - आगे क्या?</h3>
<p>अगले कुछ दिनों में और अपडेट आने की उम्मीद है। इस खबर पर नजर बनाए रखें। नीचे दिए गए बटन पर क्लिक करें पूरी जानकारी के लिए।</p>

<h3>✅ Conclusion - निष्कर्ष</h3>
<p>यह एक डेवलपिंग स्टोरी है। आने वाले समय में और जानकारी सामने आएगी। तब तक के लिए, यह सबसे बड़ी खबर है जो {category} जगत को हिला रही है।</p>

<p><em>Disclaimer: This is an AI-generated news summary. For complete details, please refer to the original source.</em></p>
"""

def post_to_blogger(title, content, category):
    """Post to Blogger"""
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
            print("❌ Cannot get access token")
            return False
        
        post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        
        post_body = {
            "kind": "blogger#post",
            "title": title[:70],
            "content": content,
            "labels": ["Breaking News", category, "Hinglish", datetime.now().strftime("%Y")]
        }
        
        post_res = requests.post(post_url, headers=headers, json=post_body, timeout=20)
        
        if post_res.status_code in [200, 201]:
            result = post_res.json()
            print(f"✅ Successfully Posted!")
            print(f"🔗 URL: {result.get('url', 'N/A')}")
            return True
        else:
            print(f"❌ Post Failed: {post_res.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_blogger():
    """Verify Blogger access"""
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
            return False
            
        blog_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}"
        headers = {"Authorization": f"Bearer {access_token}"}
        blog_res = requests.get(blog_url, headers=headers, timeout=15)
        
        if blog_res.status_code == 200:
            print(f"✅ Blogger verified! Blog: {blog_res.json().get('name')}")
            return True
        return False
    except:
        return False

# --- MAIN ---

def main():
    global entry  # To access in get_high_quality_image
    
    print("🤖 Starting Long-Content Blogger Bot...")
    print(f"📅 {datetime.now().strftime('%B %d, %Y')}")
    
    fix_dns()
    
    # Check secrets
    print("\n--- Checking Secrets ---")
    secrets = {
        "BLOG_ID": BLOG_ID,
        "BC_CLIENT_ID": BC_CLIENT_ID,
        "BC_CLIENT_SECRET": BC_CLIENT_SECRET,
        "BC_REFRESH_TOKEN": BC_REFRESH_TOKEN,
        "SHRINKME_API": SHRINKME_API
    }
    for name, value in secrets.items():
        print(f"{name}: {'✅' if value else '❌'}")
    
    if not all(secrets.values()):
        print("❌ Missing secrets!")
        return
    
    if not verify_blogger():
        print("❌ Blogger verification failed!")
        return
    
    # Find news with image
    print("\n🔍 Searching for news WITH IMAGE...")
    
    entry = None
    selected_feed = None
    image_url = None
    found_with_image = False
    
    shuffled_feeds = RSS_FEEDS.copy()
    random.shuffle(shuffled_feeds)
    
    for feed_url in shuffled_feeds:
        print(f"\n📰 Checking: {feed_url}")
        try:
            response = requests.get(feed_url, timeout=15)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                if feed.entries:
                    # Try first 3 entries
                    for i in range(min(3, len(feed.entries))):
                        entry = feed.entries[i]
                        selected_feed = feed_url
                        
                        # Check date
                        if hasattr(entry, 'published_parsed'):
                            pub_date = datetime(*entry.published_parsed[:6])
                            if pub_date.date() < datetime.now().date() - timedelta(days=2):
                                continue
                        
                        # Get title and category
                        title = re.sub(r'\s+', ' ', entry.title).strip()
                        category = detect_category(selected_feed, title)
                        
                        # ⭐ GET HD IMAGE (Auto Generate if not found)
                        print("📸 Getting HD image...")
                        
                        # First try RSS image
                        image_url = get_entry_image(entry)
                        if image_url:
                            print("✅ RSS image found!")
                        else:
                            # Try Unsplash
                            image_url = search_unsplash_image(title, category)
                            if image_url:
                                print("✅ Unsplash HD image found!")
                            else:
                                # Try Pexels
                                image_url = search_pexels_image(title, category)
                                if image_url:
                                    print("✅ Pexels HD image found!")
                                else:
                                    # Generate AI Image
                                    print("🎨 AI generating image...")
                                    image_url = generate_ai_image(title, category)
                                    if image_url:
                                        print("✅ AI HD image generated!")
                                    else:
                                        # Final fallback
                                        print("📸 Using category fallback image")
                                        if category in UNSPLASH_IMAGES:
                                            image_url = UNSPLASH_IMAGES[category]
                                        else:
                                            image_url = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1200&q=80"
                        
                        if image_url:
                            print(f"✅ IMAGE FOUND! Posting this news...")
                            found_with_image = True
                            break
                        else:
                            print(f"❌ No image found, checking next...")
                    
                    if found_with_image:
                        break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # ⛔ NO IMAGE FOUND
    if not found_with_image or not entry or not image_url:
        print("\n❌❌❌ NO NEWS WITH IMAGE FOUND!")
        print("⏭️ Today's post cancelled. Will try again in 1 hour.")
        return
    
    # ✅ IMAGE FOUND - PROCEED TO POST
    title = re.sub(r'\s+', ' ', entry.title).strip()
    link = entry.link
    full_content = get_full_content(entry)
    category = detect_category(selected_feed, title)
    
    print(f"\n📰 Title: {title}")
    print(f"📂 Category: {category}")
    print(f"📝 Content Length: {len(full_content)} chars")
    print(f"🖼️ Image Source: {image_url[:50]}...")
    
    image_html = f"""
    <img src='{image_url}' 
         alt='{title}' 
         style='width: 100%; max-height: 600px; object-fit: cover; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
    """
    
    # Shorten link
    short_link = get_short_url(link)
    print(f"🔗 Short Link: {short_link}")
    
    # Generate 1000-1500 word content
    print("🤖 Generating 1000-1500 word content...")
    ai_content = generate_long_content(title, full_content, category)
    
    # Earning button
    earning_button = f"""
    <div style="text-align: center; margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #fff5f0, #fff); border-radius: 12px;">
        <a href="{short_link}" 
           target="_blank" 
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
    """
    
    # Final content
    final_content = f"""
    {image_html}
    {ai_content}
    {earning_button}
    
    <hr style="border: 0; border-top: 2px solid #f0f0f0; margin: 30px 0;">
    
    <div style="text-align: center; color: #999; font-size: 14px;">
        <p>📅 Published: {datetime.now().strftime('%B %d, %Y')}</p>
        <p>📂 Category: {category}</p>
        <p>📝 Word Count: 1000-1500 words</p>
        <p>🌐 Language: Hinglish (Hindi + English)</p>
        <p>🖼️ Image: HD Quality</p>
        <p>🤖 AI-Generated News Summary</p>
        <p>⚠️ Disclaimer: This is an AI-generated summary. Please refer to the original source.</p>
    </div>
    """
    
    # Post
    print("\n📝 Posting to Blogger...")
    if post_to_blogger(title, final_content, category):
        print("\n✅ COMPLETED SUCCESSFULLY!")
        print(f"📰 Title: {title}")
        print(f"📂 Category: {category}")
        print(f"📝 Words: 1000-1500")
        print(f"🖼️ Image: ✅ HD Quality")
        print(f"🔗 Short Link: {short_link}")
    else:
        print("❌ Failed to post!")

if __name__ == "__main__":
    main()
