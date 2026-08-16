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

# --- POSTED NEWS TRACKING ---
POSTED_FILE = 'posted_news.txt'

def clean_and_format_title(title):
    if not title:
        return ""
    clean = re.sub(r'\s+', ' ', title).strip()
    clean = re.sub(r'202[0-9]\s*[-|]\s*202[0-9]', '', clean)
    clean = re.sub(r'\s*[-|]\s*$', '', clean)
    # Title cut-off boundary check to prevent words like "into" becoming "int"
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
        # Removed requests.head checking to prevent broken image errors
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
    if any(x in title_lower for x in ["spider-man", "movie", "film", "hollywood", "box office", "marvel", "dc", "drag race", "rupaul", "series", "episode"]):
        return "Entertainment"
    if "space" in feed_lower or "nasa" in feed_lower:
        return "Space"
    if any(x in feed_lower for x in ["tech", "verge", "cnet"]):
        return "Technology"
    if any(x in feed_lower for x in ["gamespot", "ign"]):
        return "Gaming"
    if any(x in feed_lower for x in ["rollingstone"]):
        return "Music"
    if "cric" in feed_lower or any(x in title_lower for x in ["cricket", "century", "wicket", "odi", "test", "match", "football", "goal"]):
        return "Sports"
    if any(x in feed_lower for x in ["bloomberg", "reuters"]):
        return "Business"
    
    return "News"

# --- DYNAMIC AI GENERATION USING HUGGING FACE ---
def generate_content_via_ai(title, full_content, category):
    if not HF_TOKEN:
        print("⚠️ HF_TOKEN is missing! Using static fallback.")
        return None
    
    print("🧠 Contacting Hugging Face Meta-Llama API...")
    api_url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    
    system_prompt = """You are "Viral News AI", an advanced, highly professional SEO-friendly Hinglish content generator.
Instructions:
1. No incomplete words (never write "Seaso", always write "Seasons").
2. Do not use double bullet points. Use single (•) bullet points only.
3. Absolutely NO generic filler text. Generate real, factual summaries.
4. For Sports: Never use business terms like "Industry Impact" or "Consumer Reaction". Use "Match Analysis" and "Fans' Reaction".
5. For Space/History: Do not treat old events as live breaking news.
6. Return content only in the requested HTML format."""

    user_prompt = f"""Generate a detailed Hinglish (Hindi + English) blog post for:
Title: {title}
Category: {category}
Reference Content: {full_content[:1500]}

Generate the output exactly in this HTML structure:
<h3>📝 परिचय - Introduction</h3>
[1 Paragraph in English, followed by 1 Paragraph in Hindi]

<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>
  <li>[Point 1 with emoji]</li>
  <li>[Point 2 with emoji]</li>
  <li>[Point 3 with emoji]</li>
  <li>[Point 4 with emoji]</li>
</ul>

<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
[Detailed analysis paragraph in English, followed by detailed translation in Hindi]

<h3>💬 विशेषज्ञों की राय - Expert Opinions</h3>
[Opinions in English and Hindi]
<blockquote style="border-left:5px solid #ff5722;padding:20px;background:#f9f9f9;border-radius:8px;margin:20px 0;">
    <p style="font-style:italic;font-size:16px;">"[A context-specific quote in Hindi/English]"</p>
</blockquote>

<h3>🌍 प्रभाव और आगे क्या? - Impact & What's Next</h3>
[Impact & future details in English and Hindi]

<h3>✅ निष्कर्ष - Conclusion</h3>
[Conclusion in English and Hindi]
"""

    payload = {
        "inputs": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
        "parameters": {"max_new_tokens": 1000, "temperature": 0.7}
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('generated_text', '')
                if "<|start_header_id|>assistant<|end_header_id|>\n\n" in text:
                    text = text.split("<|start_header_id|>assistant<|end_header_id|>\n\n")[-1]
                return text.strip()
    except Exception as e:
        print(f"⚠️ AI API Error: {e}")
    return None

# --- FALLBACK STATIC TEMPLATES (ONLY IF AI API FAILS) ---
def fallback_long_content(title, full_content, category):
    today = datetime.now().strftime("%B %d, %Y")
    clean_title = clean_and_format_title(title)
    first_para = full_content[:400] if full_content else ""
    
    highlights = [
        f"<li><strong>🔴 मुख्य खबर:</strong> {clean_title[:50]}</li>",
        f"<li><strong>📂 Category:</strong> {category}</li>",
        f"<li><strong>📊 विश्लेषण:</strong> विशेषज्ञों की राय</li>",
        f"<li><strong>🔮 आगे क्या:</strong> आने वाले अपडेट</li>",
    ]
    
    intro = f"""
<p>{clean_title}. This is the latest news in the {category} sector.</p>
<p>{clean_title} - यह आज की {category} सेक्टर की बड़ी खबर है।</p>
"""
    return f"""
<h2>🚨 BREAKING NEWS: {clean_title}</h2>
<div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:15px 0;">
    <p><strong>📅 Published: {today}</strong></p>
    <p><strong>📂 Category: {category}</strong></p>
</div>
<h3>📝 परिचय - Introduction</h3>
{intro}
<h3>🎯 मुख्य बातें - Key Highlights</h3>
<ul>{''.join(highlights)}</ul>
<h3>📊 विस्तृत विश्लेषण - Detailed Analysis</h3>
<p>{first_para}</p>
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
    
    print("🤖 Generating content via AI...")
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
    
    actual_word_count = len(full_content.split()) + 150
    
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
    if post_to_blogger(access_token, title, final_content, category):
        save_posted_news(title)
        print("\n✅✅✅ COMPLETED SUCCESSFULLY! ✅✅✅")
        print(f"📰 Title: {title}")
        print(f"📂 Category: {category}")
        print(f"🖼️ Image: ✅ HD Quality")
        print(f"🔗 Short Link: {short_link}")
        print(f"📝 Words: {actual_word_count}")
    else:
        print("❌ Failed to post!")

if __name__ == "__main__":
    main()
