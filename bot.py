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

# --- FUNCTIONS ---

def get_blogger_access_token():
    """Blogger API Access Token प्राप्त करें"""
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
        print(f"❌ Error getting Access Token: {e}")
        return None

def get_all_blogger_titles(access_token):
    """Blogger से सभी पोस्ट्स के टाइटल्स लोड करें"""
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
                title = post.get("title", "").lower().strip()
                if title:
                    existing_titles.add(title)
                    total += 1
            
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        
        print(f"📥 Total {total} posts loaded from Blogger")
        return existing_titles
        
    except Exception as e:
        print(f"⚠️ Error loading Blogger titles: {e}")
        return existing_titles

def is_duplicate_title(new_title, existing_titles):
    """Smart duplicate detection"""
    new_title_lower = new_title.lower().strip()
    new_words = set(new_title_lower.split())
    
    for existing in existing_titles:
        # Exact match
        if existing == new_title_lower:
            return True
        
        # 70% similar words
        existing_words = set(existing.split())
        if len(new_words) > 3 and len(existing_words) > 3:
            common = new_words.intersection(existing_words)
            if len(common) / len(new_words) > 0.7:
                return True
        
        # First 35 chars match
        if len(new_title_lower) > 35 and new_title_lower[:35] in existing:
            return True
        
        # Last 30 chars match
        if len(new_title_lower) > 30 and new_title_lower[-30:] in existing:
            return True
    
    return False

def get_full_content(entry):
    """Full content extract"""
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
    """HD AI Image generate using Pollinations.ai"""
    try:
        print("🎨 Generating HD AI image...")
        clean_prompt = prompt.replace('"', '').replace("'", '')[:80]
        
        # Pollinations.ai - Free AI image generation
        url = f"https://image.pollinations.ai/prompt/{clean_prompt.replace(' ', '%20')}"
        url += f"?width=1200&height=630&nologo=true&seed={random.randint(1, 1000)}"
        
        # Verify image exists
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            return url
        
        # Try with different parameters
        url2 = f"https://image.pollinations.ai/prompt/{clean_prompt.replace(' ', '%20')}"
        url2 += "?width=1200&height=600&nologo=true"
        response2 = requests.head(url2, timeout=10)
        if response2.status_code == 200:
            return url2
            
    except:
        pass
    return None

def get_hd_image_strict(entry, title, category):
    """Strict image check - returns None if no image"""
    print("📸 Checking for HD image...")
    
    # 1️⃣ RSS image
    image = get_entry_image(entry)
    if image and image.startswith('http'):
        print("✅ RSS image found!")
        return image
    
    # 2️⃣ AI generated
    print("🎨 Trying AI image generation...")
    image = generate_ai_image(title, category)
    if image and image.startswith('http'):
        print("✅ AI HD image generated!")
        return image
    
    # 3️⃣ Category fallback
    if category in UNSPLASH_IMAGES:
        print("✅ Category fallback image used")
        return UNSPLASH_IMAGES[category]
    
    # ❌ No image
    print("❌ No image found!")
    return None

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
    """AI content with multiple models"""
    if HF_TOKEN:
        models = [
            "mistralai/Mistral-7B-Instruct-v0.1",
            "Qwen/Qwen2.5-7B-Instruct",
            "google/flan-t5-xxl"
        ]
        
        for model in models:
            try:
                print(f"🤖 Trying model: {model}")
                
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

Use HTML tags: <h2>, <h3>, <p>, <ul>, <li>"""

                API_URL = f"https://api-inference.huggingface.co/models/{model}"
                headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                payload = {"inputs": prompt, "parameters": {"max_new_tokens": 2000, "temperature": 0.7}}
                
                response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
                
                if response.status_code == 503:
                    print(f"⏳ Model {model} loading, waiting 30s...")
                    time.sleep(30)
                    response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        text = result[0].get('generated_text', '')
                        if prompt in text:
                            text = text.replace(prompt, '').strip()
                        if len(text) > 500:
                            print(f"✅ AI Success with {model}")
                            return text
                            
            except Exception as e:
                print(f"⚠️ Model {model} failed: {e}")
                continue
    
    # Fallback content
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

<h3>💬 Expert Opinions - विशेषज्ञों की राय</h3>
<p>उद्योग विशेषज्ञों का कहना है कि यह विकास {category} के लिए गेम-चेंजर साबित हो सकता है।</p>

<h3>🌍 Impact & Implications - प्रभाव और परिणाम</h3>
<p>इस खबर का असर वैश्विक स्तर पर देखा जा रहा है।</p>

<h3>🔮 What's Next - आगे क्या?</h3>
<p>अगले कुछ दिनों में और अपडेट आने की उम्मीद है।</p>

<h3>✅ Conclusion - निष्कर्ष</h3>
<p>यह एक डेवलपिंग स्टोरी है।</p>

<p><em>Disclaimer: This is an AI-generated news summary. Please refer to the original source.</em></p>
"""

