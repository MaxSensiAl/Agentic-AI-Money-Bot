import os
import json
import random
import time
import requests
import feedparser

# --- CONFIGURATION (GitHub Secrets से डेटा उठाना) ---
BLOG_ID = os.getenv('BLOG_ID').strip() if os.getenv('BLOG_ID') else None
SHRINKME_API = os.getenv('SHRINKME_API').strip() if os.getenv('SHRINKME_API') else None
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

    prompt = f"Write a 400-word SEO optimized professional news article in English about: {title}. Context: {source_text[:500]}. Use HTML tags: <h2>, <h3>, <p>. Add Key Highlights with <ul><li>. Include a disclaimer at the end."

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
        return generate_ai_content_fallback(title, source_text)

def generate_ai_content_fallback(title, source_text):
    """Fallback using local simple article generation"""
    highlights = [
        f"• {title} - Major development in the industry",
        "• Key stakeholders are closely monitoring the situation",
        "• Industry experts weigh in on the implications",
        "• Public response has been significant"
    ]
    
    article = f"""
    <h2>Breaking News: {title}</h2>
    
    <p>In a significant development today, {title} has captured the attention of industry observers worldwide. The announcement marks a pivotal moment in the ongoing evolution of technology and its impact on society.</p>
    
    <h3>Key Highlights</h3>
    <ul>
        {''.join([f'<li>{h}</li>' for h in highlights])}
    </ul>
    
    <h3>Detailed Analysis</h3>
    <p>{source_text[:300]}... [Full story continues]</p>
    
    <blockquote>
    Industry analysts suggest that this development could reshape the competitive landscape and create new opportunities for innovation.
    </blockquote>
    
    <p><em>Disclaimer: This is an AI-generated summary. For complete details, please refer to the original source.</em></p>
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
    """Blogger Access Verify करना (सटीक एरर ट्रैकर के साथ)"""
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
        res_json = res.json()
        
        # यदि रिफ्रेश फेल होता है, तो पूरा गूगल का एरर रिस्पॉन्स प्रिंट करें
        if "access_token" not in res_json:
            print("❌ Cannot retrieve access token for verification.")
            print("Google Token Server Error Response:")
            print(json.dumps(res_json, indent=2))
            return False
            
        access_token = res_json["access_token"]
        
        blog_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}"
        headers = {"Authorization": f"Bearer {access_token}"}
        blog_res = requests.get(blog_url, headers=headers, timeout=15)
        
        if blog_res.status_code == 200:
            print(f"✅ Blogger access verified! Blog: {blog_res.json().get('name')}")
            return True
        else:
            print(f"❌ Blog Verification Failed - Status: {blog_res.status_code}")
            print(blog_res.text)
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
    
    # Shorten link
    short_link = get_short_url(link)
    print(f"🔗 Short link: {short_link}")

    # Generate content
    print("🤖 Generating content...")
    ai_content = generate_ai_content(title, summary)
    
    if ai_content and len(ai_content) > 100:
        print("✅ Content generated successfully")
        final_content = f"""{ai_content}
        
<br><br>
<strong>📌 Source:</strong> <a href='{short_link}' target='_blank'>Read Original Story</a>
<br>
<hr>
<p><em>🤖 This article was generated automatically. Some information may not be accurate. Please refer to the original source for complete details.</em></p>"""
    else:
        print("⚠️ Using fallback content")
        final_content = f"""
        <h2>{title}</h2>
        <p>{summary}</p>
        <br>
        <strong>📌 Source:</strong> <a href='{short_link}' target='_blank'>Read Original Story</a>
        <br><br>
        <em>⚠️ Auto-generated summary - Please visit the original source for complete information.</em>
        """

    # Post to Blogger
    print("📝 Posting to Blogger...")
    if post_to_blogger(title, final_content):
        print("✅ Process completed successfully!")
    else:
        print("❌ Failed to post. Check logs above.")

if __name__ == "__main__":
    main()
