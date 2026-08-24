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
from google import genai  # ✅ Google GenAI SDK
from google.genai import types  # ✅ Stable configuration types

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
    "https://usafiesta.com/feed/",  # ✅ Added USAFiesta Feed to target automatic news
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
        prompt = f"{clean} {category} news banner style"
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
# 🤖 GOOGLE GEMINI STABLE PRODUCTION MODEL (FAST & RELIABLE)
# ============================================
def generate_super_detailed_content_gemini(title, full_content, category):
    """
    स्थिर और बिजली जैसी तेज़ गति वाले 'gemini-2.5-flash' का उपयोग करके
    स्क्रीनशॉट की तरह बेहतरीन हिंदी समाचार ब्लॉग लिखेगा।
    """
    if not GEMINI_API_KEY:
        print("⚠️ GEMINI_API_KEY नहीं मिली!")
        return None

    try:
        print("⏳ Google GenAI (gemini-2.5-flash) के माध्यम से पोस्ट जनरेट कर रहा हूँ...")
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = (
            f"Write a comprehensive, professional, highly engaging Hindi/Hinglish news article. "
            f"Source News Title: {title}\n"
            f"Source Content: {full_content[:3000]}\n"
            f"Category: {category}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Generate a viral, attractive Hinglish title and enclose it inside [TITLE] ... [/TITLE] tags.\n"
            f"2. Write the article in standard, high-quality professional Hindi (समाचार पोर्टल की भाषा) with structured HTML tags.\n"
            f"3. Strictly use these exact headings matching premium news layouts:\n"
            f"   - <h3>📝 परिचय - Introduction</h3> (An elaborate intro in standard Hindi)\n"
            f"   - <h3>🎯 मुख्य बिंदु और घटनाक्रम - Key Highlights</h3> (8 detailed points/facts in a bulleted list)\n"
            f"   - <h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3> (A deep journalistic analysis of the issue)\n"
            f"   - <h3>🔮 अब आगे क्या? - What's Next?</h3> (Future prospects, official responses, and future steps)\n"
            f"   - <h3>✅ निष्कर्ष - Conclusion</h3> (A powerful wrap-up paragraph)\n"
            f"4. The word count must be extremely detailed (minimum 1500+ words of deep value)."
        )

        # ✅ रीयल-टाइम गूगल सर्च ग्राउंडिंग के साथ प्रोडक्शन जेमिनी मॉडल
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}],
            ),
        )
        
        output_text = response.text

        if output_text and len(output_text) > 200:
            print("✅ जेमिनी ने रीयल-टाइम सर्च के साथ लेख सफलतापूर्वक जनरेट कर लिया है!")
            
            # Title और Content को अलग करना
            viral_title = title
            title_match = re.search(r'\[TITLE\](.*?)\[/TITLE\]', output_text, re.IGNORECASE | re.DOTALL)
            if title_match:
                viral_title = title_match.group(1).strip()
                output_text = output_text.replace(title_match.group(0), "")
            
            return viral_title, output_text

    except Exception as e:
        print(f"⚠️ जेमिनी एपीआई के दौरान गंभीर समस्या: {e}")
        
    return None

