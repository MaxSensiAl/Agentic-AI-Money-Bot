import os
import json
import random
import time
import requests
import feedparser
import re

# --- CONFIGURATION (GitHub Secrets से डेटा उठाना) ---
BLOG_ID = os.getenv('BLOG_ID').strip() if os.getenv('BLOG_ID') else None
SHRINKME_API = os.getenv('SHRINKME_API').strip() if os.getenv('SHRINKME_API') else None
SERVICE_ACCOUNT_JSON = os.getenv('SERVICE_ACCOUNT_JSON').strip() if os.getenv('SERVICE_ACCOUNT_JSON') else None

# स्मार्ट जुगाड़: हगिंग फेस टोकन को हम GEMINI_API से उठाएंगे क्योंकि यह वर्कफ़्लो में पहले से मैप है
HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('GEMINI_API')
if HF_TOKEN:
    HF_TOKEN = HF_TOKEN.strip()

# ब्लॉगर पर्सनल एडमिन क्रेडेंशियल्स (OAuth2)
BC_CLIENT_ID = os.getenv('BC_CLIENT_ID').strip() if os.getenv('BC_CLIENT_ID') else None
BC_CLIENT_SECRET = os.getenv('BC_CLIENT_SECRET').strip() if os.getenv('BC_CLIENT_SECRET') else None
BC_REFRESH_TOKEN = os.getenv('BC_REFRESH_TOKEN').strip() if os.getenv('BC_REFRESH_TOKEN') else None

# RSS Feeds
RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.variety.com/feed/",
    "https://www.pinkvilla.com/feed",
    "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "https://www.ign.com/rss/articles/all"
]

# --- FUNCTIONS ---

def get_entry_image(entry):
    """RSS फ़ीड की खबर से मुख्य इमेज का URL निकालना"""
    try:
        # 1. media_content चेक करें
        media_content = entry.get('media_content')
        if media_content and isinstance(media_content, list):
            for media in media_content:
                if 'url' in media:
                    return media['url']
        
        # 2. links में इमेज ढूंढें
        links = entry.get('links')
        if links:
            for link in links:
                if 'image' in link.get('type', ''):
                    return link.get('href')
        
        # 3. enclosures चेक करें
        enclosures = entry.get('enclosures')
        if enclosures:
            for enc in enclosures:
                if enc.get('type', '').startswith('image'):
                    return enc.get('href')
                    
        # 4. अगर summary/description में <img> टैग है, तो regex से निकालें
        summary = entry.get('summary', '')
        if 'src=' in summary:
            match = re.search(r'src=["\'](https?://[^"\']+)["\']', summary)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Image extraction warning: {e}")
    return None

def get_short_url(long_url):
    """ShrinkMe API के जरिए लिंक छोटा करना"""
    try:
        if not SHRINKME_API:
            return long_url
        api_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={long_url}&format=text"
        response = requests.get(api_url, timeout=10)
        return response.text.strip() if response.text else long_url
    except:
        return long_url

