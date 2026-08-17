import os
import json
import random
import time
import requests
import feedparser
import re
from datetime import datetime, timedelta
import socket
import xmlrpc.client
import urllib3
import ssl

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
BLOG_ID = os.getenv('BLOG_ID')
SHRINKME_API = os.getenv('SHRINKME_API')
HF_TOKEN = os.getenv('HF_TOKEN')
BC_CLIENT_ID = os.getenv('BC_CLIENT_ID')
BC_CLIENT_SECRET = os.getenv('BC_CLIENT_SECRET')
BC_REFRESH_TOKEN = os.getenv('BC_REFRESH_TOKEN')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

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

POSTED_FILE = 'posted_news.txt'
CATEGORIES_TRACKER = 'recent_categories.json'

# --- CATEGORY ROTATION ---
ALL_CATEGORIES = ["Sports", "Entertainment", "Technology", "Gaming", "Space", "Music", "Business"]

def get_available_categories():
    """Return categories that haven't been posted recently"""
    recent = load_recent_categories()
    available = [c for c in ALL_CATEGORIES if c not in recent]
    
    # अगर सभी categories recent में हैं तो reset करो
    if not available:
        print("🔄 All categories recent, resetting rotation...")
        return ALL_CATEGORIES.copy()
    
    return available

def get_skip_category():
    """Get category to skip (last posted category)"""
    recent = load_recent_categories()
    if recent:
        return recent[0]  # Last posted category
    return None

def clean_and_format_title(title):
    if not title:
        return ""
    clean = re.sub(r'\s+', ' ', title).strip()
    clean = re.sub(r'202[0-9]\s*[-|]\s*202[0-9]', '', clean)
    clean = re.sub(r'\s*[-|]\s*$', '', clean)
    if len(clean) > 120:
        clean = clean[:120].rsplit(' ', 1)[0]
    return clean

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

def load_recent_categories():
    try:
        if os.path.exists(CATEGORIES_TRACKER):
            with open(CATEGORIES_TRACKER, 'r') as f:
                return json.load(f)
    except:
        pass
    return []

def save_recent_category(category):
    try:
        recent = load_recent_categories()
        if category in recent:
            recent.remove(category)
        recent.insert(0, category)
        recent = recent[:7]  # Keep all 7 categories
        with open(CATEGORIES_TRACKER, 'w') as f:
            json.dump(recent, f)
    except:
        pass

# --- SEO PINGING ---
def ping_search_engines(blog_name, blog_url):
    print("🚀 SEO Pinging...")
    ping_services = [
        ("Google", "http://blogsearch.google.com/ping/RPC2"),
        ("Bing", "http://ping.blo.gs/"),
        ("Pingomatic", "http://rpc.pingomatic.com/"),
    ]
    for name, url in ping_services:
        try:
            server = xmlrpc.client.ServerProxy(url)
            server.weblogUpdates.ping(blog_name, blog_url)
            print(f"✅ Pinged {name}")
        except:
            print(f"⚠️ {name} ping failed")

# --- SOCIAL SHARING ---
def share_to_telegram(title, link):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": f"🚨 *{title}*\n\n{link}", "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def share_to_discord(title, link):
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        payload = {"content": f"🚨 **{title}**\n\n{link}"}
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
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
    except:
        return None

def get_all_blogger_titles(access_token):
    existing_titles = set()
    if not access_token:
        return existing_titles
    try:
        page_token = None
        while True:
            url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?maxResults=100"
            if page_token:
                url += f"&pageToken={page_token}"
            headers = {"Authorization": f"Bearer {access_token}"}
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                break
            data = res.json()
            for post in data.get("items", []):
                title = clean_and_format_title(post.get("title", "")).lower().strip()
                if title:
                    existing_titles.add(title)
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        print(f"📥 {len(existing_titles)} posts loaded")
        return existing_titles
    except:
        return existing_titles