# ============================================
# 📝 DETAILED FALLBACK CONTENT (When AI fails)
# ============================================
def get_detailed_fallback_content(title, full_content, category):
    print("🔄 Using detailed fallback template...")
    today = get_current_date()
    clean_title = clean_and_format_title(title)
    first_para = full_content[:800] if full_content else ""
    more_content = full_content[800:1600] if len(full_content) > 800 else ""
    
    if category == "Entertainment":
        highlights = [
            f"<li>🎬 <strong>{clean_title[:50]}</strong> - बॉलीवुड/एंटरटेनमेंट की बड़ी खबर</li>",
            f"<li>⭐ <strong>मुख्य घटना:</strong> {first_para[:80]}...</li>",
            f"<li>📅 <strong>तारीख:</strong> {more_content[:60]}...</li>",
            f"<li>🎥 <strong>प्रोडक्शन:</strong> इस प्रोजेक्ट पर काम जारी</li>",
            f"<li>🍿 <strong>फैंस की प्रतिक्रिया:</strong> सोशल मीडिया पर उत्साह</li>",
            f"<li>📈 <strong>बॉक्स ऑफिस:</strong> कलेक्शन अपडेट</li>",
        ]
        expert_quote = """
<p>Film industry experts are calling this a major development for Indian cinema. The combination of star power and meaningful content is what audiences are craving.</p>
<p>फिल्म इंडस्ट्री के विशेषज्ञों का मानना है कि यह भारतीय सिनेमा के लिए एक बड़ा विकास है।</p>
"""
        analysis_detail = f"<p>{first_para}</p><p>{more_content}</p>"
    
    elif category == "Sports":
        highlights = [
            f"<li>🏏 <strong>{clean_title[:50]}</strong> - खेल जगत की बड़ी खबर</li>",
            f"<li>⭐ <strong>मुख्य घटना:</strong> {first_para[:80]}...</li>",
            f"<li>📊 <strong>विश्लेषण:</strong> {more_content[:60]}...</li>",
        ]
        expert_quote = """<p>Sports experts believe this performance will boost team morale.</p>"""
        analysis_detail = f"<p>{first_para}</p><p>{more_content}</p>"
    
    else:
        highlights = [
            f"<li>🔴 <strong>{clean_title[:50]}</strong> - आज की बड़ी खबर</li>",
            f"<li>📰 <strong>विस्तार:</strong> {first_para[:80]}...</li>",
        ]
        expert_quote = f"<p>Experts are weighing in on this significant development.</p>"
        analysis_detail = f"<p>{first_para}</p><p>{more_content}</p>"
    
    intro = f"<h3>📝 परिचय - Introduction</h3><p>{clean_title}</p><p>{first_para}</p>"
    analysis = f"<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>{analysis_detail}"
    expert = f"<h3>💬 विशेषज्ञों की राय - Expert Opinions</h3>{expert_quote}"
    impact = f"<h3>🌍 प्रभाव और आगे क्या? - Impact & What's Next</h3><p>इस घटना के दूरगामी प्रभाव हो सकते हैं।</p>"
    conclusion = f"<h3>✅ निष्कर्ष - Conclusion</h3><p>{clean_title} - यह एक महत्वपूर्ण घटनाक्रम है।</p>"
    
    return f"""
<h2>🚨 BREAKING NEWS: {clean_title}</h2>
<div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0;">
    <p><strong>📅 Published: {today}</strong></p>
    <p><strong>📂 Category: {category}</strong></p>
</div>
{intro}
<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>{''.join(highlights)}</ul>
{analysis}
{expert}
{impact}
{conclusion}
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

# ============================================
# 🚀 MAIN RUNNER (OPTIMIZED)
# ============================================
def main():
    print("🤖 Starting Viral News AI Blogger Bot...")
    print(f"📅 {get_current_date()}")
    fix_dns()
    
    access_token = get_blogger_access_token()
    if not access_token:
        print("❌ Invalid Blogger Token!")
        return
    
    MANUAL_URL = os.getenv('MANUAL_URL')
    
    if MANUAL_URL:
        print(f"🎯 मैनुअल मोड सक्रिय! इस लिंक की खबर प्रोसेस की जा रही है: {MANUAL_URL}")
        raw_title = "Trending News Update"
        full_content = f"Please read and write about this URL: {MANUAL_URL}"
        category = "News"
        link = MANUAL_URL
        image_url = generate_hd_image_with_text("Trending India News", category)
    else:
        print("🔍 सामान्य मोड: RSS फीड्स से ताज़ा खबर खोज रहा हूँ...")
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
                response = requests.get(feed_url, timeout=15)
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    for i in range(min(15, len(feed.entries))):
                        temp_entry = feed.entries[i]
                        temp_title = temp_entry.title
                        
                        # 🚫 CATEGORY BOTTLENECK REMOVED
                        if is_duplicate_title(temp_title, all_posted):
                            continue
                        
                        category = detect_category(feed_url, temp_title)
                        image_url = get_hd_image_strict(temp_entry, temp_title, category)
                        if image_url:
                            entry = temp_entry
                            selected_feed = feed_url
                            found_news = True
                            break
                    if found_news:
                        break
            except:
                continue
                
        if not found_news or not entry:
            print("❌ कोई नई न्यूज़ नहीं मिली!")
            return
            
        raw_title = entry.title
        link = entry.link
        full_content = get_full_content(entry)
        category = detect_category(selected_feed, raw_title)
    
    ai_result = generate_super_detailed_content_gemini(raw_title, full_content, category)
    
    if ai_result:
        viral_title, ai_content = ai_result
    else:
        print("⚠️ जेमिनी फ़ेल रहा! बेसिक ऑफ़लाइन जनरेटर का उपयोग कर रहा हूँ...")
        viral_title = raw_title
        ai_content = get_detailed_fallback_content(raw_title, full_content, category)

    image_html = f"""
    <div style="text-align:center;margin-bottom:25px;">
        <img src='{image_url}' alt='{viral_title}' style='width:100%;max-width:800px;height:auto;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.15);'>
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
    
    print(f"📝 Blogger पर पोस्ट अपलोड कर रहा हूँ...")
    post_url = post_to_blogger(access_token, viral_title, final_content, category)
    
    if post_url:
        save_posted_news(viral_title)
        print("\n✅✅✅ POSTED SUCCESSFULLY! ✅✅✅")
        print(f"🔗 {post_url}")
        ping_search_engines("Viral News AI", post_url)
        share_to_telegram(viral_title, post_url)
        share_to_discord(viral_title, post_url)
    else:
        print("❌ पोस्टिंग विफल!")

if __name__ == "__main__":
    main()
