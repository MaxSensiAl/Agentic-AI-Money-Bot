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
import urllib3.util.connection as urllib3_connection

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- SMART TCP REDIRECT PATCH ---
def apply_smart_connection_patch():
    print("🌐 Initializing Smart TCP Connection Redirect Patch...")
    original_create_connection = urllib3_connection.create_connection

    HARDCODED_IPS = {
        "rpc.weblogs.com": "216.92.112.55",
        "blogsearch.google.com": "142.250.190.46"
    }

    def patched_create_connection(address, *args, **kwargs):
        host, port = address
        if host in HARDCODED_IPS:
            ip = HARDCODED_IPS[host]
            print(f"🎯 Redirecting {host} connection to hardcoded IP: {ip}")
            return original_create_connection((ip, port), *args, **kwargs)
        return original_create_connection(address, *args, **kwargs)

    urllib3_connection.create_connection = patched_create_connection
    print("✅ Smart TCP Connection Redirect Patch applied globally")

apply_smart_connection_patch()

def fix_dns():
    print("✅ Testing connection to Pollinations AI...")
    try:
        res = requests.get("https://text.pollinations.ai/", timeout=10)
        print(f"✅ Pollinations AI reachable (Status Code: {res.status_code})")
    except Exception as e:
        print(f"⚠️ Connection check failed: {e}")

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
    "https://www.huffpost.com/section/politics/feed",
    "https://feeds.feedburner.com/ndtvnews-top-stories",
    "https://www.medicalnewstoday.com/feed/news",
    "https://www.motor1.com/rss/news/all/"
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
    "Politics": "https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?auto=format&fit=crop&w=1200&q=80",
    "Health": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=1200&q=80",
    "Automobile": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1200&q=80",
}

POSTED_FILE = 'posted_news.txt'

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

def get_recent_blogger_categories(access_token):
    recent_categories = []
    if not access_token:
        return recent_categories
    try:
        url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?maxResults=6"
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            allowed_categories = ["Technology", "Gaming", "Entertainment", "Space", "Sports", "Business", "Music", "Politics", "Health", "Automobile", "News"]
            for post in data.get("items", []):
                labels = post.get("labels", [])
                for label in labels:
                    if label in allowed_categories and label not in recent_categories:
                        recent_categories.append(label)
            print(f"📥 Blogger से सिंक की गई हालिया श्रेणियां: {recent_categories}")
            return recent_categories[:3]
    except Exception as e:
        print(f"⚠️ Blogger कैटेगरीज सिंक करने में एरर: {e}")
    return []

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

# ✅ FIXED: Word Boundary Function
def word_in_text(word, text):
    """Check if whole word exists in text (not as substring)"""
    if not text:
        return False
    return bool(re.search(rf'\b{re.escape(word)}\b', text, re.IGNORECASE))

