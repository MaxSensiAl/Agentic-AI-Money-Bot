import os
import json
import random
import time
import requests
import feedparser
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURATION (GitHub Secrets से डेटा उठाना) ---
BLOG_ID = os.getenv('BLOG_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API')
SHRINKME_API = os.getenv('SHRINKME_API')
SERVICE_ACCOUNT_JSON = os.getenv('SERVICE_ACCOUNT_JSON')

# RSS Feeds की लिस्ट (प्रीमियम सोर्सेस)
RSS_FEEDS = [
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://www.variety.com/feed/",
    "https://www.pinkvilla.com/feed",
    "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "https://www.ign.com/rss/articles/all"
]

# --- FUNCTIONS ---

def get_short_url(long_url):
    """ShrinkMe API के जरिए लिंक छोटा करना"""
    try:
        api_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={long_url}&format=text"
        response = requests.get(api_url, timeout=10)
        return response.text.strip()
    except:
        return long_url

def generate_ai_content(title, source_text):
    """Gemini 1.5-Flash का उपयोग करके आर्टिकल लिखना"""
    prompt = f"""
    Write a 800-word SEO optimized professional news article about: {title}.
    Use the following information as context: {source_text}.
    
    Format requirements:
    1. Use HTML tags like <h2>, <h3>, <p>, and <blockquote>.
    2. Add a 'Key Highlights' section using <ul> <li>.
    3. Make it human-like and engaging.
    4. Include a disclaimer at the end.
    5. Write in English but keep the tone global.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None

def post_to_blogger(title, content):
    """Service Account का उपयोग करके Blogger पर पोस्ट करना"""
    try:
        # JSON स्ट्रिंग को डिक्शनरी में बदलना
        info = json.loads(SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=['https://www.googleapis.com/auth/blogger']
        )
        service = build('blogger', 'v3', credentials=creds)

        body = {
            "kind": "blogger#post",
            "title": title,
            "content": content
        }

        # isDraft=False मतलब पोस्ट सीधे LIVE होगी
        posts = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"Successfully Posted! URL: {posts.get('url')}")
    except Exception as e:
        print(f"Blogger Error: {e}")

# --- MAIN LOGIC ---

def main():
    print("Starting the Robot...")
    
    # 1. किसी एक रैंडम फीड से खबर उठाना
    feed_url = random.choice(RSS_FEEDS)
    feed = feedparser.parse(feed_url)
    
    if not feed.entries:
        print("No news found!")
        return

    entry = random.choice(feed.entries)
    original_title = entry.title
    original_link = entry.link
    summary = entry.get('summary', 'Latest news update')

    print(f"Processing: {original_title}")

    # 2. लिंक छोटा करना
    short_link = get_short_url(original_link)

    # 3. AI से आर्टिकल लिखवाना
    ai_article = generate_ai_content(original_title, summary)
    
    if ai_article:
        # आर्टिकल के अंत में छोटा किया हुआ लिंक जोड़ना
        final_content = f"{ai_article} <br><br> <strong>Source:</strong> <a href='{short_link}'>Read Full Story here</a>"
        
        # 4. ब्लॉगर पर पब्लिश करना
        post_to_blogger(original_title, final_content)
    else:
        print("Content generation failed.")

if __name__ == "__main__":
    main()
