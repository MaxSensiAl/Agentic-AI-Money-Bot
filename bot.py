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
from google import genai
from google.genai import types
from urllib.parse import quote

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================
# 🔧 SMART TCP REDIRECT PATCH
# ============================================
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
            print(f"🎯 Redirecting {host} connection to {ip}")
            return original_create_connection((ip, port), *args, **kwargs)
        return original_create_connection(address, *args, **kwargs)

    urllib3_connection.create_connection = patched_create_connection
    print("✅ Smart TCP Patch applied")

apply_smart_connection_patch()

# ============================================
# 🔐 CONFIGURATION & SECRETS
# ============================================
BLOG_ID = os.getenv('BLOG_ID')
SHRINKME_API = os.getenv('SHRINKME_API')
BC_CLIENT_ID = os.getenv('BC_CLIENT_ID')
BC_CLIENT_SECRET = os.getenv('BC_CLIENT_SECRET')
BC_REFRESH_TOKEN = os.getenv('BC_REFRESH_TOKEN')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GEMINI_API')

# --- INDIA-FOCUSED RSS FEEDS ---
RSS_FEEDS = [
    "https://usafiesta.com/feed/",
    "https://feeds.feedburner.com/ndtvnews-top-stories",
    "https://feeds.feedburner.com/ndtvnews-india-news",
    "https://www.indiatoday.in/rss/india",
    "https://timesofindia.indiatimes.com/rssfeeds/296589184.cms",
    "https://www.thehindu.com/news/national/?service=rss",
    "https://www.hindustantimes.com/rss/india-news/rssfeed.xml",
    "https://www.news18.com/rss/india.xml",
    "https://www.business-standard.com/rss/current-affairs/india-news.rss",
    "https://www.livemint.com/rss/news",
    "https://economictimes.indiatimes.com/rssfeeds/13358356.cms"
]

# --- IMAGE SOURCES ---
UNSPLASH_IMAGES = {
    "Technology": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
    "Gaming": "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80",
    "Entertainment": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80",
    "Space": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
    "Sports": "https://images.unsplash.com/photo-1531415074968-036ba1b575da?auto=format&fit=crop&w=1200&q=80",
    "Business": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80",
    "Politics": "https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?auto=format&fit=crop&w=1200&q=80",
    "Health": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=1200&q=80",
    "Automobile": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1200&q=80",
}

POSTED_FILE = 'posted_news.txt'

# ============================================
# 🛠️ HELPER FUNCTIONS
# ============================================
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

# ============================================
# 🔥🔥🔥 SMART IMAGE MATCHING SYSTEM 🔥🔥🔥
# ============================================

def is_valid_image_url(url):
    """Check if image URL is valid and accessible"""
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=5)
        if res.status_code == 200:
            content_type = res.headers.get("Content-Type", "")
            if "image" in content_type:
                content_length = int(res.headers.get("Content-Length", 0))
                if content_length > 5000:  # Minimum 5KB - valid image
                    return True
    except:
        pass
    return False

def get_google_images(query):
    """Search Google Images for matching photos"""
    print(f"🔍 Google Images par search kar raha hai: {query[:50]}...")
    try:
        # Google Images search URL
        search_url = "https://www.google.com/search"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        params = {
            "q": query,
            "tbm": "isch",
            "tbs": "isz:l"  # Large images only
        }
        
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        
        # Extract image URLs using regex
        image_urls = re.findall(r'https?://[^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*', response.text)
        
        # Filter and validate
        valid_images = []
        for url in image_urls:
            if url and url.startswith('http'):
                # Skip small/logo images
                if not any(x in url.lower() for x in ['logo', 'icon', 'avatar', 'placeholder', 'gif', 'profile', '1x1', 'pixel']):
                    # Add to list (limit to 5)
                    if len(valid_images) < 5:
                        valid_images.append(url)
        
        # Validate each image
        for img_url in valid_images:
            if is_valid_image_url(img_url):
                print(f"✅ Google Images se matching photo mil gayi!")
                return img_url
                
    except Exception as e:
        print(f"⚠️ Google Images search error: {e}")
    return None

