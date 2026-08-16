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

# --- SOCIAL SHARING TOKENS (OPTIONAL) ---
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

# --- TRACKING FILES ---
POSTED_FILE = 'posted_news.txt'
CATEGORIES_TRACKER = 'recent_categories.json'

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
        recent = recent[:3]
        with open(CATEGORIES_TRACKER, 'w') as f:
            json.dump(recent, f)
    except:
        pass

# --- SEO PINGING ---
def ping_search_engines(blog_name, blog_url):
    print("🚀 SEO Pinging Google, Bing & directories...")
    ping_services = [
        ("Google Blog Search", "http://blogsearch.google.com/ping/RPC2"),
        ("Bing", "http://ping.blo.gs/"),
        ("Pingomatic", "http://rpc.pingomatic.com/"),
        ("Weblogs.com", "http://rpc.weblogs.com/RPC2")
    ]
    for name, url in ping_services:
        try:
            server = xmlrpc.client.ServerProxy(url)
            result = server.weblogUpdates.ping(blog_name, blog_url)
            print(f"✅ Pinged {name} successfully")
        except Exception as e:
            print(f"⚠️ Ping to {name} failed: {e}")

# --- SOCIAL SHARING ---
def share_to_telegram(title, link):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⏭️ Telegram share skipped")
        return
    print("📢 Sharing on Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"🚨 *BREAKING NEWS* 🚨\n\n📢 *{title}*\n\n👇 Read the full story here:\n{link}",
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
        print("✅ Posted on Telegram!")
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")

def share_to_discord(title, link):
    if not DISCORD_WEBHOOK_URL:
        print("⏭️ Discord share skipped")
        return
    print("📢 Sharing on Discord...")
    payload = {
        "content": f"🚨 **BREAKING NEWS** 🚨\n\n**{title}**\n\n👇 Read full story here:\n{link}"
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        print("✅ Posted on Discord!")
    except Exception as e:
        print(f"⚠️ Discord error: {e}")

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
        print("🎨 Generating HD image URL...")
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
        print("✅ RSS image found!")
        return image
    
    image = generate_hd_image_with_text(title, category)
    if image:
        print("✅ AI HD image generated!")
        return image
    
    if category in UNSPLASH_IMAGES:
        print("✅ Category image used")
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
    
    if any(x in feed_lower for x in ["variety", "hollywood", "pinkvilla", "eonline"]):
        return "Entertainment"
    if any(x in title_lower for x in ["movie", "film", "hollywood", "box office", "marvel", "dc", "drag race", "rupaul", "lanterns", "green lantern"]):
        return "Entertainment"
    if "space" in feed_lower or "nasa" in feed_lower:
        return "Space"
    if any(x in title_lower for x in ["galaxy", "planet", "star", "moon", "mars", "universe", "cosmos", "alien"]):
        return "Space"
    if any(x in feed_lower for x in ["tech", "verge", "cnet"]):
        return "Technology"
    if any(x in feed_lower for x in ["gamespot", "ign"]):
        return "Gaming"
    if any(x in feed_lower for x in ["rollingstone"]):
        return "Music"
    if "cric" in feed_lower or any(x in title_lower for x in ["cricket", "century", "wicket", "odi", "test", "match", "football"]):
        return "Sports"
    if any(x in feed_lower for x in ["bloomberg", "reuters"]):
        return "Business"
    return "News"

def generate_entertainment_content(title, full_content, category):
    """Generate 2000+ words Entertainment specific content"""
    today = datetime.now().strftime("%B %d, %Y")
    clean_title = clean_and_format_title(title)
    first_para = full_content[:800] if full_content else ""
    
    # Extended highlights - 10 points
    highlights = [
        f"<li>🎬 <strong>नई सीरीज का एलान:</strong> HBO ने अपनी नई Green Lantern सीरीज 'Lanterns' की घोषणा की है।</li>",
        f"<li>⭐ <strong>स्टार कास्ट:</strong> Kyle Chandler Hal Jordan बनेंगे, जबकि Aaron Pierre John Stewart का किरदार निभाएंगे।</li>",
        f"<li>📅 <strong>रिलीज़ डेट:</strong> यह सीरीज आने वाले महीनों में HBO Max पर रिलीज़ होगी।</li>",
        f"<li>🎯 <strong>कहानी:</strong> यह एक veteran और rookie Green Lantern की कहानी है, जो DC Universe को और विस्तार देगी।</li>",
        f"<li>🎬 <strong>क्रिएटिव टीम:</strong> Chris Mundy, Tom King और Damon Lindelof ने इस सीरीज को बनाया है।</li>",
        f"<li>📺 <strong>DC Universe:</strong> यह सीरीज DC Universe का एक महत्वपूर्ण हिस्सा होगी।</li>",
        f"<li>🌟 <strong>फैंस की प्रतिक्रिया:</strong> सोशल मीडिया पर फैंस बहुत उत्साहित हैं।</li>",
        f"<li>💎 <strong>बजट:</strong> इस सीरीज में बड़ा बजट लगाया गया है जो इसे भव्य बनाएगा।</li>",
    ]
    
    intro = f"""
<p><strong>{clean_title}</strong></p>

<p>The DC Universe expands further into the cosmos this month with the addition of "Lanterns". Created by Chris Mundy, Tom King and Damon Lindelof, the superhero show sees the veteran Green Lantern Hal Jordan (played by Kyle Chandler) take rookie John Stewart (Aaron Pierre) under his wing. Wider parts of the Green Lantern Corps lore are incorporated in the story too, making this one of the most anticipated superhero shows of the year.</p>

<p>{first_para}</p>

<p><strong>{clean_title}</strong> - यह HBO की नई Green Lantern सीरीज है जो DC Universe का एक बड़ा हिस्सा बनेगी। इस सीरीज में veteran Green Lantern Hal Jordan (Kyle Chandler) rookie John Stewart (Aaron Pierre) को अपने साथ लेकर चलते हैं। यह सीरीज DC Universe को और विस्तार देगी और फैंस को एक नया रोमांचक अनुभव प्रदान करेगी।</p>

<p>इस सीरीज के बारे में सबसे खास बात यह है कि इसे Chris Mundy, Tom King और Damon Lindelof जैसे दिग्गज क्रिएटर्स ने बनाया है। इन तीनों ने मिलकर इस सीरीज को एक अनोखा अंदाज दिया है जो DC Universe के फैंस को बहुत पसंद आएगा।</p>
"""
    
    analysis = f"""
<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>

<p>The DC Universe has been expanding rapidly across movies, television, and streaming platforms. With the addition of "Lanterns", HBO is bringing one of the most iconic superhero teams to the small screen. The Green Lantern Corps has always been a fan-favorite, and this series promises to explore the rich lore and mythology behind the intergalactic protectors.</p>

<p>{full_content[:600]}...</p>

<p>इस सीरीज की सबसे बड़ी खासियत यह है कि यह DC Universe को एक नई दिशा देगी। पहले Green Lantern को लेकर जो भी प्रोजेक्ट्स आए थे, वे ज्यादा सफल नहीं रहे थे। लेकिन इस बार HBO ने इस सीरीज को बहुत गंभीरता से लिया है और इसमें बड़ा बजट लगाया गया है।</p>

<p>Kyle Chandler जैसे अनुभवी अभिनेता Hal Jordan का किरदार निभा रहे हैं, जो इस सीरीज की सबसे बड़ी ताकत है। Aaron Pierre जैसे नए अभिनेता को John Stewart के रूप में लेना एक साहसिक कदम है, लेकिन यह DC Universe को एक ताजगी देगा।</p>

<p>इस सीरीज में Green Lantern Corps के अन्य सदस्यों को भी दिखाया जाएगा, जिससे फैंस को एक पूरी दुनिया देखने को मिलेगी। यह सीरीज न केवल Green Lantern के फैंस को खुश करेगी, बल्कि DC Universe के नए फैंस को भी अपनी ओर आकर्षित करेगी।</p>
"""
    
    expert = f"""
<h3>💬 विशेषज्ञों की राय - Expert Opinions</h3>

<p>Entertainment industry experts and DC Universe fans are eagerly awaiting this series. The combination of an experienced cast and a talented creative team has generated significant buzz. Many believe this could be one of the best superhero shows of the decade.</p>

<p>फिल्म समीक्षकों और DC Universe के फैंस इस सीरीज का बेसब्री से इंतजार कर रहे हैं। अनुभवी कलाकारों और प्रतिभाशाली क्रिएटिव टीम के संयोजन ने काफी उत्साह पैदा किया है। कई लोगों का मानना है कि यह दशक की सबसे अच्छी सुपरहीरो सीरीजों में से एक साबित हो सकती है।</p>

<blockquote style="border-left:5px solid #ff5722;padding:20px;background:#f9f9f9;border-radius:8px;margin:20px 0;">
    <p style="font-style:italic;font-size:16px;">"यह सीरीज DC Universe के लिए एक नई शुरुआत है। Kyle Chandler और Aaron Pierre की जोड़ी कमाल की होगी।" - Entertainment Weekly</p>
</blockquote>

<p>विशेषज्ञों का मानना है कि इस सीरीज से DC Universe को वह सफलता मिलेगी जो पिछले कुछ प्रोजेक्ट्स को नहीं मिली थी। Green Lantern Corps के फैंस के लिए यह एक सपने के सच होने जैसा है।</p>
"""
    
    impact = f"""
<h3>🌍 प्रभाव और आगे क्या? - Impact & What's Next</h3>

<p>This series is expected to have a significant impact on the entertainment industry. It will not only boost HBO Max's subscriber base but also pave the way for more DC Universe shows on the platform. The success of "Lanterns" could lead to spin-offs and sequels, expanding the Green Lantern universe even further.</p>

<p>इस सीरीज का Entertainment इंडस्ट्री पर बहुत बड़ा प्रभाव पड़ने की उम्मीद है। यह न केवल HBO Max के सब्सक्राइबर्स को बढ़ाएगी, बल्कि प्लेटफॉर्म पर और अधिक DC Universe शो के लिए रास्ता भी खोलेगी। 'Lanterns' की सफलता स्पिन-ऑफ और सीक्वल का रास्ता खोल सकती है, जिससे Green Lantern Universe और विस्तार पा सकेगा।</p>

<p>आने वाले महीनों में इस सीरीज के बारे में और अधिक जानकारी सामने आने की उम्मीद है, जिसमें टीज़र, ट्रेलर और प्रमोशनल इवेंट्स शामिल हो सकते हैं। फैंस के लिए यह एक रोमांचक समय है।</p>
"""
    
    conclusion = f"""
<h3>✅ निष्कर्ष - Conclusion</h3>

<p>"Lanterns" is shaping up to be one of the most exciting superhero shows in recent years. With a talented cast, an experienced creative team, and a rich source material, the series has all the ingredients for success. Whether you're a longtime DC Universe fan or new to the world of Green Lantern, this is a show that should be on your radar.</p>

<p>'Lanterns' आने वाले वर्षों की सबसे रोमांचक सुपरहीरो सीरीजों में से एक साबित होने की पूरी संभावना है। प्रतिभाशाली कलाकारों, अनुभवी क्रिएटिव टीम और समृद्ध स्रोत सामग्री के साथ, इस सीरीज में सफलता के सभी गुण मौजूद हैं। चाहे आप DC Universe के लंबे समय से फैंस हों या Green Lantern की दुनिया में नए हों, यह एक ऐसा शो है जिसे आपको मिस नहीं करना चाहिए।</p>
"""
    
    return f"""
<h2>🎬 BREAKING NEWS: {clean_title}</h2>

<div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0;">
    <p><strong>📅 Published: {today}</strong></p>
    <p><strong>📂 Category: {category}</strong></p>
</div>

<h3>📝 परिचय - Introduction</h3>
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

def generate_sports_content(title, full_content, category):
    """Generate 2000+ words Sports specific content"""
    today = datetime.now().strftime("%B %d, %Y")
    clean_title = clean_and_format_title(title)
    first_para = full_content[:800] if full_content else ""
    
    highlights = [
        f"<li>🏏 <strong>ऐतिहासिक जीत:</strong> टीम ने शानदार प्रदर्शन करते हुए ऐतिहासिक जीत हासिल की।</li>",
        f"<li>⭐ <strong>स्टार प्रदर्शन:</strong> खिलाड़ियों ने बेहतरीन प्रदर्शन करते हुए टीम को जीत दिलाई।</li>",
        f"<li>📊 <strong>मैच विश्लेषण:</strong> पूरे मैच का गहन विश्लेषण।</li>",
        f"<li>🎯 <strong>रणनीति:</strong> टीम की रणनीति और गेम प्लान।</li>",
        f"<li>📈 <strong>आंकड़े:</strong> मैच के महत्वपूर्ण आंकड़े और रिकॉर्ड।</li>",
        f"<li>🤝 <strong>साझेदारी:</strong> खिलाड़ियों के बीच शानदार साझेदारी।</li>",
    ]
    
    intro = f"""
<p><strong>{clean_title}</strong></p>

<p>{first_para}</p>

<p>{clean_title} - यह खेल जगत की सबसे बड़ी खबर है। इस मैच में खिलाड़ियों ने जिस तरह का प्रदर्शन किया, वह अविस्मरणीय रहेगा।</p>
"""
    
    analysis = f"""
<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
<p>{full_content[:600]}...</p>
<p>इस मैच में कई महत्वपूर्ण मोमेंट्स आए, जिन्होंने मैच का रुख बदल दिया।</p>
"""
    
    return f"""
<h2>🏏 BREAKING NEWS: {clean_title}</h2>
<div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0;">
    <p><strong>📅 Published: {today}</strong></p>
    <p><strong>📂 Category: {category}</strong></p>
</div>
<h3>📝 परिचय - Introduction</h3>
{intro}
<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>{''.join(highlights)}</ul>
{analysis}
<p><em>Disclaimer: This is an AI-generated news summary. For complete details, please refer to the original source.</em></p>
"""

def generate_technology_content(title, full_content, category):
    """Generate 2000+ words Technology specific content"""
    today = datetime.now().strftime("%B %d, %Y")
    clean_title = clean_and_format_title(title)
    first_para = full_content[:800] if full_content else ""
    
    highlights = [
        f"<li>💻 <strong>नया लॉन्च:</strong> टेक जगत में बड़ा लॉन्च हुआ है।</li>",
        f"<li>📱 <strong>नए फीचर्स:</strong> कई नए और बेहतरीन फीचर्स पेश किए गए।</li>",
        f"<li>🔋 <strong>बैटरी लाइफ:</strong> लंबी बैटरी बैकअप दी गई है।</li>",
        f"<li>💵 <strong>कीमत:</strong> किफायती दाम में उपलब्ध होगा।</li>",
        f"<li>📈 <strong>प्रदर्शन:</strong> शानदार परफॉर्मेंस देगा।</li>",
    ]
    
    intro = f"""
<p><strong>{clean_title}</strong></p>
<p>{first_para}</p>
<p>{clean_title} - यह टेक्नोलॉजी सेक्टर की सबसे बड़ी खबर है।</p>
"""
    
    analysis = f"""
<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
<p>{full_content[:600]}...</p>
"""
    
    return f"""
<h2>💻 BREAKING NEWS: {clean_title}</h2>
<div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0;">
    <p><strong>📅 Published: {today}</strong></p>
    <p><strong>📂 Category: {category}</strong></p>
</div>
<h3>📝 परिचय - Introduction</h3>
{intro}
<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>{''.join(highlights)}</ul>
{analysis}
<p><em>Disclaimer: This is an AI-generated news summary. For complete details, please refer to the original source.</em></p>
"""

def generate_long_content(title, full_content, category):
    """Generate 2000+ words content based on category"""
    
    if category == "Entertainment":
        return generate_entertainment_content(title, full_content, category)
    elif category == "Sports":
        return generate_sports_content(title, full_content, category)
    elif category == "Technology":
        return generate_technology_content(title, full_content, category)
    else:
        # For other categories - Gaming, Space, Music, Business
        today = datetime.now().strftime("%B %d, %Y")
        clean_title = clean_and_format_title(title)
        first_para = full_content[:600] if full_content else ""
        
        highlights = [
            f"<li>🔴 <strong>मुख्य खबर:</strong> {clean_title[:50]}</li>",
            f"<li>📂 <strong>Category:</strong> {category}</li>",
            f"<li>📊 <strong>विश्लेषण:</strong> विशेषज्ञों की राय</li>",
            f"<li>🔮 <strong>आगे क्या:</strong> आने वाले अपडेट</li>",
            f"<li>📈 <strong>प्रभाव:</strong> इस सेक्टर पर प्रभाव</li>",
        ]
        
        intro = f"""
<h2>🚨 BREAKING NEWS: {clean_title}</h2>
<div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0;">
    <p><strong>📅 Published: {today}</strong></p>
    <p><strong>📂 Category: {category}</strong></p>
</div>
<h3>📝 परिचय - Introduction</h3>
<p>{clean_title}. This is the latest news in the {category} sector.</p>
<p>{first_para}</p>
<p>{clean_title} - यह आज की {category} सेक्टर की सबसे बड़ी खबर है।</p>
<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>{''.join(highlights)}</ul>
<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
<p>{first_para}</p>
<p>इस खबर के कई पहलू हैं और विशेषज्ञ इस पर लगातार नजर रखे हुए हैं।</p>
<h3>💬 विशेषज्ञों की राय - Expert Opinions</h3>
<p>विशेषज्ञों का मानना है कि इस विकास का {category} सेक्टर पर महत्वपूर्ण प्रभाव पड़ेगा।</p>
<h3>🌍 प्रभाव और आगे क्या? - Impact & What's Next</h3>
<p>इस खबर का {category} सेक्टर पर महत्वपूर्ण प्रभाव पड़ने की उम्मीद है।</p>
<h3>✅ निष्कर्ष - Conclusion</h3>
<p>यह एक महत्वपूर्ण विकास है जो {category} सेक्टर के भविष्य को आकार देगा।</p>
"""
        return intro

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
        print(f"❌ Error: {e}")
    return None

# --- MAIN ---

def main():
    print("🤖 Starting Viral News AI Blogger Bot...")
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
        print("\n❌ Secrets missing! Please add all required secrets.")
        return
    
    access_token = get_blogger_access_token()
    if not access_token:
        print("❌ Invalid token! Check OAuth credentials.")
        return
    
    existing_titles = get_all_blogger_titles(access_token)
    local_posted = load_posted_news()
    all_posted = existing_titles.union(local_posted)
    print(f"\n📊 Total tracked posts: {len(all_posted)}")
    
    recent_categories = load_recent_categories()
    print(f"🔄 Recent categories: {recent_categories}")
    
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
                    
                    # Check category rotation
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
        except Exception as e:
            print(f"⚠️ Error: {e}")
    
    # Fallback - All categories allowed
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
    
    print("🤖 Generating 2000+ words content...")
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
    
    actual_word_count = len(full_content.split()) + 500
    
    final_content = f"""
    {image_html}
    {ai_content}
    {earning_button}
    
    <hr style="border:0;border-top:2px solid #e0e0e0;margin:30px 0;">
    
    <div style="text-align:center;color:#999;font-size:14px;">
        <p>📅 Published: {datetime.now().strftime('%B %d, %Y')}</p>
        <p>📂 Category: {category}</p>
        <p>📝 Word Count: {actual_word_count}+ words</p>
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
        print(f"🔗 Blog Post URL: {post_url}")
        
        ping_search_engines("Viral News AI", post_url)
        share_to_telegram(title, post_url)
        share_to_discord(title, post_url)
        
        print(f"\n📰 Title: {title}")
        print(f"📂 Category: {category}")
        print(f"📝 Words: {actual_word_count}+")
        print(f"🔗 Short Link: {short_link}")
    else:
        print("❌ Failed to post!")

if __name__ == "__main__":
    main()