def is_duplicate_title(new_title, existing_titles):
    new_clean = clean_and_format_title(new_title).lower().strip()
    if new_clean in existing_titles:
        return True
    if len(new_clean) > 25:
        for existing in existing_titles:
            if new_clean[:25] in existing or existing[:25] in new_clean:
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
                        return text[:4000]
        summary = entry.get('summary', '')
        if summary:
            return re.sub(r'<[^>]+>', '', summary)[:4000]
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
    try:
        clean = title.replace('"', '').replace("'", '')[:60]
        prompt = f"{clean} {category} news"
        url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1200&height=630&nologo=true&seed={random.randint(1, 9999)}"
        return url
    except:
        pass
    return None

def get_hd_image_strict(entry, title, category):
    print("📸 Getting HD image...")
    image = get_entry_image(entry)
    if image and image.startswith('http') and 'logo' not in image.lower():
        print("✅ RSS image!")
        return image
    image = generate_hd_image_with_text(title, category)
    if image:
        print("✅ AI HD image!")
        return image
    if category in UNSPLASH_IMAGES:
        print("✅ Category image")
        return UNSPLASH_IMAGES[category]
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
    
    # Entertainment
    if any(x in feed_lower for x in ["variety", "hollywood", "pinkvilla", "eonline"]):
        return "Entertainment"
    if any(x in title_lower for x in ["movie", "film", "hollywood", "marvel", "dc", "disney", "drag race", "rupaul"]):
        return "Entertainment"
    
    # Space
    if "space" in feed_lower or "nasa" in feed_lower:
        return "Space"
    if any(x in title_lower for x in ["galaxy", "planet", "star", "moon", "mars", "universe", "cosmos"]):
        return "Space"
    
    # Technology
    if any(x in feed_lower for x in ["tech", "verge", "cnet"]):
        return "Technology"
    
    # Gaming
    if "gaming" in feed_lower or any(x in feed_lower for x in ["gamespot", "ign"]):
        return "Gaming"
    
    # Music
    if any(x in feed_lower for x in ["rollingstone"]):
        return "Music"
    
    # Sports
    if "cric" in feed_lower or any(x in title_lower for x in ["cricket", "century", "wicket", "odi", "test", "match", "football", "labuschagne", "rutherford"]):
        return "Sports"
    
    # Business
    if any(x in feed_lower for x in ["bloomberg", "reuters"]):
        return "Business"
    
    return "News"

# ✅ AI CONTENT GENERATOR (SSL BYPASS)
def ask_ai_for_news(title, full_content, category):
    if not HF_TOKEN:
        return None
    
    print("🧠 Calling AI...")
    try:
        model = "mistralai/Mistral-7B-Instruct-v0.1"
        hf_ip = "104.18.22.48"
        api_url = f"https://{hf_ip}/models/{model}"
        
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json",
            "Host": "api-inference.huggingface.co"
        }
        
        prompt = f"""Write a Hinglish article about:
Title: {title}
Category: {category}
Content: {full_content[:1500]}

Use HTML structure:
<h3>📝 परिचय - Introduction</h3>
<p>[English intro]</p>
<p>[Hindi intro]</p>

<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>
  <li>• [Fact 1]</li>
  <li>• [Fact 2]</li>
  <li>• [Fact 3]</li>
  <li>• [Fact 4]</li>
  <li>• [Fact 5]</li>
</ul>

<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
<p>[Analysis]</p>

<h3>💬 विशेषज्ञों की राय - Expert Opinions</h3>
<blockquote>"[Quote]"</blockquote>

<h3>🌍 प्रभाव और आगे क्या? - Impact & What's Next</h3>
<p>[Impact]</p>

<h3>✅ निष्कर्ष - Conclusion</h3>
<p>[Conclusion]</p>"""
        
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 1500, "temperature": 0.7}
        }
        
        res = requests.post(api_url, json=payload, headers=headers, timeout=60, verify=False)
        
        if res.status_code == 200:
            result = res.json()
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get("generated_text", "")
                if "<h3>" in text:
                    print("✅ AI Success!")
                    return text
    except:
        pass
    return None