def get_duckduckgo_images(query):
    """Search DuckDuckGo Images for matching photos"""
    print(f"🔍 DuckDuckGo Images par search kar raha hai: {query[:50]}...")
    try:
        # Get VQD token first
        search_url = "https://duckduckgo.com/"
        headers = {"User-Agent": "Mozilla/5.0"}
        params = {"q": query}
        res = requests.get(search_url, params=params, headers=headers, timeout=10)
        
        vqd_match = re.search(r'vqd=([\d-]+)\&', res.text)
        if not vqd_match:
            vqd_match = re.search(r'vqd=["\']([\d-]+)["\']', res.text)
            
        if vqd_match:
            vqd = vqd_match.group(1)
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://duckduckgo.com/"
            }
            params = {
                "l": "wt-wt",
                "o": "json",
                "q": query,
                "vqd": vqd,
                "f": ",,,,",
                "p": "1"
            }
            image_api_url = "https://duckduckgo.com/v.html"
            img_res = requests.get(image_api_url, params=params, headers=headers, timeout=10)
            data = img_res.json()
            results = data.get("results", [])
            
            for r in results:
                img_url = r.get("image")
                if img_url and img_url.startswith("http"):
                    if not any(x in img_url.lower() for x in ["logo", "avatar", "icon", "placeholder", "gif", "profile"]):
                        if is_valid_image_url(img_url):
                            print(f"✅ DuckDuckGo se matching photo mil gayi!")
                            return img_url
    except Exception as e:
        print(f"⚠️ DuckDuckGo search error: {e}")
    return None

def generate_ai_image_from_title(title, category):
    """
    Generate HD image using Pollinations AI based on title
    This creates unique images matching the news content
    """
    print(f"🎨 AI se custom image bana raha hai for: {title[:50]}...")
    
    try:
        # Clean title for prompt
        clean_title = title.replace('"', '').replace("'", '').replace('&', 'and')[:100]
        
        # Category-specific style hints
        style_hints = {
            "Technology": "technology, futuristic, digital, modern",
            "Gaming": "gaming, esports, cyberpunk, RGB",
            "Entertainment": "cinema, hollywood, celebrity, red carpet",
            "Space": "space, galaxy, planets, cosmos",
            "Sports": "sports, stadium, action, victory",
            "Business": "business, corporate, finance, success",
            "Politics": "politics, government, leadership, assembly",
            "Health": "healthcare, medical, hospital, wellness",
            "Automobile": "automobile, luxury car, road, speed"
        }
        
        style = style_hints.get(category, "news, vibrant, professional")
        
        # Create detailed prompt
        prompt = f"{clean_title}, {style}, high quality, 4k, realistic, professional news photography, HD banner"
        
        # Generate image with Pollinations AI
        url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1200&height=630&nologo=true&seed={random.randint(1, 99999)}"
        
        print(f"🎨 AI Image URL generated: {url[:100]}...")
        
        # Validate the image
        if is_valid_image_url(url):
            print("✅ AI ne HD custom image banayi hai!")
            return url
        else:
            print("⚠️ AI image valid nahi hai, retry kar raha hai...")
            # Try one more time with different seed
            url2 = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1200&height=630&nologo=true&seed={random.randint(1, 99999)}"
            if is_valid_image_url(url2):
                print("✅ AI ne HD custom image banayi hai (retry)!")
                return url2
                
    except Exception as e:
        print(f"⚠️ AI image generation error: {e}")
    return None

def get_smart_image(title, category, rss_image=None):
    """
    SMART IMAGE MATCHING SYSTEM:
    1. Try to get image from RSS feed
    2. If not found, search Google Images
    3. If not found, search DuckDuckGo Images
    4. If not found, generate AI image based on title
    5. If all fail, use category image
    """
    print("\n🖼️ SMART IMAGE MATCHING SYSTEM STARTED...")
    print(f"📝 Title: {title[:100]}")
    print(f"📂 Category: {category}")
    
    # Clean title for search
    search_title = clean_and_format_title(title)
    search_query = search_title[:100]
    
    # === LEVEL 1: RSS Image ===
    if rss_image and rss_image.startswith('http'):
        print("📸 LEVEL 1: Checking RSS image...")
        if is_valid_image_url(rss_image):
            print("✅ RSS image is valid!")
            return rss_image
        else:
            print("⚠️ RSS image is not valid!")
    
    # === LEVEL 2: Google Images ===
    print("📸 LEVEL 2: Searching Google Images...")
    google_img = get_google_images(search_query)
    if google_img:
        return google_img
    
    # === LEVEL 3: DuckDuckGo Images ===
    print("📸 LEVEL 3: Searching DuckDuckGo Images...")
    ddg_img = get_duckduckgo_images(search_query)
    if ddg_img:
        return ddg_img
    
    # === LEVEL 4: AI Generated Image ===
    print("📸 LEVEL 4: Generating AI image from title...")
    ai_img = generate_ai_image_from_title(search_title, category)
    if ai_img:
        return ai_img
    
    # === LEVEL 5: Category Fallback ===
    print("📸 LEVEL 5: Using category fallback image...")
    if category in UNSPLASH_IMAGES:
        return UNSPLASH_IMAGES[category]
    
    # === LEVEL 6: Final Default ===
    print("📸 LEVEL 6: Using default image...")
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1200&q=80"

