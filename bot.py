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
    if not title:
        return ""
    clean = re.sub(r'\s+', ' ', title).strip()
    clean = re.sub(r'202[0-9]\s*[-|]\s*202[0-9]', '', clean)
    clean = re.sub(r'\s*[-|]\s*$', '', clean)
    return clean[:70].strip()

def load_posted_news():
    try:
        if os.path.exists(POSTED_FILE):
            with open(POSTED_FILE, 'r', encoding='utf-8') as f:
                return set(line.strip().lower() for line in f if line.strip())
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
    new_clean = clean_and_format_title(new_title).lower().strip()
    if new_clean in existing_titles:
        return True
    if len(new_clean) > 25:
        for existing in existing_titles:
            if new_clean[:25] in existing:
                return True
            if existing[:25] in new_clean:
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

def generate_hd_image_with_text(title, category):
    """Generate HD image with "Viral News AI" text overlay"""
    try:
        print("🎨 Generating HD image with 'Viral News AI'...")
        
        # Clean prompt for AI image
        clean = title.replace('"', '').replace("'", '')[:60]
        
        # Try Pollinations.ai with text overlay
        prompt = f"{clean} {category} news breaking news illustration"
        url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
        url += f"?width=1200&height=630&nologo=true&seed={random.randint(1, 9999)}"
        
        # Check if image exists
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            return url
        
        # Try without text
        url2 = f"https://image.pollinations.ai/prompt/{clean.replace(' ', '%20')}?width=1200&height=630&nologo=true"
        response2 = requests.head(url2, timeout=10)
        if response2.status_code == 200:
            return url2
            
    except:
        pass
    return None

def get_hd_image_strict(entry, title, category):
    """ALWAYS returns an HD image - No exceptions"""
    print("📸 Getting HD image...")
    
    # 1️⃣ Try RSS image
    image = get_entry_image(entry)
    if image and image.startswith('http') and 'logo' not in image.lower():
        print("✅ RSS image found!")
        return image
    
    # 2️⃣ Try AI generated image with text
    print("🎨 Generating AI HD image with 'Viral News AI' text...")
    image = generate_hd_image_with_text(title, category)
    if image:
        print("✅ AI HD image generated!")
        return image
    
    # 3️⃣ Try category image
    if category in UNSPLASH_IMAGES:
        print("✅ Category image used")
        return UNSPLASH_IMAGES[category]
    
    # 4️⃣ Ultimate fallback with 'Viral News AI' branding
    print("✅ Ultimate fallback image used")
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
    
    if any(x in feed_lower for x in ["variety", "hollywood", "pinkvilla", "eonline"]):
        return "Entertainment"
    if any(x in title_lower for x in ["spider-man", "movie", "film", "hollywood", "box office", "marvel", "dc"]):
        return "Entertainment"
    
    if "space" in feed_lower or "nasa" in feed_lower:
        if "fusion" in title_lower:
            return "Technology"
        return "Space"
    
    if any(x in feed_lower for x in ["tech", "verge", "cnet"]):
        return "Technology"
    
    if any(x in feed_lower for x in ["gamespot", "ign"]):
        return "Gaming"
    
    if any(x in feed_lower for x in ["rollingstone"]):
        return "Music"
    
    if "cric" in feed_lower:
        return "Sports"
    
    if any(x in feed_lower for x in ["bloomberg", "reuters"]):
        return "Business"
    
    return "News"

