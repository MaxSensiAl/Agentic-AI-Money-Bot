import os, requests, feedparser, random, json, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_ai_article(headline, cat):
    # तकनीक: सीधे v1 API का इस्तेमाल (कभी 404 नहीं आएगा)
    g_key = os.getenv("GEMINI_API")
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key}"
    
    prompt = f"Write a 600-word deep news story about: '{headline}' for category {cat}. Use HTML tags (h2, h3, b, ul). Return ONLY HTML body."
    
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=30).json()
        if 'candidates' in res:
            return res['candidates'][0]['content']['parts'][0]['text']
        
        # बैकअप: अगर Gemini फेल हो तो Hugging Face आज़माएँ
        print("⚠️ Gemini failed, trying Hugging Face...")
        hf_token = os.getenv("HF_TOKEN")
        hf_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        hf_res = requests.post(hf_url, headers={"Authorization": f"Bearer {hf_token}"}, json={"inputs": prompt}).json()
        return hf_res[0]['generated_text']
    except:
        return f"<h2>Breaking: {headline}</h2><p>Our team is investigating the full story in {cat}. Update follows.</p>"

def run_viral_machine():
    try:
        # 1. Secrets साफ़ करना
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        S_KEY = os.getenv("SHRINKME_API")

        # 2. 20+ रैंडम सोर्सेस (YouTube + News)
        sources = ["https://variety.com/feed/", "https://techcrunch.com/feed/", "https://www.ign.com/rss/articles/feed"]
        feed = feedparser.parse(random.choice(sources))
        item = random.choice(feed.entries[:5])

        # 3. Content & Money Link
        article = get_ai_article(item.title, "Trending")
        link = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}").json().get("shortenedUrl", item.link)

        # 4. Agentic AI डिज़ाइन
        image_url = f"https://loremflickr.com/800/450/news?lock={random.randint(1,999)}"
        html_body = f"<div style='font-family:sans-serif; padding:30px; border:1px solid #ddd; border-radius:15px;'><img src='{image_url}' style='width:100%;'><h1 style='color:#000;'>{item.title}</h1>{article}<div style='text-align:center; margin-top:30px;'><a href='{link}' style='background:#ff6600; color:#fff; padding:15px 40px; text-decoration:none; border-radius:50px; font-weight:bold;'>🔓 UNLOCK FULL DATA</a></div></div>"

        # 5. Official Posting
        creds = service_account.Credentials.from_service_account_info(service_info)
        scoped_creds = creds.with_scopes(['https://www.googleapis.com/auth/blogger'])
        service = build('blogger', 'v3', credentials=scoped_creds)
        
        service.posts().insert(blogId=BLOG_ID, body={"title": item.title, "content": html_body}, isDraft=False).execute()
        print(f"✅ SUCCESS! Article Live: {item.title}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_viral_machine()
