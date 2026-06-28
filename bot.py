import os, requests, feedparser, random, json, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

def run_viral_engine():
    try:
        # 1. Secrets को साफ़-सुथरा करना
        service_json = os.getenv("SERVICE_ACCOUNT_JSON")
        service_info = json.loads(service_json)
        BLOG_ID = os.getenv("BLOG_ID").strip() # किसी भी एक्स्ट्रा स्पेस को हटाना
        G_KEY = os.getenv("GEMINI_API")
        S_KEY = os.getenv("SHRINKME_API")

        # 2. ताज़ा खबर उठाना (YouTube India Trending)
        sources = ["https://news.google.com/rss/search?q=trending+on+youtube+india&hl=en-IN&gl=IN&ceid=IN:en", "https://techcrunch.com/feed/"]
        feed = feedparser.parse(random.choice(sources))
        item = random.choice(feed.entries[:10])
        
        # 3. AI से गहरा 600 शब्दों का लेख
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
        prompt = f"Act as a professional Viral News Reporter. Write a 600-word deep news story about: '{item.title}'. Include hidden facts, bullet points, and social media reactions with emojis. Return ONLY HTML."
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}).json()
        article = res['candidates'][0]['content']['parts'][0]['text']
        
        money_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}").json()
        money_link = money_res.get("shortenedUrl", item.link)

        # 4. Agentic AI डिज़ाइन
        image_url = f"https://loremflickr.com/800/450/news?lock={random.randint(1,999)}"
        html_body = f"<div style='font-family:sans-serif; padding:30px; border:1px solid #ddd; border-radius:15px;'><img src='{image_url}' style='width:100%;'><h1 style='color:#000;'>{item.title}</h1>{article}<div style='text-align:center; margin-top:30px;'><a href='{money_link}' style='background:#ff6600; color:#000; padding:15px 40px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px;'>🚀 UNLOCK FULL DATA</a></div></div>"

        # 5. Official API Posting
        creds = service_account.Credentials.from_service_account_info(service_info)
        service = build('blogger', 'v3', credentials=creds)
        
        post_data = {"kind": "blogger#post", "blog": {"id": BLOG_ID}, "title": item.title, "content": html_body}
        service.posts().insert(blogId=BLOG_ID, body=post_data).execute()
        print(f"✅ MISSION SUCCESS! Posted: {item.title}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    run_viral_engine()
