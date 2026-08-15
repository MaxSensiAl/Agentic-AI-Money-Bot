import os
import json
import random
import time
import requests
import feedparser
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURATION (GitHub Secrets se data lena) ---
BLOG_ID = os.getenv('BLOG_ID')
SHRINKME_API = os.getenv('SHRINKME_API')
SERVICE_ACCOUNT_JSON = os.getenv('SERVICE_ACCOUNT_JSON')

# Hugging Face token GEMINI_API se lena hai (aapke workflow mein mapped hai)
HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('GEMINI_API')

# RSS Feeds (premium sources)
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
    """ShrinkMe API se link chhota karna"""
    try:
        if not SHRINKME_API:
            return long_url
        api_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={long_url}&format=text"
        response = requests.get(api_url, timeout=10)
        return response.text.strip() if response.text else long_url
    except:
        return long_url

def generate_ai_content(title, source_text):
    """Hugging Face API se article likhna"""
    if not HF_TOKEN:
        print("Error: HF_TOKEN is empty. Cannot write article.")
        return None

    prompt = f"""Write an 800-word SEO optimized professional news article in English about: {title}. 
Context: {source_text}. 
Format requirements: 
1. Use HTML tags like <h2>, <h3>, <p>, and <blockquote> 
2. Add a 'Key Highlights' section using <ul> <li> 
3. Make it human-like and engaging 
4. Include a disclaimer at the end"""

    # Hugging Face Inference API endpoint
    API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.95,
            "do_sample": True
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        # Agar model load ho raha hai
        if response.status_code == 503:
            print("Model is loading, waiting for 20 seconds...")
            time.sleep(20)
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            # Response format handle karna
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get('generated_text', '')
                if prompt in generated_text:
                    generated_text = generated_text.replace(prompt, '').strip()
                return generated_text
            elif isinstance(result, dict) and 'generated_text' in result:
                return result['generated_text'].strip()
            else:
                print(f"Unexpected response format: {result}")
                return None
        else:
            print(f"API Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("Request timeout - trying alternative endpoint...")
        return generate_ai_content_fallback(title, source_text)
    except requests.exceptions.ConnectionError:
        print("Connection error - trying alternative endpoint...")
        return generate_ai_content_fallback(title, source_text)
    except Exception as e:
        print(f"Hugging Face Error: {e}")
        return None

def generate_ai_content_fallback(title, source_text):
    """Fallback method using different model"""
    if not HF_TOKEN:
        return None

    prompt = f"Write a detailed news article about: {title}. Include HTML formatting with h2, h3, p tags."

    # Alternative endpoint - using Mistral model
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 800,
            "temperature": 0.7
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '').replace(prompt, '').strip()
        return None
    except:
        return None

def post_to_blogger(title, content):
    """Service Account se Blogger par post karna"""
    try:
        if not SERVICE_ACCOUNT_JSON:
            print("Error: SERVICE_ACCOUNT_JSON is missing!")
            return
            
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
        print(f"✅ Successfully Posted! URL: {posts.get('url')}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid SERVICE_ACCOUNT_JSON format: {e}")
        return False
    except Exception as e:
        print(f"❌ Blogger Error: {e}")
        return False

# --- MAIN LOGIC ---

def main():
    print("🤖 Starting the Robot...")
    
    # --- Checking GitHub Secrets ---
    print("\n--- Checking GitHub Secrets Status ---")
    print(f"BLOG_ID: {'✅ LOADED' if BLOG_ID else '❌ MISSING'}")
    print(f"HUGGING_FACE_TOKEN (via GEMINI_API): {'✅ LOADED' if HF_TOKEN else '❌ MISSING'}")
    print(f"SHRINKME_API: {'✅ LOADED' if SHRINKME_API else '❌ MISSING'}")
    print(f"SERVICE_ACCOUNT_JSON: {'✅ LOADED' if SERVICE_ACCOUNT_JSON else '❌ MISSING'}")
    print("--------------------------------------\n")
    
    # Agar kuch missing hai toh exit kar do
    if not all([BLOG_ID, HF_TOKEN, SERVICE_ACCOUNT_JSON]):
        print("❌ Required secrets missing. Exiting...")
        return
    
    random.shuffle(RSS_FEEDS)
    
    entry = None
    selected_feed_url = None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # Feed fetch karna
    for feed_url in RSS_FEEDS:
        print(f"Checking feed: {feed_url}")
        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                if feed.entries:
                    entry = random.choice(feed.entries)
                    selected_feed_url = feed_url
                    print(f"✅ Success! Found news in: {feed_url}")
                    break
                else:
                    print(f"❌ No entries found in: {feed_url}")
            else:
                print(f"❌ Failed to fetch {feed_url} - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error checking {feed_url}: {e}")

    if not entry:
        print("❌ No news found in any RSS feed!")
        return

    original_title = entry.title
    original_link = entry.link
    summary = entry.get('summary', 'Latest news update')

    print(f"\n📰 Processing: {original_title}")

    # Link shortener
    short_link = get_short_url(original_link)
    print(f"🔗 Shortened link: {short_link}")

    # AI content generation
    print("🤖 Generating AI content...")
    ai_article = generate_ai_content(original_title, summary)
    
    if ai_article:
        print("✅ Content generated successfully!")
        final_content = f"""{ai_article} 
<br><br> 
<strong>Source:</strong> <a href='{short_link}'>Read Full Story here</a>
<br><br>
<em>Disclaimer: This is an AI-generated summary and analysis. For complete information, please visit the original source.</em>"""
        
        print("📝 Posting to Blogger...")
        post_to_blogger(original_title, final_content)
    else:
        print("❌ Content generation failed.")
        # Fallback: simple post without AI content
        fallback_content = f"""
        <h2>{original_title}</h2>
        <p>{summary}</p>
        <br>
        <strong>Source:</strong> <a href='{short_link}'>Read Full Story here</a>
        """
        print("📝 Posting fallback content to Blogger...")
        post_to_blogger(original_title, fallback_content)

if __name__ == "__main__":
    main()
