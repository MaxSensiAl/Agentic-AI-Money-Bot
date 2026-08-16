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
    if any(x in title_lower for x in ["movie", "film", "hollywood", "box office", "marvel", "dc", "drag race", "rupaul"]):
        return "Entertainment"
    if "space" in feed_lower or "nasa" in feed_lower:
        return "Space"
    if any(x in feed_lower for x in ["tech", "verge", "cnet"]):
        return "Technology"
    if any(x in feed_lower for x in ["gamespot", "ign"]):
        return "Gaming"
    if any(x in feed_lower for x in ["rollingstone"]):
        return "Music"
    if "cric" in feed_lower or any(x in title_lower for x in ["cricket", "century", "wicket", "odi", "test", "match"]):
        return "Sports"
    if any(x in feed_lower for x in ["bloomberg", "reuters"]):
        return "Business"
    return "News"

# --- AI CONTENT GENERATION ---
def generate_content_via_ai(title, full_content, category):
    if not HF_TOKEN:
        print("⚠️ HF_TOKEN missing!")
        return None
    
    models = [
        "mistralai/Mistral-7B-Instruct-v0.1",
        "meta-llama/Llama-2-7b-chat-hf"
    ]
    
    system_prompt = """You are "Viral News AI", a professional SEO-friendly Hinglish content generator.
Rules:
1. Write detailed sections (1000-1500 words total).
2. No incomplete words (write "Seasons", not "Seaso").
3. Single bullet points (•) only.
4. No generic filler text.
5. For Sports: Use "Match Analysis", not "Industry Impact".
6. Return content in HTML format."""

    user_prompt = f"""Generate a detailed Hinglish blog post for:
Title: {title}
Category: {category}
Reference: {full_content[:1500]}

Output structure:
<h3>📝 परिचय - Introduction</h3>
[English paragraph + Hindi paragraph]

<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>
  <li>• Point 1</li>
  <li>• Point 2</li>
  <li>• Point 3</li>
  <li>• Point 4</li>
</ul>

<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
[English + Hindi paragraphs]

<h3>💬 विशेषज्ञों की राय - Expert Opinions</h3>
[English + Hindi with quote]

<h3>🌍 प्रभाव और आगे क्या? - Impact & What's Next</h3>
[English + Hindi]

<h3>✅ निष्कर्ष - Conclusion</h3>
[English + Hindi]
"""

    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    
    for model in models:
        api_url = f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions"
        print(f"🧠 Trying: {model}...")
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.7
        }
        
        for attempt in range(3):
            try:
                response = requests.post(api_url, headers=headers, json=payload, timeout=60)
                res_data = response.json()
                
                if response.status_code == 200:
                    text = res_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if text and len(text.strip()) > 300:
                        return text.strip()
                
                elif response.status_code == 503:
                    wait = int(res_data.get("estimated_time", 25))
                    print(f"⏳ Model loading, waiting {wait}s...")
                    time.sleep(wait + 5)
                    continue
                else:
                    print(f"⚠️ Status {response.status_code}")
                    break
            except Exception as e:
                print(f"⚠️ Error: {e}")
                break
                
    return None

# --- FALLBACK CONTENT ---
def fallback_long_content(title, full_content, category):
    today = datetime.now().strftime("%B %d, %Y")
    clean_title = clean_and_format_title(title)
    first_para = full_content[:400] if full_content else ""
    
    highlights = [
        f"<li>• <strong>{clean_title[:50]}</strong> - आज की बड़ी खबर</li>",
        f"<li>• <strong>{category}</strong> सेक्टर में बड़ा बदलाव</li>",
        f"<li>• विशेषज्ञों की राय - Expert insights</li>",
        f"<li>• आगे क्या होगा - What's next</li>",
    ]
    
    return f"""
<h2>🚨 BREAKING NEWS: {clean_title}</h2>
<div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0;">
    <p><strong>📅 Published: {today}</strong></p>
    <p><strong>📂 Category: {category}</strong></p>
</div>
<h3>📝 परिचय - Introduction</h3>
<p>{clean_title}. This is the latest news in the {category} sector.</p>
<p>{clean_title} - यह आज की {category} सेक्टर की बड़ी खबर है।</p>
<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>{''.join(highlights)}</ul>
<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
<p>{first_para}</p>
<h3>💬 विशेषज्ञों की राय - Expert Opinions</h3>
<p>Experts believe this will have a significant impact on the {category} sector.</p>
<h3>🌍 प्रभाव और आगे क्या? - Impact & What's Next</h3>
<p>More updates are expected in the coming days.</p>
<h3>✅ निष्कर्ष - Conclusion</h3>
<p>This is an important development in the {category} field.</p>
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
    
    # Pass 1: Category Rotation
    print("\n🔍 Searching with category rotation...")
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
                        print(f"✅ Found in '{category}' (Rotation)!")
                        break
                if found_news:
                    break
        except Exception as e:
            print(f"⚠️ Error: {e}")
    
    # Pass 2: Fallback
    if not found_news:
        print("\n🔍 Pass 2: All categories allowed...")
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
    
    print("🤖 Generating AI content...")
    ai_content = generate_content_via_ai(title, full_content, category)
    if not ai_content:
        print("⚠️ AI generation failed. Using fallback template.")
        ai_content = fallback_long_content(title, full_content, category)
    
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
    
    actual_word_count = len(full_content.split()) + 200
    
    final_content = f"""
    {image_html}
    {ai_content}
    {earning_button}
    
    <hr style="border:0;border-top:2px solid #e0e0e0;margin:30px 0;">
    
    <div style="text-align:center;color:#999;font-size:14px;">
        <p>📅 Published: {datetime.now().strftime('%B %d, %Y')}</p>
        <p>📂 Category: {category}</p>
        <p>📝 Word Count: {actual_word_count} words</p>
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
        
        # SEO Pinging
        ping_search_engines("Viral News AI", post_url)
        
        # Social Sharing
        share_to_telegram(title, post_url)
        share_to_discord(title, post_url)
        
        print(f"\n📰 Title: {title}")
        print(f"📂 Category: {category}")
        print(f"🔗 Short Link: {short_link}")
        print(f"📝 Words: {actual_word_count}")
    else:
        print("❌ Failed to post!")

if __name__ == "__main__":
    main()
