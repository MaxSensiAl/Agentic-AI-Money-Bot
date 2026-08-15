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

# Hugging Face token
HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('GEMINI_API')

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
    """Hugging Face Inference API se article generate karna"""
    if not HF_TOKEN:
        print("❌ HF_TOKEN is empty")
        return None

    # Simplified prompt for better response
    prompt = f"""Write a 400-word SEO optimized professional news article in English about: {title}. 
Context: {source_text[:500]}. 
Use HTML tags: <h2>, <h3>, <p>. Add Key Highlights with <ul><li>. Include a disclaimer at the end."""

    # Using Hugging Face official inference endpoint
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
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - trying fallback...")
        return generate_ai_content_fallback(title, source_text)
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def generate_ai_content_fallback(title, source_text):
    """Fallback using local simple article generation"""
    # Simple template-based article when API fails
    highlights = [
        f"• {title} - Major development in the tech industry",
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
    """Blogger API se post karna - with proper OAuth handling"""
    try:
        if not SERVICE_ACCOUNT_JSON:
            print("❌ SERVICE_ACCOUNT_JSON missing")
            return False
            
        # Service account credentials load
        info = json.loads(SERVICE_ACCOUNT_JSON)
        
        # Create credentials
        creds = service_account.Credentials.from_service_account_info(
            info, 
            scopes=['https://www.googleapis.com/auth/blogger']
        )
        
        # Build service
        service = build('blogger', 'v3', credentials=creds)
        
        # Prepare post body
        post_body = {
            "kind": "blogger#post",
            "title": title,
            "content": content,
            "labels": ["AI-generated", "News", "Automated"]
        }
        
        # Insert post
        result = service.posts().insert(
            blogId=BLOG_ID,
            body=post_body,
            isDraft=False
        ).execute()
        
        print(f"✅ Successfully Posted!")
        print(f"📝 Title: {title}")
        print(f"🔗 URL: {result.get('url', 'N/A')}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in SERVICE_ACCOUNT_JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Blogger Error: {e}")
        print("💡 Make sure:")
        print("  1. Service account email is added as admin in Blogger")
        print("  2. Blog ID is correct")
        print("  3. Blogger API is enabled in Google Cloud Console")
        return False

def verify_blogger_permission():
    """Service account access verify karna"""
    try:
        info = json.loads(SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(
            info, 
            scopes=['https://www.googleapis.com/auth/blogger']
        )
        service = build('blogger', 'v3', credentials=creds)
        
        # Try to get blog info to verify access
        blog = service.blogs().get(blogId=BLOG_ID).execute()
        print(f"✅ Blogger access verified!")
        print(f"📝 Blog: {blog.get('name')}")
        return True
    except Exception as e:
        print(f"❌ Cannot access Blogger: {e}")
        return False

# --- MAIN LOGIC ---

def main():
    print("🤖 Starting the Robot...")
    
    # --- Checking GitHub Secrets ---
    print("\n--- Checking GitHub Secrets Status ---")
    print(f"BLOG_ID: {'✅ LOADED' if BLOG_ID else '❌ MISSING'}")
    print(f"HF_TOKEN: {'✅ LOADED' if HF_TOKEN else '❌ MISSING'}")
    print(f"SHRINKME_API: {'✅ LOADED' if SHRINKME_API else '❌ MISSING'}")
    print(f"SERVICE_ACCOUNT_JSON: {'✅ LOADED' if SERVICE_ACCOUNT_JSON else '❌ MISSING'}")
    print("--------------------------------------\n")
    
    # Verify required secrets
    required = [BLOG_ID, HF_TOKEN, SERVICE_ACCOUNT_JSON]
    if not all(required):
        print("❌ Required secrets missing. Exiting...")
        return
    
    # Verify Blogger access first
    print("🔍 Verifying Blogger permissions...")
    if not verify_blogger_permission():
        print("❌ Cannot proceed. Fix Blogger permissions first.")
        print("\n📌 Steps to fix:")
        print("1. Go to your Blogger blog → Settings → Permissions")
        print("2. Add your service account email as an 'Admin'")
        print("3. The email is in your SERVICE_ACCOUNT_JSON under 'client_email'")
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
