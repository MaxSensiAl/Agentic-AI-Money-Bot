import os, requests, feedparser, random, json, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

def run_api_machine():
    try:
        # 1. Secrets को साफ़ करना
        service_json = os.getenv("SERVICE_ACCOUNT_JSON")
        service_info = json.loads(service_json)
        BLOG_ID = os.getenv("BLOG_ID").strip() 
        G_KEY = os.getenv("GEMINI_API")
        S_KEY = os.getenv("SHRINKME_API")

        # 2. ताज़ा कंटेंट (20+ Categories)
        sources = ["https://variety.com/feed/", "https://techcrunch.com/feed/", "https://www.ign.com/rss/articles/feed"]
        feed = feedparser.parse(random.choice(sources))
        item = random.choice(feed.entries[:5])
        
        # AI Content
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={G_KEY}"
        prompt = f"Write a 800-word deep news story about: '{item.title}'. Use professional HTML (h2, h3, b, ul). Return ONLY HTML."
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}).json()
        article = res['candidates'][0]['content']['parts'][0]['text']
        
        # Money Link
        money_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}").json()
        link = money_res.get("shortenedUrl", item.link)

        # 3. प्रीमियम डिज़ाइन
        html_body = f"""<div style='font-family:sans-serif; padding:40px; border:1px solid #eee; border-radius:15px;'><h1 style='color:#000; font-weight:900;'>{item.title}</h1>{article}<div style='text-align:center; margin-top:40px;'><a href='{link}' style='background:#ff6600; color:#000; padding:15px 50px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block;'>🚀 UNLOCK FULL DATA</a></div></div>"""

        # 4. Official API Post (v3) - Scopes को Force करना
        creds = service_account.Credentials.from_service_account_info(service_info)
        scoped_creds = creds.with_scopes(['https://www.googleapis.com/auth/blogger']) # यह बहुत ज़रूरी है
        service = build('blogger', 'v3', credentials=scoped_creds)
        
        post_data = {
            "kind": "blogger#post",
            "blog": {"id": BLOG_ID},
            "title": item.title,
            "content": html_body
        }
        
        # पक्का करना कि पोस्ट LIVE हो (isDraft=False)
        result = service.posts().insert(blogId=BLOG_ID, body=post_data, isDraft=False).execute()
        print(f"✅ SUCCESS! Article Live: {result.get('url')}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_api_machine()
