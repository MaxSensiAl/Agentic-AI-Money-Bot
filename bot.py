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
        res = requests.get("https://text.pollinations.ai", timeout=10)
        print(f"✅ Pollinations AI reachable (Status Code: {res.status_code})")
    except Exception as e:
        print(f"⚠️ Connection check failed: {e}")

# --- CONFIGURATION ---
BLOG_ID = os.getenv('BLOG_ID')
SHRINKME_API = os.getenv('SHRINKME_API')
BC_CLIENT_ID = os.getenv('BC_CLIENT_ID')
BC_CLIENT_SECRET = os.getenv('BC_CLIENT_SECRET')
BC_REFRESH_TOKEN = os.getenv('BC_REFRESH_TOKEN')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# --- INDIA-FOCUSED RSS FEEDS ---
RSS_FEEDS = [
    "https://feeds.feedburner.com/ndtvnews-top-stories",
    "https://feeds.feedburner.com/ndtvnews-india-news",
    "https://www.indiatoday.in/rss/india",
    "https://timesofindia.indiatimes.com/rssfeeds/296589184.cms",
    "https://www.thehindu.com/news/national/?service=rss",
    "https://www.hindustantimes.com/rss/india-news/rssfeed.xml",
    "https://www.news18.com/rss/india.xml",
    "https://www.business-standard.com/rss/current-affairs/india-news.rss",
    "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
    "https://sports.ndtv.com/rss/cricket-news",
    "https://www.livemint.com/rss/news",
    "https://economictimes.indiatimes.com/rssfeeds/13358356.cms",
    "https://www.pinkvilla.com/feed",
    "https://www.bollywoodhungama.com/feed/",
    "https://www.filmibeat.com/rss/bollywood.xml",
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.gadgets360.com/rss/news"
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

def ping_search_engines(blog_name, blog_url):
    print("🚀 SEO Pinging...")
    ping_services = [
        ("Google", "http://blogsearch.google.com/ping/RPC2"),
        ("Pingomatic", "http://rpc.pingomatic.com/"),
    ]
    for name, url in ping_services:
        try:
            server = xmlrpc.client.ServerProxy(url)
            server.weblogUpdates.ping(blog_name, blog_url)
            print(f"✅ Pinged {name}")
        except:
            print(f"⚠️ {name} ping failed")

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

def get_current_date():
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
            data = json.loads(response.text)
            return data.get("shortenedUrl", long_url)
        return response.text.strip() if response.text else long_url
    except:
        return long_url

def word_in_text(word, text):
    if not text:
        return False
    return bool(re.search(rf'\b{re.escape(word)}\b', text, re.IGNORECASE))

def detect_category(feed_url, title):
    feed_lower = feed_url.lower()
    title_lower = title.lower()
    
    def match_words(word_list):
        for word in word_list:
            if re.search(r'\b' + re.escape(word.lower()) + r'\b', title_lower):
                return True
        return False
    
    if any(x in feed_lower for x in ["ndtv", "indiatoday", "timesofindia", "thehindu", "hindustantimes", "news18"]):
        if match_words(["election", "modi", "parliament", "politics", "minister", "bjp", "congress"]):
            return "Politics"
        return "News"
    
    if "cric" in feed_lower or "sports" in feed_lower:
        return "Sports"
    if match_words(["cricket", "century", "wicket", "odi", "test", "ipl", "world cup", "kohli", "rohit"]):
        return "Sports"
    
    if any(x in feed_lower for x in ["pinkvilla", "bollywoodhungama", "filmibeat"]):
        return "Entertainment"
    if match_words(["movie", "film", "bollywood", "hollywood", "actor", "actress", "song", "singer", "celebrity", "kbc", "amitabh"]):
        return "Entertainment"
    
    if any(x in feed_lower for x in ["livemint", "economictimes"]):
        return "Business"
    if match_words(["stocks", "market", "economy", "finance", "nifty", "sensex"]):
        return "Business"
    
    if any(x in feed_lower for x in ["techcrunch", "theverge", "gadgets360"]):
        return "Technology"
    if match_words(["smartphone", "apple", "samsung", "software", "chatgpt", "iphone", "gadget", "ai"]):
        return "Technology"
    
    if any(x in feed_lower for x in ["gamespot", "ign"]):
        return "Gaming"
    if match_words(["nintendo", "xbox", "playstation", "ps5", "gta", "gaming"]):
        return "Gaming"
    
    if match_words(["car", "suv", "vehicle", "electric vehicle", "ev", "tesla", "toyota", "hyundai", "maruti", "tata"]):
        return "Automobile"
    
    if "space" in feed_lower or "nasa" in feed_lower:
        return "Space"
    if match_words(["isro", "nasa", "spacex", "satellite", "rocket", "chandrayaan", "moon", "mars"]):
        return "Space"

    if match_words(["music", "album", "song", "singer", "concert"]):
        return "Music"

    if "health" in feed_lower or "medical" in feed_lower:
        return "Health"
    if match_words(["health", "doctor", "cancer", "vaccine", "disease", "fitness"]):
        return "Health"
    
    return "News"

# --- FIXED: AI CALL COMPONENT (No more 404 Endpoint) ---
def call_ai_engine(prompt):
    """Multiple AI engines with fallback (Endpoint fixed to root)"""
    engines = [
        ("Pollinations Llama", "https://text.pollinations.ai", "llama"),
        ("Pollinations Mistral", "https://text.pollinations.ai", "mistral"),
    ]
    
    for engine_name, api_url, model in engines:
        try:
            print(f"🧠 Trying {engine_name} with model: {model}...")
            payload = {
                "messages": [
                    {"role": "system", "content": "You are a professional Hindi/English news journalist and SEO editor. Write high-quality, extremely detailed news reports in Hinglish/Hindi."},
                    {"role": "user", "content": prompt}
                ],
                "model": model,
                "stream": False
            }
            res = requests.post(api_url, json=payload, timeout=60)
            if res.status_code == 200:
                # Failsafe parsing for both raw text and JSON response formats
                try:
                    data = res.json()
                    if isinstance(data, dict) and "choices" in data:
                        clean_text = data["choices"][0]["message"]["content"].strip()
                    elif isinstance(data, dict) and "response" in data:
                        clean_text = data["response"].strip()
                    else:
                        clean_text = res.text.strip()
                except ValueError:
                    clean_text = res.text.strip()

                clean_text = clean_text.replace("```html", "").replace("```", "").strip()
                if len(clean_text) > 300:
                    print(f"✅ {engine_name} success! (Length: {len(clean_text)} characters)")
                    return clean_text
            else:
                print(f"⚠️ {engine_name} Status: {res.status_code}")
        except Exception as e:
            print(f"⚠️ {engine_name} Error: {e}")
        time.sleep(2)
    return None

# --- JOURNALISTIC CONTENT GENERATOR (Dynamic Headings, USA Fiesta Style) ---
def generate_super_detailed_content(title, full_content, category):
    """Generate high-quality journalistic article with dynamic story-specific headings"""
    print("🤖 Generating professional, dynamic article (USA Fiesta style)...")
    
    prompt = f"""Based on this news source:
Title: {title}
Content: {full_content[:3000]}
Category: {category}

Write a comprehensive, professional news article in Hinglish (Hindi + English blend, natural flowing tone). 
Follow these STRICT journalistic guidelines to make it look like a high-end news portal:

1. Do NOT use boring, generic headings like 'Introduction', 'Key Highlights', 'Detailed Analysis', 'Expert Opinions', or 'Conclusion'.
2. Instead, create 4 to 5 STORY-SPECIFIC, DYNAMIC subheadings in Hindi (for example, if the news is about a movie, use headings like 'अक्षय कुमार का अनोखा अवतार', 'टीज़र में क्या है खास', 'दर्शकों में बढ़ा उत्साह').
3. The content must flow naturally. Start with a strong lead paragraph (no heading for the very first paragraph).
4. Do NOT repeat paragraphs or facts. Keep the word count rich and informative (at least 1500+ words of unique text).
5. At the beginning of your response, write a viral, catchy Hinglish/Hindi title wrapped in [TITLE] and [/TITLE] tags.

Format the HTML structure exactly as follows:
[TITLE] Catchy Hindi/Hinglish Title [/TITLE]

<p>Lead paragraph here (Introduction without heading, explaining What, Who, Where, When)...</p>

<h3>🎯 मुख्य बिंदु (Key Takeaways)</h3>
<ul>
  <li>Highlight point 1...</li>
  <li>Highlight point 2...</li>
  <li>Highlight point 3...</li>
  <li>Highlight point 4...</li>
</ul>

<h3>[Story-Specific Subheading 1 in Hindi]</h3>
<p>Detailed paragraphs...</p>

<h3>[Story-Specific Subheading 2 in Hindi]</h3>
<p>Detailed paragraphs...</p>

<h3>[Story-Specific Subheading 3 in Hindi]</h3>
<p>Detailed paragraphs...</p>

<h3>[Story-Specific Subheading 4 in Hindi]</h3>
<p>Detailed paragraphs...</p>

<h3>✅ निष्कर्ष और प्रभाव (Outlook)</h3>
<p>Concluding paragraphs reflecting on the future impact...</p>
"""
    result = call_ai_engine(prompt)
    if not result or len(result) < 300:
        return None
        
    viral_title = title
    title_match = re.search(r'\[TITLE\](.*?)\[/TITLE\]', result, re.IGNORECASE | re.DOTALL)
    if title_match:
        viral_title = title_match.group(1).strip()
        result = result.replace(title_match.group(0), "")
        
    return viral_title, result

# --- DETAILED FALLBACK CONTENT (NO REPETITION / DUPLICATION) ---
def get_detailed_fallback_content(title, full_content, category):
    """Generate detailed fallback content without duplicate paragraphs"""
    print("🔄 Using smart detailed fallback template...")
    today = get_current_date()
    clean_title = clean_and_format_title(title)
    
    # Split content into unique paragraphs to prevent duplication
    paragraphs = [p.strip() for p in re.split(r'\n+', full_content) if p.strip()]
    
    p1 = paragraphs[0] if len(paragraphs) > 0 else "ताजा रिपोर्ट के अनुसार, इस विषय पर देश भर में चर्चा हो रही है।"
    p2 = paragraphs[1] if len(paragraphs) > 1 else "इस घटनाक्रम के कई महत्वपूर्ण पहलू हैं जिन पर विशेषज्ञ लगातार अपनी नजर बनाए हुए हैं।"
    p3 = paragraphs[2] if len(paragraphs) > 2 else "सोशल मीडिया पर भी इस खबर को लेकर लोग अपनी प्रतिक्रियाएं दे रहे हैं और चर्चा का बाजार गर्म है।"
    p4 = paragraphs[3:] if len(paragraphs) > 3 else []
    p4_text = " ".join(p4)[:1000] if p4 else "आने वाले दिनों में इस मामले में नए खुलासे होने की उम्मीद है।"

    # Category-specific custom headings
    if category == "Entertainment":
        h1, h2, h3 = "शुरुआती जानकारी और बैकग्राउंड", "कलाकारों और इंडस्ट्री पर असर", "फैंस की प्रतिक्रिया और भविष्य"
    elif category == "Sports":
        h1, h2, h3 = "मैच और खेल का विवरण", "खिलाड़ियों का प्रदर्शन और आंकड़े", "टीम की आगे की रणनीति"
    elif category == "Business":
        h1, h2, h3 = "मार्केट और शेयर बाजार पर असर", "निवेशकों के लिए मुख्य बातें", "आर्थिक विश्लेषकों का नजरिया"
    elif category == "Technology":
        h1, h2, h3 = "नये फीचर्स और तकनीक", "यूज़र्स के लिए इसके मायने", "टेक जगत में इसका प्रभाव"
    else:
        h1, h2, h3 = "मामले का पूरा विवरण", "मुख्य घटनाक्रम और विश्लेषण", "जनता की राय और प्रभाव"

    highlights = [
        f"<li>📌 <strong>{clean_title[:60]}</strong> - आज की मुख्य सुर्खी</li>",
        f"<li>⚡ <strong>अपडेट:</strong> {p1[:80]}...</li>",
        f"<li>🔍 <strong>विशेष विश्लेषण:</strong> {p2[:80]}...</li>",
        f"<li>📈 <strong>ट्रेंडिंग टॉपिक:</strong> सोशल मीडिया पर लगातार चर्चा</li>"
    ]

    return f"""
<h2>🚨 BREAKING NEWS: {clean_title}</h2>

<div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0;">
    <p><strong>📅 Published: {today}</strong></p>
    <p><strong>📂 Category: {category}</strong></p>
</div>

<h3>📝 परिचय - Introduction</h3>
<p>{p1}</p>

<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>
    {''.join(highlights)}
</ul>

<h3>📊 {h1}</h3>
<p>{p2}</p>

<h3>💬 {h2}</h3>
<p>{p3}</p>

<h3>🌍 {h3}</h3>
<p>{p4_text}</p>

<h3>✅ निष्कर्ष - Conclusion</h3>
<p>इस पूरे घटनाक्रम पर हमारी टीम लगातार नजर बनाए हुए है। जैसे ही कोई नया अपडेट आएगा, हम आपके साथ साझा करेंगे। तब तक बने रहिए हमारे साथ।</p>

<p><em>Disclaimer: This is an AI-generated news summary. For complete details, please refer to the original source.</em></p>
"""

def post_to_blogger(access_token, title, content, category):
    try:
        post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        post_body = {
            "kind": "blogger#post",
            "title": title,
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
    print("🤖 Starting Viral News AI Blogger Bot (Super Detailed)...")
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
    link = entry.link
    full_content = get_full_content(entry)
    category = detect_category(selected_feed, raw_title)
    
    print(f"\n📰 Title: {raw_title}")
    print(f"📂 Category: {category}")
    print(f"🖼️ Image: ✅ HD Quality")
    
    print("🤖 Generating super detailed content...")
    ai_result = generate_super_detailed_content(raw_title, full_content, category)
    
    if ai_result:
        viral_title, ai_content = ai_result
        print(f"🔥 Viral Title: {viral_title}")
    else:
        print("⚠️ AI failed, using detailed fallback...")
        viral_title = raw_title
        ai_content = get_detailed_fallback_content(raw_title, full_content, category)
        
    image_html = f"""
    <div style="text-align:center;margin-bottom:25px;">
        <img src='{image_url}' alt='{viral_title}' style='width:100%;max-width:800px;height:auto;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.15);'>
        <p style="font-size:12px;color:#999;margin-top:5px;">📸 Viral News AI | HD Quality</p>
    </div>
    """
    
    short_link = get_short_url(link)
    print(f"🔗 Short Link: {short_link}")
    
    earning_button = f"""
    <div style="text-align:center;margin:30px 0;padding:20px;background:#f5f5f5;border-radius:12px;">
        <a href="{short_link}" target="_blank" style="background:linear-gradient(135deg,#ff5722,#ff6f00);color:white;padding:20px 60px;text-decoration:none;font-size:22px;font-weight:bold;border-radius:50px;display:inline-block;text-transform:uppercase;box-shadow:0 4px 15px rgba(255,87,34,0.3);">
            📖 पूरी खबर पढ़ें - READ FULL STORY
        </a>
        <p style="font-size:12px;color:#999;margin-top:10px;">Click to read the complete story on the original source</p>
    </div>
    """
    
    approx_words = len(ai_content.split())
    
    final_content = f"""
    {image_html}
    {ai_content}
    {earning_button}
    
    <hr style="border:0;border-top:2px solid #e0e0e0;margin:30px 0;">
    
    <div style="text-align:center;color:#999;font-size:14px;">
        <p>📅 Published: {get_current_date()}</p>
        <p>📂 Category: {category}</p>
        <p>📝 Word Count: {approx_words}+ words</p>
        <p>🌐 Language: Hinglish (Hindi + English)</p>
        <p>🖼️ Image: HD Quality</p>
        <p>🤖 AI-Generated News Summary</p>
        <p>© Viral News AI - All Rights Reserved</p>
        <p>⚠️ Disclaimer: This is an AI-generated summary. Please refer to the original source.</p>
    </div>
    """
    
    print(f"\n📝 Posting to Blogger...")
    post_url = post_to_blogger(access_token, viral_title, final_content, category)
    
    if post_url:
        save_posted_news(viral_title)
        print("\n✅✅✅ POSTED SUCCESSFULLY! ✅✅✅")
        print(f"🔗 {post_url}")
        ping_search_engines("Viral News AI", post_url)
        share_to_telegram(viral_title, post_url)
        share_to_discord(viral_title, post_url)
        print(f"\n📰 {viral_title}")
        print(f"📂 {category}")
        print(f"📝 {approx_words}+ words")
        print(f"🔗 {short_link}")
    else:
        print("❌ Failed to post!")

if __name__ == "__main__":
    main()