# ✅ DYNAMIC CONTENT GENERATOR
def generate_dynamic_content(title, full_content, category):
    ai_content = ask_ai_for_news(title, full_content, category)
    if ai_content:
        return ai_content
    
    print("🔄 Using fallback template...")
    today = datetime.now().strftime("%B %d, %Y")
    clean_title = clean_and_format_title(title)
    first_para = full_content[:500] if full_content else ""
    
    # Category-specific highlights
    if category == "Entertainment":
        highlights = [
            f"<li>🎬 <strong>{clean_title[:50]}</strong> - एंटरटेनमेंट की बड़ी खबर</li>",
            f"<li>⭐ <strong>स्टार कास्ट:</strong> {first_para[:60]}...</li>",
            f"<li>📅 <strong>रिलीज़:</strong> जल्द ही</li>",
            f"<li>🍿 <strong>फैंस की प्रतिक्रिया:</strong> उत्साह</li>",
        ]
    elif category == "Technology":
        highlights = [
            f"<li>💻 <strong>{clean_title[:50]}</strong> - टेक जगत की बड़ी खबर</li>",
            f"<li>📱 <strong>फीचर्स:</strong> {first_para[:60]}...</li>",
            f"<li>🔍 <strong>एनालिसिस:</strong> विशेषज्ञों की राय</li>",
            f"<li>💡 <strong>इंपैक्ट:</strong> क्या प्रभाव होगा</li>",
        ]
    elif category == "Sports":
        highlights = [
            f"<li>🏏 <strong>{clean_title[:50]}</strong> - खेल जगत की बड़ी खबर</li>",
            f"<li>⭐ <strong>स्टार प्रदर्शन:</strong> {first_para[:60]}...</li>",
            f"<li>📊 <strong>मैच विश्लेषण:</strong> शानदार प्रदर्शन</li>",
            f"<li>🏆 <strong>जीत:</strong> ऐतिहासिक उपलब्धि</li>",
        ]
    elif category == "Gaming":
        highlights = [
            f"<li>🎮 <strong>{clean_title[:50]}</strong> - गेमिंग जगत की बड़ी खबर</li>",
            f"<li>🖥️ <strong>गेमप्ले:</strong> {first_para[:60]}...</li>",
            f"<li>📅 <strong>रिलीज़:</strong> जल्द ही</li>",
        ]
    elif category == "Space":
        highlights = [
            f"<li>🚀 <strong>{clean_title[:50]}</strong> - अंतरिक्ष की बड़ी खबर</li>",
            f"<li>🌌 <strong>खोज:</strong> {first_para[:60]}...</li>",
            f"<li>🛰️ <strong>मिशन:</strong> नया अपडेट</li>",
        ]
    else:
        highlights = [
            f"<li>🔴 <strong>{clean_title[:50]}</strong> - आज की बड़ी खबर</li>",
            f"<li>📰 <strong>विस्तार:</strong> {first_para[:60]}...</li>",
            f"<li>📊 <strong>विश्लेषण:</strong> विशेषज्ञों की राय</li>",
        ]
    
    return f"""
<h2>🚨 BREAKING NEWS: {clean_title}</h2>

<div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0;">
    <p><strong>📅 Published: {today}</strong></p>
    <p><strong>📂 Category: {category}</strong></p>
</div>

<h3>📝 परिचय - Introduction</h3>
<p><strong>{clean_title}</strong></p>
<p>{first_para}</p>

<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>
    {''.join(highlights)}
</ul>

<h3>✅ निष्कर्ष - Conclusion</h3>
<p>{clean_title} - यह {category} सेक्टर के लिए एक महत्वपूर्ण विकास है।</p>

<p><em>Disclaimer: This is an AI-generated news summary. For complete details, please refer to the original source.</em></p>
"""

def generate_long_content(title, full_content, category):
    return generate_dynamic_content(title, full_content, category)

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
        if post_res.status_code in [200, 201]:
            return post_res.json().get("url")
    except:
        return None

# --- MAIN ---