# ============================================
# 🔐 BLOGGER AUTHENTICATION
# ============================================
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

def is_similar_to_existing(new_title, existing_titles):
    """Check if title is similar to existing posts"""
    stop_words = {"in", "the", "and", "of", "to", "for", "with", "on", "at", "by", "an", "is", "vs", "me", "ko", "par", "se", "ka", "ki", "ke", "ne", "bada", "badi", "hui", "thi", "gaya", "macha", "hua", "huye", "says", "against", "over"}
    
    def get_keywords(text):
        words = re.sub(r'[^\w\s]', '', text.lower()).split()
        return {w for w in words if len(w) > 3 and w not in stop_words}
    
    new_keywords = get_keywords(new_title)
    if not new_keywords:
        return False
        
    for existing in existing_titles:
        existing_keywords = get_keywords(existing)
        overlap = new_keywords.intersection(existing_keywords)
        if len(overlap) >= 3:
            print(f"⚠️ Similar news detected! Keywords: {overlap}")
            return True
    return False

# ============================================
# 📰 RSS PROCESSING
# ============================================
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
    """Extract image from RSS feed entry"""
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

def get_hd_image_strict(entry, title, category):
    """Get HD image using smart matching system"""
    # Get RSS image if available
    rss_image = get_entry_image(entry)
    
    # Use smart image matching
    return get_smart_image(title, category, rss_image)

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
    if match_words(["movie", "film", "bollywood", "hollywood", "actor", "actress", "song", "singer", "celebrity"]):
        return "Entertainment"
    
    if any(x in feed_lower for x in ["livemint", "economictimes"]):
        return "Business"
    if match_words(["stocks", "market", "economy", "finance", "nifty", "sensex"]):
        return "Business"
    
    if any(x in feed_lower for x in ["techcrunch", "theverge", "gadgets360"]):
        return "Technology"
    if match_words(["smartphone", "apple", "samsung", "software", "chatgpt", "iphone", "gadget", "ai"]):
        return "Technology"
    
    return "News"

# ============================================
# 🤖 GEMINI WITH QUOTA HANDLING
# ============================================
def generate_super_detailed_content_gemini(title, full_content, category):
    if not GEMINI_API_KEY:
        print("⚠️ GEMINI_API_KEY not found!")
        return None

    models_to_try = [
        'gemini-2.0-flash',
        'gemini-1.5-flash'
    ]
    
    for model in models_to_try:
        try:
            print(f"⏳ Trying {model}...")
            client = genai.Client(api_key=GEMINI_API_KEY)

            prompt = f"""
            Write a professional, engaging Hindi/Hinglish news article.
            
            Title: {title}
            Category: {category}
            Source Content: {full_content[:3000]}
            
            Instructions:
            1. Create a viral Hinglish title inside [TITLE]...[/TITLE] tags
            2. Write in professional Hindi
            3. Use these sections:
               - <h3>📝 परिचय - Introduction</h3>
               - <h3>🎯 मुख्य बिंदु - Key Highlights</h3>
               - <h3>📊 विश्लेषण - Analysis</h3>
               - <h3>🔮 आगे क्या? - What's Next?</h3>
               - <h3>✅ निष्कर्ष - Conclusion</h3>
            4. Minimum 500+ words
            """

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=4096,
                ),
            )
            
            output_text = response.text

            if output_text and len(output_text) > 200:
                print(f"✅ Article generated with {model}!")
                
                viral_title = title
                title_match = re.search(r'\[TITLE\](.*?)\[/TITLE\]', output_text, re.IGNORECASE | re.DOTALL)
                if title_match:
                    viral_title = title_match.group(1).strip()
                    output_text = output_text.replace(title_match.group(0), "")
                
                return viral_title, output_text

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print(f"⚠️ Quota exceeded for {model}, trying next...")
                time.sleep(2)
                continue
            else:
                print(f"⚠️ Gemini API error: {e}")
                continue
    
    print("❌ All Gemini models failed! Using fallback...")
    return None