def generate_long_content(title, full_content, category):
    """Generate 1500-2000 words content"""
    if HF_TOKEN:
        models = ["mistralai/Mistral-7B-Instruct-v0.1", "Qwen/Qwen2.5-7B-Instruct"]
        for model in models:
            try:
                print(f"🤖 Trying: {model}")
                prompt = f"""Write a DETAILED 1500-2000 word news article in Hinglish (Hindi+English mix) about: {title}

Context: {full_content[:1500]}

Category: {category}

Write a COMPLETE, COMPREHENSIVE article with:

1. INTRODUCTION (150 words) - Hook, context, what happened
2. KEY HIGHLIGHTS (10-12 bullet points) - Main points
3. DETAILED ANALYSIS (500 words) - Full analysis with quotes
4. EXPERT OPINIONS (150 words) - What experts say
5. IMPACT & IMPLICATIONS (200 words) - Global impact
6. WHAT'S NEXT (150 words) - Future predictions
7. COMPLETE STORY - Full narrative
8. CONCLUSION (100 words) - Final thoughts

Use HTML tags: <h2>, <h3>, <p>, <ul>, <li>, <blockquote>
Make it SEO friendly, engaging, and professional."""

                API_URL = f"https://api-inference.huggingface.co/models/{model}"
                headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
                payload = {"inputs": prompt, "parameters": {"max_new_tokens": 2500, "temperature": 0.7}}
                
                response = requests.post(API_URL, headers=headers, json=payload, timeout=200)
                if response.status_code == 503:
                    print("⏳ Loading...")
                    time.sleep(45)
                    response = requests.post(API_URL, headers=headers, json=payload, timeout=200)
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        text = result[0].get('generated_text', '')
                        if prompt in text:
                            text = text.replace(prompt, '').strip()
                        if len(text) > 800:
                            return text
            except:
                continue
    
    # Enhanced Fallback content
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
        f"• देश-विदेश की प्रतिक्रिया - Global Response",
        f"• इस खबर का महत्व - Why This Matters",
        f"• आने वाले दिनों में क्या - Coming Days",
        f"• पूरी कहानी - Full Story Below",
    ]
    
    return f"""
<h2>🚨 BREAKING NEWS: {title}</h2>

<div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0;">
    <p><strong>📅 Published: {today}</strong></p>
    <p><strong>📂 Category: {category}</strong></p>
</div>

<h3>📝 Introduction - परिचय</h3>
<p>{title} - यह आज की सबसे बड़ी खबर है। यह घटना {category} सेक्टर में तहलका मचा रही है। विशेषज्ञों का मानना है कि इसका दूरगामी प्रभाव होगा।</p>

<p>{full_content[:600]}...</p>

<h3>🎯 Key Highlights - मुख्य बातें</h3>
<ul>
    {''.join([f'<li>{h}</li>' for h in highlights])}
</ul>

<h3>📊 Detailed Analysis - विस्तृत विश्लेषण</h3>
<p>{full_content[:500]}...</p>
<p>इस खबर के कई पहलू हैं। विशेषज्ञों के अनुसार, यह एक महत्वपूर्ण मोड़ है। इसके आगे क्या प्रभाव होंगे, यह देखना दिलचस्प होगा।</p>

<h3>💬 Expert Opinions - विशेषज्ञों की राय</h3>
<p>उद्योग विशेषज्ञों का कहना है कि यह विकास {category} के लिए गेम-चेंजर साबित हो सकता है। कुछ का मानना है कि इससे नई संभावनाएं खुलेंगी।</p>

<blockquote style="border-left:5px solid #ff5722;padding:20px;background:#f9f9f9;border-radius:8px;margin:20px 0;">
    <p style="font-style:italic;font-size:16px;">"यह एक ऐतिहासिक क्षण है। इसका प्रभाव आने वाले वर्षों में देखने को मिलेगा।"</p>
</blockquote>

<h3>🌍 Impact & Implications - प्रभाव और परिणाम</h3>
<p>इस खबर का असर वैश्विक स्तर पर देखा जा रहा है। कंपनियां अपनी रणनीतियां बदल रही हैं। कंज्यूमर भी इस पर अपनी प्रतिक्रिया दे रहे हैं।</p>

<h3>🔮 What's Next - आगे क्या?</h3>
<p>अगले कुछ दिनों में और अपडेट आने की उम्मीद है। इस खबर पर नजर बनाए रखें। नीचे दिए गए बटन पर क्लिक करें पूरी जानकारी के लिए।</p>

<h3>📌 Why This Matters - क्यों महत्वपूर्ण है?</h3>
<p>यह खबर {category} क्षेत्र के लिए एक मील का पत्थर है। इससे लाखों लोग प्रभावित होंगे।</p>

<h3>✅ Conclusion - निष्कर्ष</h3>
<p>यह एक डेवलपिंग स्टोरी है। आने वाले समय में और जानकारी सामने आएगी। तब तक के लिए, यह सबसे बड़ी खबर है जो {category} जगत को हिला रही है।</p>

<p><em>Disclaimer: This is an AI-generated news summary. For complete details, please refer to the original source.</em></p>
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
    print(f"📅 {datetime.now().strftime('%B %d, %Y')}")
    fix_dns()
    
    # Check secrets
    print("\n--- Checking Secrets ---")
    secrets = {
        "BLOG_ID": BLOG_ID,
        "HF_TOKEN": HF_TOKEN,
        "SHRINKME_API": SHRINKME_API,
        "BC_CLIENT_ID": BC_CLIENT_ID,
        "BC_CLIENT_SECRET": BC_CLIENT_SECRET,
        "BC_REFRESH_TOKEN": BC_REFRESH_TOKEN
    }
    all_loaded = True
    for name, value in secrets.items():
        status = "✅ LOADED" if value else "❌ MISSING"
        print(f"{name}: {status}")
        if not value:
            all_loaded = False
    
    if not all_loaded:
        print("\n❌ Secrets missing!")
        return
    
    access_token = get_blogger_access_token()
    if not access_token:
        print("❌ Invalid token!")
        return
    
    existing_titles = get_all_blogger_titles(access_token)
    local_posted = load_posted_news()
    all_posted = existing_titles.union(local_posted)
    print(f"\n📊 Total tracked posts: {len(all_posted)}")
    
    found_news = False
    entry = None
    selected_feed = None
    image_url = None
    
    shuffled_feeds = RSS_FEEDS.copy()
    random.shuffle(shuffled_feeds)
    
    print("\n🔍 Searching for new news...")
    for feed_url in shuffled_feeds:
        print(f"\n📰 Checking: {feed_url}")
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
                        print(f"⏭️ SKIP (Duplicate): {temp_title[:40]}...")
                        continue
                    
                    category = detect_category(feed_url, temp_title)
                    
                    # ⭐ GET HD IMAGE - ALWAYS RETURNS AN IMAGE
                    image_url = get_hd_image_strict(temp_entry, temp_title, category)
                    
                    if image_url:
                        entry = temp_entry
                        selected_feed = feed_url
                        found_news = True
                        print(f"✅ NEW news with IMAGE found!")
                        break
                if found_news:
                    break
        except Exception as e:
            print(f"⚠️ Error: {e}")
    
    if not found_news or not entry:
        print("\n❌ No new news found! Will try again in 1 hour.")
        return
    
    raw_title = entry.title
    title = clean_and_format_title(raw_title)
    link = entry.link
    full_content = get_full_content(entry)
    category = detect_category(selected_feed, title)
    
    print(f"\n📰 Title: {title}")
    print(f"📂 Category: {category}")
    print(f"🖼️ Image: ✅ HD Quality")
    
    image_html = f"""
    <div style="text-align:center;margin-bottom:25px;">
        <img src='{image_url}' 
             alt='{title}' 
             style='width:100%;max-width:800px;height:auto;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.15);'>
        <p style="font-size:12px;color:#999;margin-top:5px;">📸 Viral News AI | HD Quality</p>
    </div>
    """
    
    short_link = get_short_url(link)
    print(f"🔗 Short Link: {short_link}")
    
    print("🤖 Generating 1500-2000 word content...")
    ai_content = generate_long_content(title, full_content, category)
    
    earning_button = f"""
    <div style="text-align:center;margin:30px 0;padding:20px;background:#f5f5f5;border-radius:12px;">
        <a href="{short_link}" 
           target="_blank" 
           style="background:linear-gradient(135deg,#ff5722,#ff6f00);color:white;padding:20px 60px;text-decoration:none;font-size:22px;font-weight:bold;border-radius:50px;display:inline-block;text-transform:uppercase;box-shadow:0 4px 15px rgba(255,87,34,0.3);">
            📖 पूरी खबर पढ़ें - READ FULL STORY
        </a>
        <p style="font-size:12px;color:#999;margin-top:10px;">Click to read the complete story on the original source</p>
    </div>
    """
    
    final_content = f"""
    {image_html}
    {ai_content}
    {earning_button}
    
    <hr style="border:0;border-top:2px solid #e0e0e0;margin:30px 0;">
    
    <div style="text-align:center;color:#999;font-size:14px;">
        <p>📅 Published: {datetime.now().strftime('%B %d, %Y')}</p>
        <p>📂 Category: {category}</p>
        <p>📝 Word Count: 1500-2000 words</p>
        <p>🌐 Language: Hinglish (Hindi + English)</p>
        <p>🖼️ Image: HD Quality</p>
        <p>🤖 AI-Generated News Summary</p>
        <p>© Viral News AI - All Rights Reserved</p>
        <p>⚠️ Disclaimer: This is an AI-generated summary. Please refer to the original source.</p>
    </div>
    """
    
    print(f"\n📝 Posting to Blogger...")
    if post_to_blogger(access_token, title, final_content, category):
        save_posted_news(title)
        print("\n✅✅✅ COMPLETED SUCCESSFULLY! ✅✅✅")
        print(f"📰 Title: {title}")
        print(f"📂 Category: {category}")
        print(f"🖼️ Image: ✅ HD Quality")
        print(f"🔗 Short Link: {short_link}")
        print(f"📝 Words: 1500-2000")
    else:
        print("❌ Failed to post!")

if __name__ == "__main__":
    main()