def generate_ai_content(title, source_text):
    """Hugging Face Inference API से article generate karna"""
    if not HF_TOKEN:
        print("❌ HF_TOKEN is empty")
        return None

    prompt = f"""Write a 400-word SEO optimized professional news article in English about: {title}. 
Context: {source_text[:500]}. 
Use HTML tags: <h2>, <h3>, <p>. Add Key Highlights with <ul><li>. Include a disclaimer at the end."""

    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 600,
            "temperature": 0.7,
            "do_sample": True
        }
    }
    
    try:
        print("⏳ Calling Hugging Face API...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=45)
        
        if response.status_code == 503:
            print("⏳ Model loading, waiting 25 seconds...")
            time.sleep(25)
            response = requests.post(API_URL, headers=headers, json=payload, timeout=45)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('generated_text', '')
                if prompt in text:
                    text = text.replace(prompt, '').strip()
                return text if len(text) > 50 else None
            elif isinstance(result, dict) and 'generated_text' in result:
                return result['generated_text'].strip()
        else:
            print(f"❌ API Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Hugging Face Error: {e} - trying fallback...")
        return None

def generate_ai_content_fallback(title, source_text, image_html):
    """Fallback using local simple article generation"""
    highlights = [
        f"• {title} - Major development in the industry",
        "• Key stakeholders are closely monitoring the situation",
        "• Industry experts weigh in on the implications",
        "• Public response has been significant"
    ]
    
    article = f"""
    {image_html}
    <h2>Breaking News: {title}</h2>
    
    <p>In a significant development today, {title} has captured the attention of industry observers worldwide. The announcement marks a pivotal moment in the ongoing evolution of technology and its impact on society.</p>
    
    <h3>Key Highlights</h3>
    <ul>
        {''.join([f'<li>{h}</li>' for h in highlights])}
    </ul>
    
    <h3>Detailed Analysis</h3>
    <p>{source_text[:300]}... [Full story continues]</p>
    
    <blockquote style="border-left: 5px solid #ff5722; padding-left: 15px; font-style: italic; color: #555; margin: 20px 0;">
    Industry analysts suggest that this development could reshape the competitive landscape and create new opportunities for innovation.
    </blockquote>
    """
    return article

def post_to_blogger(title, content):
    """Blogger Personal OAuth क्रेडेंशियल्स का उपयोग करके सीधे एडमिन अकाउंट से पोस्ट करना"""
    if not all([BC_CLIENT_ID, BC_CLIENT_SECRET, BC_REFRESH_TOKEN]):
        print("❌ Blogger OAuth Secrets missing.")
        return False
        
    try:
        # 1. Refresh Token से नया Access Token प्राप्त करना
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": BC_CLIENT_ID,
            "client_secret": BC_CLIENT_SECRET,
            "refresh_token": BC_REFRESH_TOKEN,
            "grant_type": "refresh_token"
        }
        res = requests.post(token_url, data=payload, timeout=15)
        res_json = res.json()
        
        if "access_token" not in res_json:
            print(f"❌ Failed to refresh Blogger token: {res_json}")
            return False
            
        access_token = res_json["access_token"]
        
        # 2. ब्लॉगर पर पोस्ट इंसर्ट करना (सीधे आपके एडमिन अकाउंट से!)
        post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        post_body = {
            "kind": "blogger#post",
            "title": title,
            "content": content,
            "labels": ["AI-generated", "News", "Automated"]
        }
        
        post_res = requests.post(post_url, headers=headers, json=post_body, timeout=20)
        
        if post_res.status_code in [200, 201]:
            result = post_res.json()
            print(f"✅ Successfully Posted!")
            print(f"🔗 URL: {result.get('url', 'N/A')}")
            return True
        else:
            print(f"❌ Blogger Post Failed - Status: {post_res.status_code}")
            print(post_res.text)
            return False
            
    except Exception as e:
        print(f"❌ Blogger OAuth Error: {e}")
        return False

def verify_blogger_permission():
    """Blogger Access Verify करना (OAuth2 का उपयोग करके)"""
    if not all([BC_CLIENT_ID, BC_CLIENT_SECRET, BC_REFRESH_TOKEN]):
        print("❌ Blogger OAuth Secrets missing in Verification.")
        return False
    try:
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": BC_CLIENT_ID,
            "client_secret": BC_CLIENT_SECRET,
            "refresh_token": BC_REFRESH_TOKEN,
            "grant_type": "refresh_token"
        }
        res = requests.post(token_url, data=payload, timeout=15)
        access_token = res.json().get("access_token")
        
        if not access_token:
            print("❌ Cannot retrieve access token for verification.")
            return False
            
        blog_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}"
        headers = {"Authorization": f"Bearer {access_token}"}
        blog_res = requests.get(blog_url, headers=headers, timeout=15)
        
        if blog_res.status_code == 200:
            print(f"✅ Blogger access verified! Blog: {blog_res.json().get('name')}")
            return True
        else:
            print(f"❌ Blog Verification Failed - Status: {blog_res.status_code}")
            return False
    except Exception as e:
        print(f"❌ Verification Error: {e}")
        return False

# --- MAIN LOGIC ---