# ============================================
# 📝 FALLBACK CONTENT
# ============================================
def get_detailed_fallback_content(title, full_content, category):
    print("🔄 Using fallback content...")
    today = get_current_date()
    clean_title = clean_and_format_title(title)
    first_para = full_content[:800] if full_content else ""
    more_content = full_content[800:1600] if len(full_content) > 800 else ""
    
    category_emoji = {
        "News": "📰",
        "Politics": "🏛️",
        "Sports": "🏏",
        "Entertainment": "🎬",
        "Business": "💰",
        "Technology": "💻",
        "Health": "🏥",
        "Automobile": "🚗"
    }.get(category, "📰")
    
    highlights = [
        f"<li>🔴 <strong>{clean_title[:50]}</strong> - आज की बड़ी खबर</li>",
        f"<li>📰 <strong>मुख्य घटना:</strong> {first_para[:100]}...</li>",
    ]
    
    if len(more_content) > 50:
        highlights.append(f"<li>📌 <strong>विस्तार:</strong> {more_content[:100]}...</li>")
    
    highlights.append(f"<li>📅 <strong>तारीख:</strong> {today}</li>")
    highlights.append(f"<li>📂 <strong>श्रेणी:</strong> {category}</li>")
    
    return f"""
    <h2>🚨 {clean_title}</h2>
    <div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0;">
        <p><strong>📅 Published: {today}</strong></p>
        <p><strong>📂 Category: {category}</strong></p>
    </div>
    <h3>📝 परिचय - Introduction</h3>
    <p>{category_emoji} <strong>{clean_title}</strong></p>
    <p>{first_para}</p>
    <h3>🎯 मुख्य बातें - Key Highlights</h3>
    <ul>{''.join(highlights)}</ul>
    <h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
    <p>{first_para}</p>
    {f'<p>{more_content}</p>' if more_content else ''}
    <h3>✅ निष्कर्ष - Conclusion</h3>
    <p>{clean_title} - यह एक महत्वपूर्ण घटनाक्रम है।</p>
    """

# ============================================
# 📝 POST TO BLOGGER
# ============================================
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
        else:
            print(f"⚠️ Blogger API Error: {post_res.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Error posting: {e}")
        return None

# ============================================
# 🏥 HEALTH CHECK
# ============================================
def check_bot_health():
    print("\n🏥 Running Health Check...")
    checks = {
        "Gemini API": lambda: bool(GEMINI_API_KEY),
        "Blogger Token": lambda: bool(get_blogger_access_token()),
        "RSS Feeds": lambda: len(RSS_FEEDS) > 0,
    }
    
    all_ok = True
    for name, check in checks.items():
        try:
            status = "✅" if check() else "❌"
            print(f"{status} {name}")
            if "❌" in status:
                all_ok = False
        except:
            print(f"❌ {name} (Error)")
            all_ok = False
    
    return all_ok

def fix_dns():
    print("✅ Testing connection...")
    try:
        res = requests.get("https://text.pollinations.ai", timeout=10)
        print(f"✅ Connection OK (Status: {res.status_code})")
    except Exception as e:
        print(f"⚠️ Connection error: {e}")

