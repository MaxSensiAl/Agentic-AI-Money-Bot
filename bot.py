import os, requests, feedparser, random, json, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_ai_content(headline, cat):
    # तकनीक: OpenRouter (यह कभी 404 एरर नहीं देता)
    api_key = os.getenv("OPENROUTER_API_KEY")
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    prompt = f"Write a 600-word professional news article about: '{headline}' for category {cat}. Use HTML tags (h2, h3, b, ul). Return ONLY HTML body."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "meta-llama/llama-3-8b-instruct:free", # 100% फ्री मॉडल
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=30).json()
        return res['choices'][0]['message']['content']
    except:
        # बैकअप: Hugging Face
        return f"<h2>Update: {headline}</h2><p>Latest verified reports for {cat} are emerging. Our team is tracking the full story.</p>"

def run_viral_machine():
    try:
        # 1. Secrets को लोड और चेक करना
        service_json = os.getenv("SERVICE_ACCOUNT_JSON")
        BLOG_ID = os.getenv("BLOG_ID", "").strip()
        S_KEY = os.getenv("SHRINKME_API")

        print(f"📡 Using Blog ID: {BLOG_ID}")

        # 2. ताज़ा न्यूज़ (YouTube + Tech)
        sources = ["https://variety.com/feed/", "https://techcrunch.com/feed/", "https://www.ign.com/rss/articles/feed"]
        feed = feedparser.parse(random.choice(sources))
        item = random.choice(feed.entries[:5])

        # 3. AI Article & Money Link
        article = get_ai_content(item.title, "Trending")
        money_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}").json()
        link = money_res.get("shortenedUrl", item.link)

        # 4. Agentic AI डिज़ाइन
        image_url = f"https://loremflickr.com/800/450/news?lock={random.randint(1,999)}"
        html_body = f"""<div style='font-family:sans-serif; padding:30px; border:1px solid #eee; border-radius:15px;'><img src='{image_url}' style='width:100%; border-bottom:5px solid #ff6600;'><h1 style='color:#000;'>{item.title}</h1>{article}<div style='text-align:center; margin-top:40px;'><a href='{link}' style='background:#ff6600; color:#000; padding:15px 40px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block;'>🚀 UNLOCK FULL DATA</a></div></div>"""

        # 5. Official Posting
        service_info = json.loads(service_json)
        creds = service_account.Credentials.from_service_account_info(service_info)
        scoped_creds = creds.with_scopes(['https://www.googleapis.com/auth/blogger'])
        service = build('blogger', 'v3', credentials=scoped_creds)
        
        # 'isDraft=True' करेंगे ताकि कम से कम पोस्ट ब्लॉगर के अंदर पहुँच जाए
        service.posts().insert(blogId=BLOG_ID, body={"title": item.title, "content": html_body}, isDraft=True).execute()
        print(f"✅ SUCCESS! Article saved in Drafts: {item.title}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_viral_machine()