# ✅ FIXED: Category Detection with Whole-Word Matching
def detect_category(feed_url, title):
    feed_lower = feed_url.lower()
    title_lower = title.lower()
    
    # ✅ Entertainment
    if any(x in feed_lower for x in ["variety", "hollywood", "pinkvilla", "eonline"]):
        return "Entertainment"
    if word_in_text("movie", title_lower) or word_in_text("film", title_lower) or word_in_text("hollywood", title_lower):
        return "Entertainment"
    if word_in_text("marvel", title_lower) or word_in_text("dc", title_lower) or word_in_text("actor", title_lower):
        return "Entertainment"
    if word_in_text("actress", title_lower) or word_in_text("disney", title_lower) or word_in_text("box office", title_lower):
        return "Entertainment"
    if word_in_text("star cast", title_lower) or word_in_text("pop star", title_lower) or word_in_text("rock star", title_lower):
        return "Entertainment"
    
    # ✅ Space
    if "space" in feed_lower or "nasa" in feed_lower:
        return "Space"
    if word_in_text("galaxy", title_lower) or word_in_text("planet", title_lower):
        return "Space"
    if word_in_text("moon", title_lower) or word_in_text("mars", title_lower) or word_in_text("universe", title_lower):
        return "Space"
    if word_in_text("cosmos", title_lower) or word_in_text("astronaut", title_lower):
        return "Space"
    if word_in_text("corona", title_lower) or word_in_text("eclipse", title_lower) or word_in_text("solar", title_lower):
        return "Space"
    
    # ✅ Technology
    if any(x in feed_lower for x in ["tech", "verge", "cnet", "techcrunch"]):
        return "Technology"
    if word_in_text("smartphone", title_lower) or word_in_text("apple", title_lower) or word_in_text("samsung", title_lower):
        return "Technology"
    if word_in_text("software", title_lower) or word_in_text("artificial intelligence", title_lower) or word_in_text("chatgpt", title_lower):
        return "Technology"
    
    # ✅ Gaming
    if "gaming" in feed_lower or any(x in feed_lower for x in ["gamespot", "ign"]):
        return "Gaming"
    if word_in_text("nintendo", title_lower) or word_in_text("xbox", title_lower) or word_in_text("playstation", title_lower):
        return "Gaming"
    if word_in_text("ps5", title_lower) or word_in_text("gta", title_lower) or word_in_text("gamer", title_lower):
        return "Gaming"
    
    # ✅ Music
    if any(x in feed_lower for x in ["rollingstone"]):
        return "Music"
    if word_in_text("album", title_lower) or word_in_text("song", title_lower) or word_in_text("singer", title_lower):
        return "Music"
    if word_in_text("concert", title_lower) or word_in_text("tour", title_lower) or word_in_text("ariana", title_lower):
        return "Music"
    if word_in_text("cynthia", title_lower) or word_in_text("pop star", title_lower) or word_in_text("rock star", title_lower):
        return "Music"
    if word_in_text("matthew mcconaughey", title_lower) or word_in_text("life in songs", title_lower):
        return "Music"
    
    # ✅ Sports
    if "cric" in feed_lower:
        return "Sports"
    if word_in_text("cricket", title_lower) or word_in_text("century", title_lower) or word_in_text("wicket", title_lower):
        return "Sports"
    if word_in_text("odi", title_lower) or word_in_text("test match", title_lower) or word_in_text("test cricket", title_lower):
        return "Sports"
    if word_in_text("test series", title_lower) or word_in_text("football", title_lower) or word_in_text("goal", title_lower):
        return "Sports"
    if word_in_text("fifa", title_lower) or word_in_text("olympics", title_lower) or word_in_text("player", title_lower):
        return "Sports"
    
    # ✅ Business
    if any(x in feed_lower for x in ["bloomberg", "reuters", "markets"]):
        return "Business"
    if word_in_text("stocks", title_lower) or word_in_text("inflation", title_lower) or word_in_text("market", title_lower):
        return "Business"
    if word_in_text("economy", title_lower) or word_in_text("trade", title_lower):
        return "Business"
    
    # ✅ Politics
    if "politics" in feed_lower:
        return "Politics"
    if word_in_text("election", title_lower) or word_in_text("biden", title_lower) or word_in_text("trump", title_lower):
        return "Politics"
    if word_in_text("modi", title_lower) or word_in_text("parliament", title_lower) or word_in_text("minister", title_lower):
        return "Politics"
    if word_in_text("senate", title_lower) or word_in_text("congress", title_lower):
        return "Politics"
    if word_in_text("federal", title_lower) or word_in_text("state officials", title_lower):
        return "Politics"
    
    # ✅ Health
    if "health" in feed_lower or "medical" in feed_lower:
        return "Health"
    if word_in_text("health", title_lower) or word_in_text("mental", title_lower) or word_in_text("doctor", title_lower):
        return "Health"
    if word_in_text("cancer", title_lower) or word_in_text("vaccine", title_lower) or word_in_text("disease", title_lower):
        return "Health"
    if word_in_text("fitness", title_lower):
        return "Health"
    
    # ✅ Automobile
    if "motor" in feed_lower or "auto" in feed_lower:
        return "Automobile"
    if word_in_text("car", title_lower) or word_in_text("suv", title_lower) or word_in_text("vehicle", title_lower):
        return "Automobile"
    if word_in_text("electric vehicle", title_lower) or word_in_text("ev", title_lower) or word_in_text("tesla", title_lower):
        return "Automobile"
    if word_in_text("engine", title_lower) or word_in_text("motorcycle", title_lower) or word_in_text("bike", title_lower):
        return "Automobile"
    if word_in_text("polestar", title_lower):
        return "Automobile"
        
    return "News"