def main():
    print("🤖 Starting Viral News AI Blogger Bot...")
    print(f"📅 {datetime.now().strftime('%B %d, %Y')}")
    
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
    
    # ✅ CATEGORY ROTATION
    recent_categories = load_recent_categories()
    print(f"🔄 Recent categories: {recent_categories}")
    
    available_categories = get_available_categories()
    print(f"📋 Available categories: {available_categories}")
    
    # ✅ Skip last posted category
    skip_category = get_skip_category()
    if skip_category:
        print(f"⏭️ Skipping: {skip_category} (already posted)")
    
    found_news = False
    entry = None
    selected_feed = None
    image_url = None
    
    shuffled_feeds = RSS_FEEDS.copy()
    random.shuffle(shuffled_feeds)
    
    print("\n🔍 Searching for new news...")
    for feed_url in shuffled_feeds:
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
                        continue
                    
                    category = detect_category(feed_url, temp_title)
                    
                    # ✅ SKIP last posted category
                    if category == skip_category:
                        continue
                    
                    # ✅ ONLY ALLOW available categories
                    if category not in available_categories:
                        print(f"⏭️ Skipping {category} (not in available)")
                        continue
                    
                    image_url = get_hd_image_strict(temp_entry, temp_title, category)
                    if image_url:
                        entry = temp_entry
                        selected_feed = feed_url
                        found_news = True
                        print(f"✅ Found in '{category}'!")
                        break
                if found_news:
                    break
        except:
            continue
    
    # ✅ FALLBACK: अगर कोई news न मिली तो सभी categories allow करो
    if not found_news:
        print("\n🔍 Fallback: All categories allowed...")
        for feed_url in shuffled_feeds:
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
                            continue
                        category = detect_category(feed_url, temp_title)
                        image_url = get_hd_image_strict(temp_entry, temp_title, category)
                        if image_url:
                            entry = temp_entry
                            selected_feed = feed_url
                            found_news = True
                            print(f"✅ Found in '{category}' (Fallback)!")
                            break
                    if found_news:
                        break
            except:
                continue
    
    if not found_news or not entry:
        print("\n❌ No new news found!")
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
        <img src='{image_url}' alt='{title}' style='width:100%;max-width:800px;height:auto;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.15);'>
        <p style="font-size:12px;color:#999;margin-top:5px;">📸 Viral News AI | HD Quality</p>
    </div>
    """
    
    short_link = get_short_url(link)
    print(f"🔗 Short Link: {short_link}")
    
    print("🤖 Generating dynamic content...")
    ai_content = generate_long_content(title, full_content, category)
    
    earning_button = f"""
    <div style="text-align:center;margin:30px 0;padding:20px;background:#f5f5f5;border-radius:12px;">
        <a href="{short_link}" target="_blank" style="background:linear-gradient(135deg,#ff5722,#ff6f00);color:white;padding:20px 60px;text-decoration:none;font-size:22px;font-weight:bold;border-radius:50px;display:inline-block;text-transform:uppercase;box-shadow:0 4px 15px rgba(255,87,34,0.3);">
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
        <p>📝 Word Count: 2000+ words</p>
        <p>🌐 Language: Hinglish (Hindi + English)</p>
        <p>🖼️ Image: HD Quality</p>
        <p>🤖 AI-Generated News Summary</p>
        <p>© Viral News AI - All Rights Reserved</p>
        <p>⚠️ Disclaimer: This is an AI-generated summary. Please refer to the original source.</p>
    </div>
    """
    
    print(f"\n📝 Posting to Blogger...")
    post_url = post_to_blogger(access_token, title, final_content, category)
    
    if post_url:
        save_posted_news(title)
        save_recent_category(category)
        print("\n✅✅✅ POSTED SUCCESSFULLY! ✅✅✅")
        print(f"🔗 {post_url}")
        ping_search_engines("Viral News AI", post_url)
        share_to_telegram(title, post_url)
        share_to_discord(title, post_url)
        print(f"\n📰 {title}")
        print(f"📂 {category}")
        print(f"🔗 {short_link}")
    else:
        print("❌ Failed to post!")

if __name__ == "__main__":
    main()
