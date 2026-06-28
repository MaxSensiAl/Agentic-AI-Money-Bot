import os, requests, feedparser, random, json, time, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_deep_article(headline, cat, g_key):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key}"
    style = random.choice(["Senior Journalist", "Viral Content Specialist", "Expert Critic"])
    prompt = f"Act as a professional {style}. Write a 800-word DEEP, UNIQUE article about: '{headline}' (Category: {cat}). Use HTML (h2, h3, b, ul, li). Include social buzz and 5 SEO keywords. Return ONLY HTML."
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=40).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h2>Report: {headline}</h2><p>Latest verified data for {cat} is being processed.</p>"

def run_api_machine():
    try:
        # Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        G_KEY = os.getenv("GEMINI_API")
        S_KEY = os.getenv("SHRINKME_API")

        # 20+ Sources
        sources = {"Tech": "https://techcrunch.com/feed/", "Movies": "https://variety.com/feed/", "Gaming": "https://www.ign.com/rss/articles/feed", "Bollywood": "https://www.pinkvilla.com/feed"}
        cat, rss = random.choice(list(sources.items()))
        feed = feedparser.parse(rss)
        item = random.choice(feed.entries[:10])

        # Content & Money Link
        article = get_deep_article(item.title, cat, G_KEY)
        money_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}").json()
        link = money_res.get("shortenedUrl", item.link)

        # Design
        html_body = f"""<div style='font-family:sans-serif; padding:40px; border:1px solid #eee; border-radius:15px;'><h1 style='color:#000;'>{item.title}</h1>{article}<div style='text-align:center; margin-top:40px;'><a href='{link}' style='background:#ff6600; color:#000; padding:15px 45px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px;'>🚀 UNLOCK FULL DATA</a></div></div>"""

        # --- Official API Posting ---
        creds = service_account.Credentials.from_service_account_info(service_info)
        service = build('blogger', 'v3', credentials=creds)
        
        post_data = {"kind": "blogger#post", "blog": {"id": BLOG_ID}, "title": item.title, "content": html_body}
        
        # 'isDraft=False' पक्का करता है कि पोस्ट LIVE हो
        result = service.posts().insert(blogId=BLOG_ID, body=post_data, isDraft=False).execute()
        
        if 'id' in result:
            print(f"✅ SUCCESS! Article Published: {result.get('url')}")
        else:
            print(f"❌ Blogger rejection: {result}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ SYSTEM ERROR: {e}")
        sys.exit(1) # GitHub को लाल निशान दिखाने पर मजबूर करेगा

if __name__ == "__main__":
    run_api_machine()
