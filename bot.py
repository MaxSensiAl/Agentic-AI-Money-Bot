import os
import json
import random
import time
import requests
import feedparser
import subprocess
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURATION (GitHub Secrets से डेटा उठाना) ---
BLOG_ID = os.getenv('BLOG_ID').strip() if os.getenv('BLOG_ID') else None
SHRINKME_API = os.getenv('SHRINKME_API').strip() if os.getenv('SHRINKME_API') else None
SERVICE_ACCOUNT_JSON = os.getenv('SERVICE_ACCOUNT_JSON').strip() if os.getenv('SERVICE_ACCOUNT_JSON') else None

# स्मार्ट जुगाड़: हगिंग फेस टोकन को हम GEMINI_API से उठाएंगे क्योंकि यह वर्कफ़्लो में पहले से मैप है
HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('GEMINI_API')
if HF_TOKEN:
    HF_TOKEN = HF_TOKEN.strip()

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

def resolve_dns_via_cloudflare(domain):
    """1.1.1.1 (Cloudflare DNS-over-HTTPS) का उपयोग करके डोमेन का असली और ताज़ा AWS IP निकालना"""
    url = f"https://1.1.1.1/dns-query?name={domain}&type=A"
    headers = {"accept": "application/dns-json"}
    try:
        # 1.1.1.1 सीधे आईपी है, इसलिए यह बिना किसी DNS एरर के तुरंत काम करेगा
        response = requests.get(url, headers=headers, timeout=10)
        res_json = response.json()
        if "Answer" in res_json:
            for answer in res_json["Answer"]:
                if answer.get("type") == 1:
                    ip = answer.get("data")
                    print(f"Cloudflare 1.1.1.1 Resolved {domain} to {ip} 🌐")
                    return ip
    except Exception as e:
        print(f"Cloudflare DoH Resolution failed: {e}")
    return None

def get_short_url(long_url):
    """ShrinkMe API के जरिए लिंक छोटा करना"""
    try:
        api_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={long_url}&format=text"
        response = requests.get(api_url, timeout=10)
        return response.text.strip()
    except:
        return long_url

def generate_ai_content(title, source_text):
    """Hugging Face API (Qwen 2.5 7B Super-Fast) का उपयोग करके आर्टिकल लिखना"""
    if not HF_TOKEN:
        print("Error: HF_TOKEN is empty. Cannot write article.")
        return None

    prompt = f"Write a 800-word SEO optimized professional news article in English about: {title}. Context: {source_text}. Format requirements: 1. Use HTML tags like <h2>, <h3>, <p>, and <blockquote>. 2. Add a 'Key Highlights' section using <ul> <li>. 3. Make it human-like and engaging. 4. Include a disclaimer at the end."
    
    url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
    
    # 1. 1.1.1.1 के ज़रिए हगिंग फेस का ताजा और असली AWS IP लाइव निकालें
    hf_ip = resolve_dns_via_cloudflare("api-inference.huggingface.co")
    resolve_arg = None
    
    if hf_ip:
        # cURL को निर्देश दें कि वह सिस्टम DNS को बाईपास करके सीधे इस ताज़ा AWS IP पर जाए
        resolve_arg = f"api-inference.huggingface.co:443:{hf_ip}"
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.7
        }
    }
    
    payload_str = json.dumps(payload)
    
    # 3 बार ऑटो-रिट्राय लूप
    for attempt in range(3):
        print(f"Hugging Face API Call via cURL with 1.1.1.1 Resolve - Attempt {attempt + 1}/3...")
        try:
            cmd = [
                "curl", "-sS", "-X", "POST",
                "-H", f"Authorization: Bearer {HF_TOKEN}",
                "-H", "Content-Type: application/json"
            ]
            
            # यदि 1.1.1.1 से लाइव आईपी मिल गया है, तो उसे यहाँ जोड़ें
            if resolve_arg:
                cmd.extend(["--resolve", resolve_arg])
                
            cmd.extend(["-d", payload_str, url])
            
            # कमांड रन करना
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            response_text = result.stdout
            
            if not response_text:
                print(f"Empty response from curl. stderr: {result.stderr}")
                continue
                
            res_json = json.loads(response_text)
            
            # यदि हडिंग फेस का मॉडल बैकग्राउंड में अभी लोड हो रहा हो
            if isinstance(res_json, dict) and "error" in res_json and "loading" in res_json["error"].lower():
                wait_time = res_json.get("estimated_time", 20.0)
                print(f"Model is currently loading. Waiting for {wait_time} seconds before retrying...")
                time.sleep(wait_time)
                continue  # अगली कोशिश करें

            # सफल रिस्पांस मिलने पर
            if isinstance(res_json, list) and len(res_json) > 0 and 'generated_text' in res_json[0]:
                raw_text = res_json[0]['generated_text']
                if prompt in raw_text:
                    raw_text = raw_text.replace(prompt, "")
                return raw_text.strip()
            elif isinstance(res_json, dict) and 'generated_text' in res_json:
                return res_json['generated_text'].strip()
            else:
                print(f"Hugging Face response format mismatch: {res_json}")
                
        except Exception as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
        
        if attempt < 2:
            print("Waiting 5 seconds before next attempt...")
            time.sleep(5)
            
    print("All attempts failed.")
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
    print(f"HUGGING_FACE_TOKEN (via GEMINI_API): {'LOADED (OK)' if HF_TOKEN else 'MISSING ❌'}")
    print(f"SHRINKME_API: {'LOADED (OK)' if SHRINKME_API else 'MISSING ❌'}")
    print(f"SERVICE_ACCOUNT_JSON: {'LOADED (OK)' if SERVICE_ACCOUNT_JSON else 'MISSING ❌'}")
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
