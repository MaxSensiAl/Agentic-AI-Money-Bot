import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. AI जर्नलिस्ट (Multi-Model Unstoppable Logic)
# ==========================================
def generate_viral_article(headline, cat, or_key):
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # OpenRouter को ये Headers देना बहुत ज़रूरी है वरना वो ब्लॉक कर देता है
    headers = {
        "Authorization": f"Bearer {or_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/MaxSensial", # आपकी पहचान
        "X-Title": "ViralBot Pro"
    }
    
    # अगर एक मॉडल फेल हो, तो दूसरा ट्राई करने के लिए लिस्ट
    models = [
        "meta-llama/llama-3.1-8b-instruct:free", 
        "mistralai/mistral-7b-instruct:free",
        "google/gemma-2-9b-it:free"
    ]

    prompt = f"Act as a professional viral news blogger. Write a 1200-word highly engaging news article in HTML about: '{headline}'. Category: {cat}. Use H2, H3, b tags. Return ONLY HTML."

    for model in models:
        print(f"🤖 Trying AI Model: {model}...")
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            res = requests.post(url, headers=headers, json=data, timeout=100).json()
            if 'choices' in res:
                return res['choices'][0]['message']['content'].strip()
            else:
                print(f"⚠️ Model {model} busy: {res.get('error', {}).get('message', 'Unknown Error')}")
                continue # अगले मॉडल पर जाओ
        except:
            continue
    return None

# ==========================================
# 2. मुख्य इंजन (The Master Orchestrator)
# ==========================================
def run_power_bot():
    print("🔋 BOOTING GOD-MODE NEWS ENGINE (V210)...")
    try:
        # Secrets Loading
        def get_sec(name):
            val = os.getenv(name)
            if not val:
                print(f"❌ Missing Secret: {name}"); sys.exit(1)
            return val.strip()

        service_json = get_sec("SERVICE_ACCOUNT_JSON")
        service_info = json.loads(service_json)
        BLOG_ID = get_sec("BLOG_ID")
        OR_KEY = get_sec("OPENROUTER_API_KEY")
        S_KEY = get_sec("SHRINKME_API")

        # Blogger Auth
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        # ताज़ा न्यूज़ हंटर
        rss_url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(rss_url)
        if not feed.entries: return

        posted = False
        for entry in feed.entries[:15]:
            print(f"🎯 Checking News: {entry.title}")
            
            # AI से लेख लिखवाना (Multi-Model Support)
            article_body = generate_viral_article(entry.title, "Trending News", OR_KEY)
            
            if not article_body or len(article_body) < 400:
                print("⏭️ AI failed this news. Trying next..."); continue

            # Earning Link
            try:
                m_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
                money_link = m_res.get("shortenedUrl", entry.link)
            except: money_link = entry.link

            img_url = f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"

            # Premium Design
            full_html = f"""
            <div style='font-family:Arial; line-height:1.9; color:#111; max-width:800px; margin:auto;'>
                <img src='{img_url}' style='width:100%; border-radius:20px; box-shadow:0 10px 40px rgba(0,0,0,0.2);'/>
                <h1 style='color:#000;'>{entry.title}</h1>
                <div style='font-size:18px;'>{article_body}</div>
                <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:50px; border:3px solid #ff6600;'>
                    <h2 style='color:#ff6600;'>📢 WATCH EXCLUSIVE FOOTAGE</h2>
                    <p style='font-size:18px;'>The original unedited video and full report are available below.</p>
                    <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:18px 45px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block; box-shadow:0 10px 20px rgba(255,102,0,0.5);'>🚀 UNLOCK FULL DATA</a>
                    <p style='font-size:11px; margin-top:15px; color:#666;'>Verification: {random.randint(1000,9999)} | Protected</p>
                </div>
            </div>
            """

            # Post LIVE
            try:
                service.posts().insert(blogId=BLOG_ID, body={
                    "title": "🔴 BREAKING: " + entry.title,
                    "content": full_html,
                    "labels": ["Latest News", "Trending", "Viral"]
                }, isDraft=False).execute()
                
                print(f"✅ SUCCESS! Post is LIVE via Model Switcher.")
                posted = True; break
            except Exception as e:
                print(f"❌ Blogger Fail: {e}"); continue

        if not posted:
            print("❌ All models failed or busy. Retrying next cycle."); sys.exit(1)

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_power_bot()