# ============================================
# 🚀 MAIN FUNCTION
# ============================================
def main():
    print("\n🤖 Starting Viral News AI Blogger Bot...")
    print(f"📅 {get_current_date()}")
    print(f"🔑 Gemini API: {'✅ Set' if GEMINI_API_KEY else '❌ Not Set'}")
    
    try:
        fix_dns()
        access_token = get_blogger_access_token()
        
        if not access_token:
            print("❌ Invalid Blogger Token!")
            return
        
        MANUAL_URL = os.getenv('MANUAL_URL')
        
        if MANUAL_URL:
            print(f"🎯 Manual mode: {MANUAL_URL}")
            raw_title = "Trending News Update"
            full_content = f"Read about: {MANUAL_URL}"
            category = "News"
            link = MANUAL_URL
            image_url = get_smart_image(raw_title, category, None)
        else:
            print("🔍 Searching RSS feeds...")
            existing_titles = get_all_blogger_titles(access_token)
            local_posted = load_posted_news()
            all_posted = existing_titles.union(local_posted)
            
            found_news = False
            entry = None
            selected_feed = None
            image_url = None
            
            shuffled_feeds = RSS_FEEDS.copy()
            random.shuffle(shuffled_feeds)
            
            for feed_url in shuffled_feeds:
                try:
                    print(f"📡 Checking: {feed_url}")
                    response = requests.get(feed_url, timeout=15)
                    if response.status_code == 200:
                        feed = feedparser.parse(response.content)
                        for i in range(min(15, len(feed.entries))):
                            temp_entry = feed.entries[i]
                            temp_title = temp_entry.title
                            
                            if is_duplicate_title(temp_title, all_posted):
                                continue
                            
                            if is_similar_to_existing(temp_title, all_posted):
                                continue
                            
                            category = detect_category(feed_url, temp_title)
                            # Get image using smart system
                            image_url = get_hd_image_strict(temp_entry, temp_title, category)
                            
                            if image_url:
                                entry = temp_entry
                                selected_feed = feed_url
                                found_news = True
                                print(f"✅ Found: {temp_title[:50]}...")
                                break
                        if found_news:
                            break
                except Exception as e:
                    print(f"⚠️ Feed error: {e}")
                    continue
                    
            if not found_news or not entry:
                print("❌ No new news found!")
                return
                
            raw_title = entry.title
            link = entry.link
            full_content = get_full_content(entry)
            category = detect_category(selected_feed, raw_title)
        
        # Generate content
        ai_result = generate_super_detailed_content_gemini(raw_title, full_content, category)
        
        if ai_result:
            viral_title, ai_content = ai_result
            print("✅ Using Gemini content")
        else:
            print("⚠️ Using fallback content...")
            viral_title = raw_title
            ai_content = get_detailed_fallback_content(raw_title, full_content, category)

        # Build final post
        safe_viral_title = viral_title.replace("'", "&#39;").replace('"', "&quot;")
        
        image_html = f"""
        <div style="text-align:center;margin-bottom:25px;">
            <img src="{image_url}" alt="{safe_viral_title}" style="width:100%;max-width:800px;height:auto;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.15);">
            <p style="font-size:12px;color:#999;margin-top:5px;">📸 Viral News AI | HD Quality</p>
        </div>
        """
        
        short_link = get_short_url(link)
        earning_button = f"""
        <div style="text-align:center;margin:30px 0;padding:20px;background:#f5f5f5;border-radius:12px;">
            <a href="{short_link}" target="_blank" style="background:linear-gradient(135deg,#ff5722,#ff6f00);color:white;padding:20px 60px;text-decoration:none;font-size:22px;font-weight:bold;border-radius:50px;display:inline-block;text-transform:uppercase;box-shadow:0 4px 15px rgba(255,87,34,0.3);">
                📖 पूरी खबर पढ़ें - READ FULL STORY
            </a>
        </div>
        """
        
        final_content = f"{image_html}\n{ai_content}\n{earning_button}"
        
        print(f"📝 Uploading to Blogger...")
        post_url = post_to_blogger(access_token, viral_title, final_content, category)
        
        if post_url:
            save_posted_news(viral_title)
            print("\n✅✅✅ POSTED SUCCESSFULLY! ✅✅✅")
            print(f"🔗 {post_url}")
            
            ping_search_engines("Viral News AI", post_url)
            share_to_telegram(viral_title, post_url)
            share_to_discord(viral_title, post_url)
            
            with open('success_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now()}: {viral_title} -> {post_url}\n")
        else:
            print("❌ Posting failed!")

    except Exception as e:
        print(f"❌ Critical error: {e}")
        with open('error_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()}: {str(e)}\n")

# ============================================
# 🚀 ENTRY POINT
# ============================================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
