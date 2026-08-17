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

# --- SMART TCP REDIRECT PATCH (Google और अन्य Pings के लिए सुरक्षित) ---
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

# पैच को लागू करें
apply_smart_connection_patch()

def fix_dns():
    print("✅ Testing connection to Pollinations AI...")
    try:
        res = requests.get("https://text.pollinations.ai", timeout=10)
        print(f"✅ Pollinations AI reachable (Status Code: {res.status_code})")
    except Exception as e:
        print(f"⚠️ Connection check failed: {e}")

# --- CONFIGURATION ---
BLOG_ID = os.getenv('BLOG_ID')
SHRINKME_API = os.getenv('SHRINKME_API')
GEMINI_API = os.getenv('GEMINI_API')  # यदि गिटहब .yml में मैप है तो उपयोग होगा
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

# गिटहब सर्वर के यूटीसी समय को भारतीय समय (IST) के अनुसार सिंक करने का फंक्शन
def get_current_date():
    """Get current date in Indian Standard Time (IST) format"""
    ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
    return ist_time.strftime("%B %d, %Y")

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
        if response.text and "shortenedUrl" in response.text:
            import json
            data = json.loads(response.text)
            return data.get("shortenedUrl", long_url)
        return response.text.strip() if response.text else long_url
    except:
        return long_url

# Word Boundary Function
def word_in_text(word, text):
    """Check if whole word exists in text (not as substring)"""
    if not text:
        return False
    return bool(re.search(rf'\b{re.escape(word)}\b', text, re.IGNORECASE))

# Category Detection with Whole-Word Matching (Strict Keywords)
def detect_category(feed_url, title):
    feed_lower = feed_url.lower()
    title_lower = title.lower()
    
    # कोडिंग टकराव (Collisions) रोकने के लिए हेल्पर फंक्शन
    def match_words(word_list):
        for word in word_list:
            if re.search(r'\b' + re.escape(word.lower()) + r'\b', title_lower):
                return True
        return False

    # Entertainment (मनोरंजन)
    if any(x in feed_lower for x in ["variety", "hollywood", "pinkvilla", "eonline"]):
        return "Entertainment"
    if match_words(["movie", "film", "hollywood", "box office", "marvel", "dc", "disney", "lands", "rides", "spider-man", "spiderman", "actor", "actress", "celebrity", "drama"]):
        return "Entertainment"
    if match_words(["star cast", "pop star", "rock star"]):
        return "Entertainment"
    
    # Space (अंतरिक्ष) - 'star' शब्द को यहाँ से हटा दिया गया है ताकि "Pop Star" जैसी खबरें स्पेस में न जाएं।
    if "space" in feed_lower or "nasa" in feed_lower:
        return "Space"
    if match_words(["galaxy", "planet", "moon", "mars", "universe", "cosmos", "astronaut", "asteroid", "telescope", "eclipse", "stargazing", "constellation", "nebula"]):
        return "Space"
        
    # Technology (तकनीक)
    if any(x in feed_lower for x in ["tech", "verge", "cnet", "techcrunch"]):
        return "Technology"
    if match_words(["smartphone", "apple", "samsung", "software", "artificial intelligence", "chatgpt", "iphone", "gadget", "cybersecurity", "hacker", "app", "spyware"]):
        return "Technology"
    # "AI" को स्वतंत्र शब्द के रूप में मैच करें
    if re.search(r'\b' + "ai" + r'\b', title_lower):
        return "Technology"
        
    # Gaming (गेमिंग)
    if "gaming" in feed_lower or any(x in feed_lower for x in ["gamespot", "ign"]):
        return "Gaming"
    if match_words(["nintendo", "xbox", "playstation", "ps5", "gta", "gamer", "gaming", "gameplay", "console"]):
        return "Gaming"
        
    # Music (संगीत)
    if any(x in feed_lower for x in ["rollingstone"]):
        return "Music"
    if match_words(["album", "song", "singer", "concert", "tour", "music", "guitar", "pop", "rap", "band", "singing", "cynthia", "ariana", "mcconaughey"]):
        return "Music"
        
    # Sports (खेल) - 'test' की जगह 'test cricket', 'test match' किया गया है।
    if "cric" in feed_lower:
        return "Sports"
    if match_words(["cricket", "century", "wicket", "odi", "test cricket", "test match", "test series", "football", "goal", "fifa", "olympics", "athletics", "basketball", "tennis", "stadium", "sciver", "brunt", "england"]):
        return "Sports"
        
    # Business (व्यापार)
    if any(x in feed_lower for x in ["bloomberg", "reuters", "markets"]):
        return "Business"
    if match_words(["stocks", "inflation", "market", "economy", "trade", "finance", "investing", "crypto", "bitcoin"]):
        return "Business"
        
    # Politics (राजनीति)
    if "politics" in feed_lower:
        return "Politics"
    if match_words(["election", "biden", "trump", "modi", "parliament", "politics", "minister", "senate", "congress", "government", "vote", "bjp", "amit malviya", "deepak mhaske"]):
        return "Politics"
        
    # Health (स्वास्थ्य)
    if "health" in feed_lower or "medical" in feed_lower:
        return "Health"
    if match_words(["health", "mental", "doctor", "cancer", "vaccine", "disease", "fitness", "nutrition", "diet"]):
        return "Health"
        
    # Automobile (ऑटोमोबाइल)
    if "motor" in feed_lower or "auto" in feed_lower:
        return "Automobile"
    if match_words(["car", "suv", "vehicle", "electric vehicle", "ev", "tesla", "engine", "motorcycle", "bike", "polestar", "volvo", "ferrari", "porsche", "ford", "bmw", "audi"]):
        return "Automobile"
        
    return "News"

