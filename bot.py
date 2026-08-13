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
    """Gemini 1.5-Flash का उपयोग करके आर्टिकल लिखना (v1 API का उपयोग)"""
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
    
    # यहाँ URL में v1beta की जगह v1 का उपयोग किया गया है
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        
        # अगर 'candidates' मौजूद है, तो टेक्स्ट वापस करें
        if 'candidates' in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            # अगर एरर है, तो पूरा रिस्पांस प्रिंट करें
            print("Gemini API Error Response:")
            print(json.dumps(res_json, indent=2))
            return None
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
    
    # फ़ीड्स को रैंडम क्रम में मिक्स करना ताकि हर बार अलग फ़ीड पहले चेक हो
    random.shuffle(RSS_FEEDS)
    
    entry = None
    selected_feed_url = None

    # असली ब्राउज़र जैसा हेडर (ताकि वेबसाइट्स ब्लॉक न करें)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # सभी फ़ीड्स को एक-एक करके चेक करना
    for feed_url in RSS_FEEDS:
        print(f"Checking feed: {feed_url}")
        try:
            # यूजर-एजेंट के साथ रिक्वेस्ट भेजना
            response = requests.get(feed_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                if feed.entries:
                    entry = random.choice(feed.entries)
                    selected_feed_url = feed_url
                    print(f"Success! Found news in: {feed_url}")
                    break  # खबर मिल गई, अब लूप से बाहर निकलें
                else:
                    print(f"Feed parsed but no entries found in: {feed_url}")
            else:
                print(f"Failed to fetch {feed_url} - Status Code: {response.status_code}")
                
        except Exception as e:
            print(f"Error checking {feed_url}: {e}")

    # अगर किसी भी फ़ीड से खबर नहीं मिली
    if not entry:
        print("No news found in any of the RSS feeds!")
        return

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