def main():
    print("🤖 Starting the Robot...")
    
    # --- Checking GitHub Secrets ---
    print("\n--- Checking GitHub Secrets Status ---")
    print(f"BLOG_ID: {'✅ LOADED' if BLOG_ID else '❌ MISSING'}")
    print(f"BC_CLIENT_ID: {'✅ LOADED' if BC_CLIENT_ID else '❌ MISSING'}")
    print(f"BC_CLIENT_SECRET: {'✅ LOADED' if BC_CLIENT_SECRET else '❌ MISSING'}")
    print(f"BC_REFRESH_TOKEN: {'✅ LOADED' if BC_REFRESH_TOKEN else '❌ MISSING'}")
    print(f"HF_TOKEN: {'✅ LOADED' if HF_TOKEN else '❌ MISSING'}")
    print("--------------------------------------\n")
    
    # Verify required secrets
    required = [BLOG_ID, HF_TOKEN, BC_CLIENT_ID, BC_CLIENT_SECRET, BC_REFRESH_TOKEN]
    if not all(required):
        print("❌ Required secrets missing. Exiting...")
        return
    
    # Verify Blogger access first
    print("🔍 Verifying Blogger permissions...")
    if not verify_blogger_permission():
        print("❌ Cannot proceed. Blogger credentials are invalid or expired.")
        return
    
    # Shuffle feeds
    random.shuffle(RSS_FEEDS)
    
    entry = None
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # Find news from feeds
    for feed_url in RSS_FEEDS:
        print(f"\n🔍 Checking feed: {feed_url}")
        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                if feed.entries:
                    entry = random.choice(feed.entries)
                    print(f"✅ Found news in: {feed_url}")
                    break
                else:
                    print(f"❌ No entries found")
            else:
                print(f"❌ Failed - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

    if not entry:
        print("❌ No news found!")
        return

    # Process article
    title = entry.title
    link = entry.link
    summary = entry.get('summary', 'No summary available')

    print(f"\n📰 Processing: {title}")
    
    # Image extraction
    image_url = get_entry_image(entry)
    image_html = ""
    if image_url:
        print(f"📸 Image extracted successfully: {image_url}")
        image_html = f"<img src='{image_url}' style='width: 100%; max-height: 440px; object-fit: cover; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); margin-bottom: 25px;' alt='{title}'><br>"
    else:
        print("⚠️ No image found in RSS feed entry")
    
    # Shorten link (Earning Link)
    short_link = get_short_url(link)
    print(f"🔗 Short link: {short_link}")

    # Generate content
    print("🤖 Generating content...")
    ai_content = generate_ai_content(title, summary)
    
    # चमकदार अर्निंग बटन (Call to Action Button)
    earning_button_html = f"""
    <div style="text-align: center; margin: 35px 0;">
        <a href="{short_link}" target="_blank" style="background-color: #ff5722; color: white; padding: 14px 35px; text-decoration: none; font-size: 18px; font-weight: bold; border-radius: 30px; box-shadow: 0 5px 15px rgba(255,87,34,0.4); display: inline-block; transition: 0.3s; text-transform: uppercase;">👉 READ FULL STORY HERE 👈</a>
    </div>
    """

    if ai_content and len(ai_content) > 100:
        print("✅ Content generated successfully")
        # इमेज को सबसे ऊपर लगाना
        final_content = f"""{image_html}
        {ai_content}
        
        {earning_button_html}
        
        <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #888; font-size: 13px; font-style: italic; text-align: center;">🤖 This article was generated automatically. Some information may not be accurate. Please click the button above to refer to the original source.</p>"""
    else:
        print("⚠️ Using fallback content")
        fallback_content = generate_ai_content_fallback(title, summary, image_html)
        final_content = f"""{fallback_content}
        
        {earning_button_html}
        
        <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #888; font-size: 13px; font-style: italic; text-align: center;">⚠️ Auto-generated summary. Please click the button above to refer to the original source.</p>"""

    # Post to Blogger
    print("📝 Posting to Blogger...")
    if post_to_blogger(title, final_content):
        print("✅ Process completed successfully!")
    else:
        print("❌ Failed to post. Check logs above.")

if __name__ == "__main__":
    main()