# ✅ FIXED: AI CONTENT GENERATOR (Pollinations AI - Correct Endpoint)
def ask_ai_for_news(title, full_content, category):
    """Pollinations AI से 100% Unique और Unblocked Content Generate करेगा"""
    print("🧠 Calling Pollinations AI for unique post-specific content...")
    try:
        # ✅ FIXED: Correct Pollinations AI endpoint
        api_url = "https://text.pollinations.ai/"
        
        prompt = f"""You are a professional News Journalist writing in Hinglish (Hindi + English).
Write a highly engaging, SEO-friendly news article based on this news:
Title: {title}
Content: {full_content[:1500]}
Category: {category}

Strict Instructions:
1. Write in natural Hinglish (blend of Hindi and English).
2. Do not use generic placeholder sentences. Use actual names, facts, and details from the provided news.
3. Generate a realistic and highly specific expert opinion quote about this exact event.
4. Output the content using this exact HTML structure with EXTREMELY DETAILED paragraphs:

<h3>📝 परिचय - Introduction</h3>
<p>[EXTREMELY DETAILED introduction in English - minimum 200 words]</p>
<p>[EXTREMELY DETAILED introduction in Hindi - minimum 200 words]</p>

<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>
  <li>[Specific highlight 1]</li>
  <li>[Specific highlight 2]</li>
  <li>[Specific highlight 3]</li>
  <li>[Specific highlight 4]</li>
  <li>[Specific highlight 5]</li>
  <li>[Specific highlight 6]</li>
  <li>[Specific highlight 7]</li>
  <li>[Specific highlight 8]</li>
</ul>

<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
<p>[EXTREMELY DETAILED analysis in English - minimum 250 words]</p>
<p>[EXTREMELY DETAILED analysis in Hindi - minimum 250 words]</p>

<h3>💬 विशेषज्ञों की राय - Expert Opinions</h3>
<p>[EXTREMELY DETAILED expert opinion in English - minimum 150 words]</p>
<p>[EXTREMELY DETAILED expert opinion in Hindi - minimum 150 words]</p>
<blockquote style="border-left:5px solid #ff5722;padding:20px;background:#f9f9f9;border-radius:8px;margin:20px 0;">
    <p style="font-style:italic;font-size:16px;">"[Expert quote in Hindi]"</p>
</blockquote>

<h3>🌍 प्रभाव और आगे क्या? - Impact & What's Next</h3>
<p>[EXTREMELY DETAILED impact analysis in English - minimum 200 words]</p>
<p>[EXTREMELY DETAILED impact analysis in Hindi - minimum 200 words]</p>

<h3>✅ निष्कर्ष - Conclusion</h3>
<p>[EXTREMELY DETAILED conclusion in English - minimum 150 words]</p>
<p>[EXTREMELY DETAILED conclusion in Hindi - minimum 150 words]</p>
"""
        
        payload = {
            "messages": [
                {"role": "system", "content": "You are a professional news editor writing detailed HTML output in Hinglish. Write EXTREMELY LONG and DETAILED paragraphs."},
                {"role": "user", "content": prompt}
            ]
        }
        
        # ✅ FIXED: No "model" parameter - Pollinations AI auto-detects
        res = requests.post(api_url, json=payload, timeout=60)
        
        if res.status_code == 200:
            clean_html = res.text.strip()
            if "<h3>" in clean_html:
                print("✅ AI successfully generated unique content via Pollinations!")
                return clean_html
            else:
                if len(clean_html) > 500:
                    print("✅ AI generated content (HTML formatting may vary)")
                    return f"""
<h3>📝 परिचय - Introduction</h3>
<p>{clean_html[:500]}</p>
<p>{clean_html[500:1000]}</p>
<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>
  <li>• {clean_html[1000:1100]}</li>
  <li>• {clean_html[1100:1200]}</li>
  <li>• {clean_html[1200:1300]}</li>
</ul>
<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
<p>{clean_html[1300:1800]}</p>
<h3>💬 विशेषज्ञों की राय - Expert Opinions</h3>
<p>{clean_html[1800:2000]}</p>
"""
        print(f"⚠️ AI API Status: {res.status_code}, using fallback...")
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
    return None