# ✅ DUAL ENGINE: Google Gemini (Primary) & Pollinations AI (Backup Fallback)
def ask_ai_for_news(title, full_content, category):
    """Google Gemini (प्राथमिक) से कनेक्ट करेगा, यदि उपलब्ध न हो तो स्वतः Pollinations AI (बैकअप) पर चला जाएगा"""
    
    # 🌟 ENGINE 1: Google Gemini API (सबसे बेस्ट और बिल्कुल अनब्लॉक)
    if GEMINI_API:
        print("🧠 Engine 1: Calling Google Gemini 1.5 Flash...")
        try:
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API}"
            headers = {"Content-Type": "application/json"}
            
            prompt = f"""You are a professional News Journalist writing in Hinglish (Hindi + English).
Write a highly engaging, SEO-friendly news article based on this news:
Title: {title}
Content: {full_content[:1500]}
Category: {category}

Strict Instructions:
1. Write in natural Hinglish (blend of Hindi and English).
2. Do not use generic placeholder sentences. Use actual names, facts, and details from the provided news.
3. Generate a realistic and highly specific expert opinion quote about this exact event.
4. Output the content using this exact HTML structure with EXTREMELY DETAILED paragraphs (minimum 200-300 words per section):

<h3>📝 परिचय - Introduction</h3>
<p>[EXTREMELY DETAILED introduction in English - minimum 200 words based on the news content]</p>
<p>[EXTREMELY DETAILED introduction in Hindi - minimum 200 words based on the news content]</p>

<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>
  <li>[Specific highlight 1 containing real facts/names/scores from the news]</li>
  <li>[Specific highlight 2 containing real facts/names from the news]</li>
  <li>[Specific highlight 3 containing real facts/names from the news]</li>
  <li>[Specific highlight 4 containing real facts/names from the news]</li>
  <li>[Specific highlight 5 containing real facts/names from the news]</li>
  <li>[Specific highlight 6 containing real facts/names from the news]</li>
  <li>[Specific highlight 7 containing real facts/names from the news]</li>
  <li>[Specific highlight 8 containing real facts/names from the news]</li>
</ul>

<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
<p>[EXTREMELY DETAILED analysis paragraph in English - minimum 250 words]</p>
<p>[EXTREMELY DETAILED analysis paragraph in Hindi - minimum 250 words]</p>

<h3>💬 विशेषज्ञों की राय - Expert Opinions</h3>
<p>[EXTREMELY DETAILED expert opinion in English - minimum 150 words]</p>
<p>[EXTREMELY DETAILED expert opinion in Hindi - minimum 150 words]</p>
<blockquote style="border-left:5px solid #ff5722;padding:20px;background:#f9f9f9;border-radius:8px;margin:20px 0;">
    <p style="font-style:italic;font-size:16px;">"[A realistic, highly specific expert quote in Hindi about this event]"</p>
</blockquote>

<h3>🌍 प्रभाव और आगे क्या? - Impact & What's Next</h3>
<p>[EXTREMELY DETAILED impact analysis in English - minimum 200 words]</p>
<p>[EXTREMELY DETAILED impact analysis in Hindi - minimum 200 words]</p>

<h3>✅ निष्कर्ष - Conclusion</h3>
<p>[EXTREMELY DETAILED conclusion in English - minimum 150 words]</p>
<p>[EXTREMELY DETAILED conclusion in Hindi - minimum 150 words]</p>
"""
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7}
            }
            res = requests.post(api_url, json=payload, headers=headers, timeout=50)
            if res.status_code == 200:
                data = res.json()
                clean_html = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                clean_html = clean_html.replace("```html", "").replace("```", "").strip()
                if "<h3>" in clean_html:
                    print("✅ Engine 1 (Gemini) successfully generated content!")
                    return clean_html
            print(f"⚠️ Engine 1 (Gemini) returned status {res.status_code}, switching to Engine 2...")
        except Exception as e:
            print(f"⚠️ Engine 1 (Gemini) Error: {e}, switching to Engine 2...")

    # 🌟 ENGINE 2: Pollinations AI (मुफ़्त बैकअप - 100% अनब्लॉक और टोकन-फ्री)
    print("🧠 Engine 2: Calling Pollinations AI (Backup)...")
    try:
        api_url = "https://text.pollinations.ai"  # No trailing slash (404 fixed)
        model = "llama"  # Llama-3-70B (स्टेबल और फ्री)
        
        prompt = f"""You are a professional News Journalist writing in Hinglish (Hindi + English).
Write a highly engaging news article based on this news:
Title: {title}
Content: {full_content[:1500]}
Category: {category}

Strict Instructions:
1. Write in Hinglish.
2. Output strictly using this HTML structure:
<h3>📝 परिचय - Introduction</h3>
<p>[Detailed English intro]</p>
<p>[Detailed Hindi intro]</p>
<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>
  <li>• [Fact 1]</li>
  <li>• [Fact 2]</li>
  <li>• [Fact 3]</li>
  <li>• [Fact 4]</li>
</ul>
<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
<p>[Detailed analysis]</p>
<h3>💬 विशेषज्ञों की राय - Expert Opinions</h3>
<p>[Expert opinion]</p>
<blockquote>"[Quote]"</blockquote>
<h3>🌍 प्रभाव और आगे क्या? - Impact & What's Next</h3>
<p>[Impact]</p>
<h3>✅ निष्कर्ष - Conclusion</h3>
<p>[Conclusion]</p>
"""
        payload = {
            "messages": [
                {"role": "system", "content": "You are a professional news editor writing HTML output in Hinglish."},
                {"role": "user", "content": prompt}
            ],
            "model": model
        }
        res = requests.post(api_url, json=payload, timeout=60)
        if res.status_code == 200:
            clean_html = res.text.strip()
            if "<h3>" in clean_html:
                print("✅ Engine 2 (Pollinations) successfully generated content!")
                return clean_html
        print(f"⚠️ Engine 2 (Pollinations) Status: {res.status_code}")
    except Exception as e:
        print(f"⚠️ Engine 2 Error: {e}")
        
    return None

