import os
import json
import random
import time
import requests
import feedparser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# --- CONFIGURATION (GitHub Secrets से डेटा उठाना) ---
BLOG_ID = os.getenv('BLOG_ID').strip() if os.getenv('BLOG_ID') else None
SHRINKME_API = os.getenv('SHRINKME_API').strip() if os.getenv('SHRINKME_API') else None
SERVICE_ACCOUNT_JSON = os.getenv('SERVICE_ACCOUNT_JSON').strip() if os.getenv('SERVICE_ACCOUNT_JSON') else None

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
    """Google Service Account का उपयोग करके सीधे Gemini API को अधिकृत रूप से कॉल करना (मास्टर स्कोप के साथ)"""
    if not SERVICE_ACCOUNT_JSON:
        print("Error: SERVICE_ACCOUNT_JSON is empty. Cannot generate token.")
        return None

    try:
        # सर्विस अकाउंट JSON से क्रेडेंशियल्स लोड करना
        info = json.loads(SERVICE_ACCOUNT_JSON)
        
        # यहाँ स्कोप को बदलकर मास्टर स्कोप 'cloud-platform' किया गया है ताकि 100% वर्किंग एक्सेस टोकन मिले
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        # गूगल ऑथ ट्रांसपोर्ट का उपयोग करके लाइव ऑथेंटिकेशन टोकन जनरेट करना
        auth_req = Request()
        creds.refresh(auth_req)
        sa_token = creds.token
        
        if not sa_token:
            print("Error: Failed to generate Service Account token.")
            return None
    except Exception as e:
        print(f"Service Account Token Error: {e}")
        return None

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
    
    # सर्विस अकाउंट टोकन के लिए सीधा सुरक्षित एंडपॉइंट
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
    
    # टोकन को सुरक्षित Bearer Header के रूप में भेजना
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {sa_token}'
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        res_json = response.json()
        
        # सफल रिस्पांस मिलने पर
        if 'candidates' in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            print("Gemini API (Service Account) Error Response:")
            print(json.dumps(res_json, indent=2))
            return None
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None

def post_to_blogger(title, content):
    """Service Account का उपयोग करके Blogger पर पोस्ट करना"""
    try:
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

        posts = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
        print(f"Successfully Posted! URL: {posts.get('url')}")
    except Exception as e:
        print(f"Blogger Error: {e}")

# --- MAIN LOGIC ---

def main():
    print("Starting the Robot...")
    
    # --- क्रेडेंशियल डायग्नोस्टिक चेक ---
    print("\n--- Checking GitHub Secrets Status ---")
    print(f"BLOG_ID: {'LOADED (OK)' if BLOG_ID else 'MISSING ❌'}")
    print(f"SERVICE_ACCOUNT_JSON: {'LOADED (OK)' if SERVICE_ACCOUNT_JSON else 'MISSING ❌'}")
    print(f"SHRINKME_API: {'LOADED (OK)' if SHRINKME_API else 'MISSING ❌'}")
    print("--------------------------------------\n")
    
    random.shuffle(RSS_FEEDS)
    
    entry = None
    selected_feed_url = None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for feed_url in RSS_FEEDS:
        print(f"Checking feed: {feed_url}")
        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                feed = parser = feedparser.parse(response.content)
                if feed.entries:
                    entry = random.choice(feed.entries)
                    selected_feed_url = feed_url
                    print(f"Success! Found news in: {feed_url}")
                    break
                else:
                    print(f"Feed parsed but no entries found in: {feed_url}")
            else:
                print(f"Failed to fetch {feed_url} - Status Code: {response.status_code}")
                
        except Exception as e:
            print(f"Error checking {feed_url}: {e}")

    if not entry:
        print("No news found in any of the RSS feeds!")
        return

    original_title = entry.title
    original_link = entry.link
    summary = entry.get('summary', 'Latest news update')

    print(f"Processing: {original_title}")

    short_link = get_short_url(original_link)

    ai_article = generate_ai_content(original_title, summary)
    
    if ai_article:
        final_content = f"{ai_article} <br><br> <strong>Source:</strong> <a href='{short_link}'>Read Full Story here</a>"
        post_to_blogger(original_title, final_content)
    else:
        print("Content generation failed.")

if __name__ == "__main__":
    main()
