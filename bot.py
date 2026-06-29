import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. AI जर्नलिस्ट (Unblockable Prompt)
# ==========================================
def generate_unblockable_article(headline, cat, g_key):
    # सबसे सुरक्षित API वर्जन
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key.strip()}"
    
    # बहुत ही साधारण प्रॉम्प्ट (ताकि AI कभी मना न करे)
    prompt = f"Write a very long (1500 words) interesting and human-like story about this topic: '{headline}'. Use professional HTML tags like h2 and h3. Make it look like a viral blog post from a famous Indian blogger. Include a 'Frequently Asked Questions' section at the end. Talk about emotions and facts."

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    try:
        res = requests.post(url, json=payload, timeout=90).json()
        if 'candidates' in res and res['candidates']:
            return res['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"⚠️ Safety block for: {headline[:30]}")
            return None
    except:
        return None

# ==========================================
# 2. न्यूज़ हंटर (Duniya ki har khabar)
# ==========================================
def get_world_trending():
    # ऐसी फीड जो कभी खाली नहीं होती
    rss_urls = [
        "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
        "https://techcrunch.com/feed/",
        "https://www.pinkvilla.com/feed"
    ]
    random.shuffle(rss_urls)
    try:
        feed = feedparser.parse(rss_urls[0])
        return feed.entries
    except: return []

# ==========================================
# 3. कोर मशीन (The Fixer)
# ==========================================
def run_master_bot():
    print("🔋 BOOTING GHOST ENGINE v150.0...")
    try:
        # Load Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        G_KEY = os.getenv("GEMINI_API").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        # Blogger Auth
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        entries = get_world_trending()
        if not entries: 
            print("❌ No News Found!"); sys.exit(1)

        success = False
        # टॉप 50 खबरों को चेक करना (Unstoppable Loop)
        for entry in entries[:50]:
            print(f"📡 Testing: {entry.title}")
            
            # आर्टिकल लिखवाना
            article_body = generate_unblockable_article(entry.title, "Trending", G_KEY)
            
            if not article_body or len(article_body) < 500:
                print("⏭️ AI Refused. Trying next news..."); continue

            # Earning Link
            try:
                m_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
                money_link = m_res.get("shortenedUrl", entry.link)
            except: money_link = entry.link

            img_url = f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"

            # Final Design
            full_html = f"""
            <div style='font-family:Arial, sans-serif; line-height:1.9; color:#111; max-width:800px; margin:auto;'>
                <img src='{img_url}' style='width:100%; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.1);'/>
                <h1 style='color:#000;'>{entry.title}</h1>
                <div style='font-size:18px;'>{article_body}</div>
                <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:50px; border:3px solid #ff6600;'>
                    <h2 style='color:#ff6600;'>📢 WATCH EXCLUSIVE FOOTAGE</h2>
                    <p style='font-size:18px;'>Access the original unedited footage and verified report below.</p>
                    <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:15px 40px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block;'>🚀 UNLOCK FULL DATA</a>
                </div>
            </div>
            """

            # Post LIVE
            try:
                service.posts().insert(blogId=BLOG_ID, body={
                    "title": entry.title,
                    "content": full_html,
                    "labels": ["Latest News", "Viral", "Trending"]
                }, isDraft=False).execute()
                
                print(f"✅ SUCCESS! Post is LIVE: {entry.title}")
                success = True; break
            except Exception as e:
                print(f"❌ Blogger Error: {e}"); continue

        if not success:
            print("❌ TOTAL FAILURE: All 50 topics failed. AI or Blogger is blocking everything.")
            sys.exit(1) # GitHub को लाल निशान दिखाएगा

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_master_bot()