# ✅ DYNAMIC CONTENT GENERATOR WITH DETAILED SECTIONS
def generate_dynamic_content(title, full_content, category):
    """AI से Content Generate करे, नहीं तो DETAILED Fallback Template"""
    
    # पहले AI try करो (Gemini या Pollinations)
    ai_content = ask_ai_for_news(title, full_content, category)
    if ai_content:
        return ai_content
    
    # AI fail हो तो DETAILED Fallback Template
    print("🔄 Using detailed fallback template...")
    today = get_current_date()
    clean_title = clean_and_format_title(title)
    first_para = full_content[:500] if full_content else ""
    more_content = full_content[500:1000] if len(full_content) > 500 else ""
    
    # Category-wise DETAILED Highlights (8 points)
    if category == "Technology":
        highlights = [
            f"<li>💻 <strong>{clean_title[:50]}</strong> - टेक जगत में बड़ी खबर</li>",
            f"<li>📱 <strong>डिटेल्स:</strong> {first_para[:60]}...</li>",
            f"<li>🔍 <strong>एनालिसिस:</strong> विशेषज्ञों की राय</li>",
            f"<li>💡 <strong>इंपैक्ट:</strong> इसका क्या प्रभाव होगा</li>",
            f"<li>🚀 <strong>फ्यूचर:</strong> आगे क्या होगा</li>",
            f"<li>🛡️ <strong>सुरक्षा:</strong> स्पाइवेयर से बचाव के उपाय</li>",
            f"<li>📊 <strong>आंकड़े:</strong> असामान्य रूप से अधिक यूज़र्स</li>",
            f"<li>🎯 <strong>निष्कर्ष:</strong> यह एक गंभीर मामला है</li>",
        ]
        expert_quote = """
<p>Tech reviewers and industry analysts are impressed by this new technological development. They believe that this issue represents a serious threat to user privacy.</p>
<p>टेक समीक्षकों और उद्योग विश्लेषकों का मानना है कि यह तकनीकी विकास इस क्षेत्र में नए आयाम स्थापित करेगा। उनका मानना है कि यह मुद्दा यूज़र्स की निजता के लिए एक गंभीर खतरा है।</p>
<blockquote style="border-left:5px solid #ff5722;padding:20px;background:#f9f9f9;border-radius:8px;margin:20px 0;">
    <p style="font-style:italic;font-size:16px;">"सुरक्षा और निजता अब तकनीक उद्योग में सबसे बड़े महत्वपूर्ण मानक बन चुके हैं।"</p>
</blockquote>
"""
        analysis_detail = f"""
<p>{first_para}</p>
<p>{more_content}</p>
<p>इस तकनीकी घटनाक्रम ने विशेषज्ञों को नई चिंता दी है और आने वाले सुरक्षा अपडेट्स के लिए नए रास्ते खोले हैं।</p>
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
<p>Political analysts and constitutional experts are closely monitoring this situation. The outcome could have far-reaching implications for the political landscape.</p>
<p>राजनीतिक विश्लेषकों और संवैधानिक विशेषज्ञों की नजर इस स्थिति पर टिकी है। इसके परिणाम राजनीतिक प्रणाली के लिए दूरगामी प्रभाव डाल सकते हैं।</p>
<blockquote style="border-left:5px solid #ff5722;padding:20px;background:#f9f9f9;border-radius:8px;margin:20px 0;">
    <p style="font-style:italic;font-size:16px;">"यह राजनीतिक स्थिति लोकतंत्र और शासन के लिए एक महत्वपूर्ण परीक्षा है।"</p>
</blockquote>
"""
        analysis_detail = f"""
<p>{first_para}</p>
<p>{more_content}</p>
<p>यह राजनीतिक घटनाक्रम राजनीति में एक नया मोड़ ला सकता है। विशेषज्ञों का मानना है कि इसका प्रभाव नीतियों पर पड़ेगा।</p>
"""
    
    elif category == "Sports":
        highlights = [
            f"<li>🏏 <strong>{clean_title[:50]}</strong> - मैच का सबसे बड़ा मोमेंट</li>",
            f"<li>⭐ <strong>स्टार प्रदर्शन:</strong> {first_para[:60]}...</li>",
            f"<li>📊 <strong>मैच विश्लेषण:</strong> टीम ने शानदार प्रदर्शन किया</li>",
            f"<li>🏆 <strong>ऐतिहासिक जीत:</strong> यह टीम के लिए एक बड़ी उपलब्धि है</li>",
            f"<li>⚡ <strong>अहम मोमेंट्स:</strong> {more_content[:60]}...</li>",
            f"<li>📈 <strong>आंकड़े:</strong> खिलाड़ियों के शानदार आंकड़े</li>",
            f"<li>🎯 <strong>रणनीति:</strong> टीम की बेहतरीन रणनीति</li>",
            f"<li>🏅 <strong>खिलाड़ी:</strong> स्टार खिलाड़ियों का योगदान</li>",
        ]
        expert_quote = """
<p>Cricket pundits and former players are praising this performance as one of the best in recent times. According to experts, this victory will boost the team's confidence for upcoming tournaments.</p>
<p>क्रिकेट विश्लेषकों और पूर्व खिलाड़ियों का मानना है कि यह हाल के समय के सबसे शानदार प्रदर्शनों में से एक है। विशेषज्ञों के अनुसार, यह जीत आगामी टूर्नामेंट्स के लिए टीम का आत्मविश्वास बढ़ाएगी।</p>
<blockquote style="border-left:5px solid #ff5722;padding:20px;background:#f9f9f9;border-radius:8px;margin:20px 0;">
    <p style="font-style:italic;font-size:16px;">"यह प्रदर्शन दिखाता है कि यह टीम किसी भी चुनौती का सामना करने के लिए तैयार है।"</p>
</blockquote>
"""
        analysis_detail = f"""
<p>{first_para}</p>
<p>{more_content}</p>
<p>इस मैच में खिलाड़ियों ने जिस तरह का संयम और आक्रामकता दिखाया, वह काबिल-ए-तारीफ है। टीम ने हर विभाग में बेहतरीन प्रदर्शन किया और जीत अपने नाम की।</p>
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
<p>Experts from around the world are weighing in on this significant development. This event is expected to reshape the future of the {category} sector.</p>
<p>दुनिया भर के विशेषज्ञ इस महत्वपूर्ण विकास पर अपनी राय दे रहे हैं। इस घटना से {category} सेक्टर का भविष्य बदलने की उम्मीद है।</p>
<blockquote style="border-left:5px solid #ff5722;padding:20px;background:#f9f9f9;border-radius:8px;margin:20px 0;">
    <p style="font-style:italic;font-size:16px;">"यह {category} सेक्टर के इतिहास में एक महत्वपूर्ण मोड़ है।"</p>
</blockquote>
"""
        analysis_detail = f"""
<p>{first_para}</p>
<p>{more_content}</p>
<p>इस खबर के कई पहलू हैं और विशेषज्ञ इस पर लगातार नजर रखे हुए हैं। यह {category} सेक्टर के लिए एक बड़ा बदलाव ला सकता है।</p>
"""
    
    # DETAILED Introduction
    intro = f"""
<h3>📝 परिचय - Introduction</h3>
<p><strong>{clean_title}</strong></p>
<p>{first_para}</p>
<p>{more_content}</p>
<p>{clean_title} - यह {category} सेक्टर की आज की सबसे बड़ी खबर है। यह घटना पूरे उद्योग में चर्चा का विषय बनी हुई है। विशेषज्ञ इस विकास पर लगातार नजर रखे हुए हैं।</p>
"""

    # DETAILED Analysis
    analysis = f"""
<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
{analysis_detail}
<p>इस खबर का प्रभाव आने वाले दिनों में और स्पष्ट होगा। जो लोग इस सेक्टर से जुड़े हैं, उनके लिए यह एक महत्वपूर्ण समय है। विशेषज्ञों का मानना है कि इस {category} सेक्टर के लिए एक महत्वपूर्ण मोड़ है।</p>
"""

    # DETAILED Expert
    expert = f"""
<h3>💬 विशेषज्ञों की राय - Expert Opinions</h3>
{expert_quote}
"""

    # DETAILED Impact
    impact = f"""
<h3>🌍 प्रभाव और आगे क्या? - Impact & What's Next</h3>
<p>इस खबर का {category}  सेक्टर पर महत्वपूर्ण प्रभाव पड़ने की उम्मीद है। आने वाले दिनों में और अपडेट आने की संभावना है।</p>
"""

    # DETAILED Conclusion
    conclusion = f"""
<h3>✅ निष्कर्ष - Conclusion</h3>
<p>{clean_title} - यह {category}  सेक्टर के लिए एक महत्वपूर्ण विकास है।</p>
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
    print(f"📅 {get_current_date()}")
    fix_dns()
    
    print("\n--- Checking Secrets ---")
    secrets = {
        "BLOG_ID": BLOG_ID,
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
    
    # GEMINI_API को अनिवार्य (Mandatory) चेक से हटा दिया गया है
    print(f"GEMINI_API: {'✅ LOADED (Using Google Gemini as Primary AI Engine)' if GEMINI_API else '⚠️ NOT MAPPED (Using Pollinations AI as Backup AI Engine)'}")
    
    if not all_loaded:
        print("\n❌ Mandatory Secrets missing!")
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
    
    # Generate DYNAMIC content
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
        <p>📅 Published: {get_current_date()}</p>
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
