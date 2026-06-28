import os, requests, feedparser, random, json, time, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_deep_article(headline, cat, g_key):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key}"
    style = random.choice(["Senior Journalist", "Viral Content Specialist", "Expert Critic"])
    prompt = f"Act as a professional {style}. Write a 800-word DEEP, UNIQUE article about: '{headline}' (Category: {cat}). Use HTML (h2, h3, b, ul, li). Include social buzz and 5 SEO keywords. Return ONLY HTML."
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=40).json()
        # Gemini Safety check logic
        if 'candidates' in res:
            return res['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"⚠️ Gemini Warning: Safety block or error - {res}")
            return f"<h2>Report: {headline}</h2><p>Latest verified data for {cat} is currently being updated.</p>"
    except Exception as e:
        print(f"⚠️ Gemini Error: {e}")
        return f"<h2>Report: {headline}</h2><p>Article content pending sync.</p>"

def run_api_machine():
    try:
        # Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        G_KEY = os.getenv("GEMINI_API")
        S_KEY = os.getenv("SHRINKME_API")

        # Scopes define करना बहुत ज़रूरी है
        SCOPES = ['https://www.googleapis.com/auth/blogger']
        
        # Sources
        sources = {
            "Tech": "https://techcrunch.com/feed/", 
            "Movies": "https://variety.com/feed/", 
            "Gaming": "https://www.ign.com/rss/articles/feed", 
            "Bollywood": "https://www.pinkvilla.com/feed"
        }
        cat, rss = random.choice(list(sources.items()))
        feed = feedparser.parse(rss)
        
        if not feed.entries:
            print("❌ No entries found in RSS")
            sys.exit(1)
            
        item = random.choice(feed.entries[:10])

        # Content & Money Link
        article = get_deep_article(item.title, cat, G_KEY)
        
        # Link Shortener (with error handling)
        try:
            money_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}", timeout=10).json()
            link = money_res.get("shortenedUrl", item.link)
        except:
            link = item.link

        # Article Design
        html_body = f"""<div style='font-family:sans-serif; line-height:1.6; color:#333;'>
        {article}
        <div style='text-align:center; margin-top:40px; background:#f9f9f9; padding:20px; border-radius:10px;'>
        <p><b>Want to read full original coverage?</b></p>
        <a href='{link}' style='background:#ff6600; color:#fff; padding:15px 35px; text-decoration:none; border-radius:5px; font-weight:bold; display:inline-block;'>🚀 CLICK HERE FOR FULL DATA</a>
        </div></div>"""

        # --- Official API Posting ---
        # Scopes को यहाँ include करना अनिवार्य है
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=SCOPES)
        service = build('blogger', 'v3', credentials=creds)
        
        post_data = {
            "kind": "blogger#post",
            "blog": {"id": BLOG_ID},
            "title": item.title,
            "content": html_body,
            "labels": [cat, "Breaking News", "Viral"]
        }
        
        # API Call
        request = service.posts().insert(blogId=BLOG_ID, body=post_data, isDraft=False)
        result = request.execute()
        
        if 'id' in result:
            print(f"✅ SUCCESS! Article Published at: {result.get('url')}")
        else:
            print(f"❌ Blogger Rejection: {result}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ SYSTEM ERROR: {str(e)}")
        sys.exit(1) 

if __name__ == "__main__":
    run_api_machine()
