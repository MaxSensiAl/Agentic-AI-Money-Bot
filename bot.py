import os, requests, feedparser, random, json, time, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_deep_article(headline, cat, g_key):
    # URL को v1 से v1beta में बदल दिया गया है
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    style = random.choice(["Senior Journalist", "Viral Content Specialist", "Expert Critic"])
    prompt = f"Act as a professional {style}. Write a 800-word DEEP, UNIQUE article about: '{headline}' (Category: {cat}). Use HTML (h2, h3, b, ul, li). Include social buzz and 5 SEO keywords. Return ONLY HTML."
    
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=40).json()
        if 'candidates' in res:
            return res['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"⚠️ Gemini API Response: {res}")
            return f"<h2>Report: {headline}</h2><p>Latest updates on {cat} are being compiled.</p>"
    except Exception as e:
        print(f"⚠️ Gemini Connection Error: {e}")
        return f"<h2>Report: {headline}</h2><p>Article generation failed, please check API limits.</p>"

def run_api_machine():
    try:
        # Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        G_KEY = os.getenv("GEMINI_API")
        S_KEY = os.getenv("SHRINKME_API")

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
            print("❌ RSS Feed is empty")
            return

        item = random.choice(feed.entries[:10])

        # Article & Link
        article = get_deep_article(item.title, cat, G_KEY)
        
        try:
            money_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}", timeout=10).json()
            link = money_res.get("shortenedUrl", item.link)
        except:
            link = item.link

        html_body = f"""<div style='font-family:sans-serif; line-height:1.7;'>{article}<br><div style='text-align:center;'><a href='{link}' style='background:#ff6600; color:#fff; padding:15px 35px; text-decoration:none; border-radius:5px; font-weight:bold;'>🚀 READ FULL STORY</a></div></div>"""

        # --- Blogger API Auth ---
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=SCOPES)
        service = build('blogger', 'v3', credentials=creds)
        
        post_data = {
            "kind": "blogger#post",
            "blog": {"id": BLOG_ID},
            "title": item.title,
            "content": html_body,
            "labels": [cat, "Viral News"]
        }
        
        # isDraft=False ensure karta hai ki post turant publish ho
        print(f"Attempting to post to Blog ID: {BLOG_ID}...")
        result = service.posts().insert(blogId=BLOG_ID, body=post_data, isDraft=False).execute()
        
        if 'id' in result:
            print(f"✅ SUCCESS! Live URL: {result.get('url')}")
        else:
            print(f"❌ Unknown Rejection: {result}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ SYSTEM ERROR: {str(e)}")
        # अगर 403 एरर आए तो साफ़ निर्देश दें
        if "403" in str(e):
            print("\n💡 ACTION REQUIRED: Blogger Settings mein jaakar Service Account email ko 'ADMIN' banayein!")
        sys.exit(1)

if __name__ == "__main__":
    run_api_machine()