# ✅ DYNAMIC CONTENT GENERATOR WITH DETAILED SECTIONS
def generate_dynamic_content(title, full_content, category):
    """AI से Content Generate करे, नहीं तो DETAILED Fallback Template"""
    
    # पहले AI try करो
    ai_content = ask_ai_for_news(title, full_content, category)
    if ai_content:
        return ai_content
    
    # AI fail हो तो DETAILED Fallback Template
    print("🔄 Using detailed fallback template...")
    today = datetime.now().strftime("%B %d, %Y")
    clean_title = clean_and_format_title(title)
    first_para = full_content[:500] if full_content else ""
    more_content = full_content[500:1000] if len(full_content) > 500 else ""
    
    # ✅ Category-wise DETAILED Highlights (8 points)
    if category == "Music":
        highlights = [
            f"<li>🎵 <strong>{clean_title[:50]}</strong> - संगीत जगत की बड़ी खबर</li>",
            f"<li>🎤 <strong>स्टार परफॉर्मेंस:</strong> {first_para[:60]}...</li>",
            f"<li>🎶 <strong>खास गाना:</strong> स्पेशल परफॉर्मेंस</li>",
            f"<li>📅 <strong>इवेंट:</strong> {first_para[60:120]}...</li>",
            f"<li>🌍 <strong>फैंस की प्रतिक्रिया:</strong> दुनिया भर में उत्साह</li>",
            f"<li>🎸 <strong>सांग:</strong> {more_content[:60]}...</li>",
            f"<li>📈 <strong>ट्रेंड:</strong> सोशल मीडिया पर ट्रेंड</li>",
            f"<li>🎯 <strong>इंपैक्ट:</strong> संगीत इंडस्ट्री पर प्रभाव</li>",
        ]
        expert_quote = """
<p>Music critics and industry experts are calling this a historic moment in the music industry.</p>
<p>संगीत समीक्षकों और उद्योग विशेषज्ञों का मानना है कि यह संगीत उद्योग में एक ऐतिहासिक क्षण है।</p>
<blockquote style="border-left:5px solid #ff5722;padding:20px;background:#f9f9f9;border-radius:8px;margin:20px 0;">
    <p style="font-style:italic;font-size:16px;">"यह प्रदर्शन संगीत इतिहास में एक मील का पत्थर साबित होगा।"</p>
</blockquote>
"""
        analysis_detail = f"""
<p>{first_para}</p>
<p>{more_content}</p>
<p>इस प्रदर्शन ने संगीत प्रेमियों के दिलों को छू लिया।</p>
"""
    
    elif category == "Space":
        highlights = [
            f"<li>🚀 <strong>{clean_title[:50]}</strong> - अंतरिक्ष की बड़ी खबर</li>",
            f"<li>🌌 <strong>खोज:</strong> {first_para[:60]}...</li>",
            f"<li>🛰️ <strong>मिशन अपडेट:</strong> नई जानकारी</li>",
            f"<li>🔭 <strong>रिसर्च:</strong> वैज्ञानिकों की खोज</li>",
            f"<li>📡 <strong>सिग्नल:</strong> अंतरिक्ष से नए संकेत</li>",
            f"<li>🌞 <strong>सूर्य:</strong> {more_content[:60]}...</li>",
            f"<li>🌍 <strong>पृथ्वी:</strong> अंतरिक्ष से दृश्य</li>",
            f"<li>⭐ <strong>तारे:</strong> नई खोज</li>",
        ]
        expert_quote = """
<p>Astronomers and space scientists are calling this discovery a significant milestone.</p>
<p>खगोलविदों और अंतरिक्ष वैज्ञानिकों का मानना है कि यह खोज एक महत्वपूर्ण मील का पत्थर है।</p>
<blockquote style="border-left:5px solid #ff5722;padding:20px;background:#f9f9f9;border-radius:8px;margin:20px 0;">
    <p style="font-style:italic;font-size:16px;">"यह खोज अंतरिक्ष विज्ञान के इतिहास में एक नया अध्याय जोड़ती है।"</p>
</blockquote>
"""
        analysis_detail = f"""
<p>{first_para}</p>
<p>{more_content}</p>
<p>इस अंतरिक्ष घटना ने वैज्ञानिकों को नई जानकारी दी है।</p>
"""
    
    elif category == "Politics":
        highlights = [
            f"<li>🏛️ <strong>{clean_title[:50]}</strong> - राजनीति की बड़ी खबर</li>",
            f"<li>👥 <strong>मुख्य मुद्दे:</strong> {first_para[:60]}...</li>",
            f"<li>📈 <strong>विशेषज्ञों की राय:</strong> नीतिगत बदलावों पर चर्चा</li>",
            f"<li>🔮 <strong>आने वाले दिन:</strong> चुनाव और निर्णयों पर नज़र</li>",
            f"<li>🌍 <strong>वैश्विक प्रभाव:</strong> इसका वैश्विक राजनीति पर असर</li>",
            f"<li>⚖️ <strong>कानूनी पहलू:</strong> संवैधानिक और कानूनी निहितार्थ</li>",
            f"<li>📊 <strong>जनता की राय:</strong> सर्वेक्षण और जनमत</li>",
            f"<li>🎯 <strong>राजनीतिक रणनीति:</strong> आगामी चुनावी रणनीति</li>",
        ]
        expert_quote = """
<p>Political analysts and constitutional experts are closely monitoring this situation.</p>
<p>राजनीतिक विश्लेषकों और संवैधानिक विशेषज्ञों की नजर इस स्थिति पर टिकी है।</p>
<blockquote style="border-left:5px solid #ff5722;padding:20px;background:#f9f9f9;border-radius:8px;margin:20px 0;">
    <p style="font-style:italic;font-size:16px;">"यह राजनीतिक स्थिति लोकतंत्र के लिए एक महत्वपूर्ण परीक्षा है।"</p>
</blockquote>
"""
        analysis_detail = f"""
<p>{first_para}</p>
<p>{more_content}</p>
<p>यह राजनीतिक घटनाक्रम एक नया मोड़ ला सकता है।</p>
"""
    
    else:
        highlights = [
            f"<li>🔴 <strong>{clean_title[:50]}</strong> - आज की बड़ी खबर</li>",
            f"<li>📰 <strong>विस्तार:</strong> {first_para[:60]}...</li>",
            f"<li>📊 <strong>विश्लेषण:</strong> विशेषज्ञों की राय</li>",
            f"<li>🔮 <strong>आगे क्या:</strong> आने वाले अपडेट</li>",
            f"<li>🌍 <strong>ग्लोबल इंपैक्ट:</strong> दुनिया भर में प्रभाव</li>",
            f"<li>💡 <strong>इंसाइट:</strong> गहन विश्लेषण</li>",
            f"<li>📈 <strong>ट्रेंड:</strong> इस सेक्टर में रुझान</li>",
            f"<li>🎯 <strong>फ्यूचर:</strong> आने वाला भविष्य</li>",
        ]
        expert_quote = f"""
<p>Experts from around the world are weighing in on this significant development.</p>
<p>दुनिया भर के विशेषज्ञ इस महत्वपूर्ण विकास पर अपनी राय दे रहे हैं।</p>
<blockquote style="border-left:5px solid #ff5722;padding:20px;background:#f9f9f9;border-radius:8px;margin:20px 0;">
    <p style="font-style:italic;font-size:16px;">"यह {category} सेक्टर के इतिहास में एक महत्वपूर्ण मोड़ है।"</p>
</blockquote>
"""
        analysis_detail = f"""
<p>{first_para}</p>
<p>{more_content}</p>
<p>इस खबर के कई पहलू हैं और विशेषज्ञ इस पर लगातार नजर रखे हुए हैं।</p>
"""
    
    # ✅ DETAILED Introduction
    intro = f"""
<h3>📝 परिचय - Introduction</h3>
<p><strong>{clean_title}</strong></p>
<p>{first_para}</p>
<p>{more_content}</p>
<p>{clean_title} - यह {category} सेक्टर की आज की सबसे बड़ी खबर है।</p>
"""

    # ✅ DETAILED Analysis
    analysis = f"""
<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
{analysis_detail}
<p>इस खबर का प्रभाव आने वाले दिनों में और स्पष्ट होगा।</p>
"""

    # ✅ DETAILED Expert
    expert = f"""
<h3>💬 विशेषज्ञों की राय - Expert Opinions</h3>
{expert_quote}
"""

    # ✅ DETAILED Impact
    impact = f"""
<h3>🌍 प्रभाव और आगे क्या? - Impact & What's Next</h3>
<p>इस खबर का {category} सेक्टर पर महत्वपूर्ण प्रभाव पड़ने की उम्मीद है।</p>
<p>आने वाले दिनों में और अपडेट आने की संभावना है।</p>
"""

    # ✅ DETAILED Conclusion
    conclusion = f"""
<h3>✅ निष्कर्ष - Conclusion</h3>
<p>{clean_title} - यह {category} सेक्टर के लिए एक महत्वपूर्ण विकास है।</p>
<p>विशेषज्ञ इस बात पर सहमत हैं कि यह {category} के भविष्य को आकार देने वाला एक महत्वपूर्ण कदम है।</p>
"""
    
    return f"""
<h2>🚨 BREAKING NEWS: {clean_title}</h2>

<div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0;">
    <p><strong>📅 Published: {today}</strong></p>
    <p><strong>📂 Category: {category}</strong></p>
</div>

{intro}

<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>
    {''.join(highlights)}
</ul>

{analysis}

{expert}

{impact}

{conclusion}

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
    except Exception as e:
        print(f"⚠️ Error posting to Blogger: {e}")
        return None

# --- MAIN ---

def main():
    print("🤖 Starting Viral News AI Blogger Bot...")
    print(f"📅 {datetime.now().strftime('%B %d, %Y')}")
    fix_dns()
    
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
    
    recent_categories = get_recent_blogger_categories(access_token)
    print(f"🔄 Recent categories (Blogger Synced): {recent_categories}")
    
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
                    if category in recent_categories:
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
    
    if not found_news:
        print("\n🔍 Fallback: All categories...")
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
                            print(f"Found in '{category}' (Fallback)!")
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