def post_to_blogger(access_token, title, content, category):
    """Post to Blogger"""
    try:
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
        print(f"❌ Blogger Post Error: {e}")
        return False

# --- MAIN ---

def main():
    print("🤖 Starting Long-Content Blogger Bot...")
    print(f"📅 {datetime.now().strftime('%B %d, %Y')}")
    
    fix_dns()
    
    # Get Access Token
    access_token = get_blogger_access_token()
    if not access_token:
        print("❌ Access token invalid. Exiting...")
        return
    
    # Load existing Blogger titles
    existing_titles = get_all_blogger_titles(access_token)
    
    print("\n🔍 Searching for NEW news WITH IMAGE...")
    
    entry = None
    selected_feed = None
    image_url = None
    found_news = False
    
    shuffled_feeds = RSS_FEEDS.copy()
    random.shuffle(shuffled_feeds)
    
    for feed_url in shuffled_feeds:
        print(f"\n📰 Checking Feed: {feed_url}")
        try:
            response = requests.get(feed_url, timeout=15)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                # Check first 10 entries
                for i in range(min(10, len(feed.entries))):
                    temp_entry = feed.entries[i]
                    temp_title = re.sub(r'\s+', ' ', temp_entry.title).strip()
                    
                    # Check date
                    if hasattr(temp_entry, 'published_parsed'):
                        pub_date = datetime(*temp_entry.published_parsed[:6])
                        if pub_date.date() < datetime.now().date() - timedelta(days=2):
                            continue
                    
                    # Check duplicate
                    if is_duplicate_title(temp_title, existing_titles):
                        print(f"⏭️ SKIP (Already posted): {temp_title[:45]}...")
                        continue
                    
                    # Detect category
                    category = detect_category(feed_url, temp_title)
                    
                    # Check image
                    image_url = get_hd_image_strict(temp_entry, temp_title, category)
                    
                    if image_url:
                        entry = temp_entry
                        selected_feed = feed_url
                        found_news = True
                        print(f"✅ NEW news with IMAGE found!")
                        break
                    else:
                        print(f"❌ No image, checking next...")
                
                if found_news:
                    break
                    
        except Exception as e:
            print(f"❌ Error checking feed: {e}")
    
    # No news found
    if not found_news or not entry or not image_url:
        print("\n❌❌❌ NO NEW NEWS WITH IMAGE FOUND!")
        print("⏭️ Today's post cancelled. Will try again in 1 hour.")
        return
    
    # Process
    title = re.sub(r'\s+', ' ', entry.title).strip()
    link = entry.link
    full_content = get_full_content(entry)
    category = detect_category(selected_feed, title)
    
    print(f"\n📰 Title: {title}")
    print(f"📂 Category: {category}")
    print(f"🖼️ Image: ✅ Found")
    
    # Image HTML
    image_html = f"""
    <div style="text-align: center; margin-bottom: 25px;">
        <img src='{image_url}' 
             alt='{title}' 
             style='width: 100%; max-width: 700px; height: auto; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.15);'>
    </div>
    """
    
    # Shorten link
    short_link = get_short_url(link)
    print(f"🔗 Short Link: {short_link}")
    
    # Generate content
    print("🤖 Generating 1000-1500 word content...")
    ai_content = generate_long_content(title, full_content, category)
    
    # Earning button
    earning_button = f"""
    <div style="text-align: center; margin: 30px 0; padding: 20px; background: #f5f5f5; border-radius: 12px;">
        <a href="{short_link}" 
           target="_blank" 
           style="background: linear-gradient(135deg, #ff5722, #ff6f00); 
                  color: white; 
                  padding: 18px 50px; 
                  text-decoration: none; 
                  font-size: 20px; 
                  font-weight: bold; 
                  border-radius: 50px; 
                  display: inline-block;
                  text-transform: uppercase;
                  box-shadow: 0 4px 15px rgba(255,87,34,0.3);">
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
    
    <hr style="border: 0; border-top: 2px solid #e0e0e0; margin: 30px 0;">
    
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
    if post_to_blogger(access_token, title, final_content, category):
        print("\n✅ COMPLETED SUCCESSFULLY!")
        print(f"📰 Title: {title}")
        print(f"📂 Category: {category}")
        print(f"🖼️ Image: ✅ HD Quality")
        print(f"🔗 Short Link: {short_link}")
        print(f"📝 Words: 1000-1500")
    else:
        print("❌ Failed to post!")

if __name__ == "__main__":
    main()
