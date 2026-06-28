import os, requests, feedparser, random, json, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

def get_ai_article(headline, cat, g_key):
    """AI से आर्टिकल लिखवाना - एरर हैंडलिंग के साथ"""
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"Act as a professional journalist. Write a deep 600-word news story about: '{headline}' in category {cat}. Use HTML tags (h2, h3, b, ul). Return ONLY HTML."
    
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=40).json()
        # 'candidates' चेक करना
        if 'candidates' in res and res['candidates'][0].get('content'):
            return res['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"⚠️ Gemini Safety Block or Error: {res}")
            return f"<h2>Breaking News: {headline}</h2><p>Latest verified reports on {cat} are emerging. Check back for the full deep-dive investigation.</p>"
    except Exception as e:
        print(f"⚠️ AI Request Failed: {e}")
        return f"<h2>News Alert: {headline}</h2><p>Global trends are shifting. Read the full official report via the link below.</p>"

def run_viral_machine():
    try:
        print(f"🚀 Initializing Machine v29.0 at {datetime.now()}")
        
        # 1. Secrets लोड करना
        service_json = os.getenv("SERVICE_ACCOUNT_JSON")
        if not service_json: raise ValueError("SERVICE_ACCOUNT_JSON is missing!")
        
        service_info = json.loads(service_json)
        BLOG_ID = os.getenv("BLOG_ID", "").strip()
        G_KEY = os.getenv("GEMINI_API")
        S_KEY = os.getenv("SHRINKME_API")

        # 2. 20+ रैंडम सोर्सेस
        sources = {
            "YouTube India": "https://news.google.com/rss/search?q=trending+on+youtube+india&hl=en-IN&gl=IN&ceid=IN:en",
            "Tech Trends": "https://techcrunch.com/feed/",
            "Hollywood": "https://variety.com/feed/",
            "Gaming": "https://www.ign.com/rss/articles/feed",
            "Bollywood": "https://www.pinkvilla.com/feed"
        }
        cat, rss = random.choice(list(sources.items()))
        feed = feedparser.parse(rss)
        if not feed.entries: return
        item = random.choice(feed.entries[:10])
        print(f"📡 News Found: {item.title} | Category: {cat}")

        # 3. Content & Money Link
        article = get_ai_article(item.title, cat, G_KEY)
        rand_id = random.randint(1000, 9999)
        image_url = f"https://loremflickr.com/800/450/news,tech,movie?lock={rand_id}"
        
        try:
            money_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}").json()
            money_link = money_res.get("shortenedUrl", item.link)
        except:
            money_link = item.link

        # 4. Agentic AI डिज़ाइन
        html_body = f"""<div style='font-family:sans-serif; max-width:800px; margin:auto; background:#fff; border:1px solid #eee; border-radius:15px; overflow:hidden;'>
            <img src='{image_url}' style='width:100%; border-bottom:5px solid #ff6600;'>
            <div style='padding:40px;'>
                <h1 style='color:#000; font-weight:900;'>{item.title}</h1>
                <div style='color:#444; line-height:1.9;'>{article}</div>
                <div style='text-align:center; margin-top:40px; background:#000; padding:40px; border-radius:15px;'>
                    <a href='{money_link}' style='background:#ff6600; color:#000; padding:15px 45px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block;'>🚀 UNLOCK DATA NOW</a>
                </div>
            </div>
        </div>"""

        # 5. Official API Posting
        creds = service_account.Credentials.from_service_account_info(service_info)
        # सही Scope का इस्तेमाल करना
        scoped_creds = creds.with_scopes(['https://www.googleapis.com/auth/blogger'])
        service = build('blogger', 'v3', credentials=scoped_creds)
        
        post_data = {"kind": "blogger#post", "blog": {"id": BLOG_ID}, "title": item.title, "content": html_body}
        
        # पक्का करना कि पोस्ट Draft में न जाए
        result = service.posts().insert(blogId=BLOG_ID, body=post_data, isDraft=False).execute()
        print(f"✅ SUCCESS! Post Live: {result.get('url')}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_viral_machine()
