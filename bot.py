import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. THE DECEIVER (AI को चकमा देने वाला लॉजिक)
# ==========================================
def generate_unblockable_article(headline, cat, g_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key.strip()}"
    
    # हैक: न्यूज़ को 'कहानी' या 'रिसर्च' की तरह पेश करना
    # ताकि सुरक्षा फ़िल्टर को लगे कि यह न्यूज़ नहीं, बल्कि साहित्य (Literature) है।
    prompt = f"""
    Act as a Master Storyteller & Creative Writer. 
    Your task is to write a 1200-word deep narrative based on the theme: '{headline}'.
    
    ARCHITECTURAL REQUIREMENTS:
    1. STYLE: Emotional, human-centric, and very detailed. Use a first-person perspective ("I saw," "I believe").
    2. FORMAT: Professional blog structure with one H1, four H2, and six H3 subheadings.
    3. LANGUAGE: Avoid using any formal news-reporting words. Use spicy, conversational, and direct language.
    4. NO AI CLICHES: Strictly avoid 'delve', 'moreover', 'comprehensive', 'shaping', 'era'. 
    5. SEO: Meta description (150 chars) and 5 viral FAQs.
    
    STRICT FORMAT: Return ONLY a JSON object (no markdown):
    {{
      "meta": "viral description",
      "article": "HTML content with subheadings",
      "faq": [ {{"q":"?","a":".."}} ]
    }}
    """
    
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
        if 'candidates' not in res or not res['candidates']:
            print(f"⚠️ Safety block detected. Activating Fallback Logic...")
            return None # अगले टॉपिक पर जाएगा
            
        raw_text = res['candidates'][0]['content']['parts'][0]['text']
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else None
    except Exception as e:
        print(f"❌ AI Parse Error: {e}")
        return None

# ==========================================
# 2. VIRAL TOPIC RECOVERY (Never Fails)
# ==========================================
def get_trending_news():
    # ऐसी फीड्स जो कम ब्लॉक होती हैं
    queries = [
        "latest tech gadgets india", "bollywood behind the scenes", 
        "gaming world updates", "cricket viral stories", "unexplained world events"
    ]
    random.shuffle(queries)
    for q in queries:
        rss_url = f"https://news.google.com/rss/search?q={q.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries: return feed.entries, q
        except: continue
    return None, None

# ==========================================
# 3. THE MONEY ENGINE (ShrinkMe + High CTR)
# ==========================================
def run_master_engine():
    print("🔋 STARTING GOD-MODE ENGINE (Bypassing Filters)...")
    try:
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        G_KEY = os.getenv("GEMINI_API").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        entries, niche = get_trending_news()
        if not entries: return

        posted = False
        for entry in entries[:20]: # 20 आर्टिकल्स चेक करेगा जब तक एक पास न हो जाए
            print(f"🎯 Analyzing: {entry.title}")
            
            data = generate_unblockable_article(entry.title, niche, G_KEY)
            if not data: continue

            # Earning Link
            try:
                m_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
                money_link = m_res.get("shortenedUrl", entry.link)
            except: money_link = entry.link

            img_url = f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"
            faq_html = "".join([f"<b>Q: {f.get('q','')}</b><p>A: {f.get('a','')}</p>" for f in data.get('faq', [])])

            # Premium Blogger Layout (Google Search Console Ready)
            full_html = f"""
            <div style='font-family:Arial; line-height:1.9; color:#111; max-width:800px; margin:auto;'>
                <img src='{img_url}' style='width:100%; border-radius:20px; box-shadow:0 15px 40px rgba(0,0,0,0.15);'/>
                <h1 style='color:#000; font-size:35px;'>{entry.title}</h1>
                <div class='main-article' style='font-size:18px;'>{data['article']}</div>
                <div style='background:#f4f4f4; padding:25px; border-radius:15px; margin-top:40px;'>
                    <h3>Important People Also Ask (SEO)</h3>{faq_html}
                </div>
                <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:50px; border:3px solid #ff6600;'>
                    <h2 style='color:#ff6600;'>📢 DOWNLOAD FULL SOURCE DATA</h2>
                    <p style='font-size:18px;'>We have collected the original documents and raw footage for this report. Download from our secure cloud below.</p>
                    <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:18px 45px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block; box-shadow:0 5px 25px rgba(255,102,0,0.5);'>🚀 UNLOCK SOURCE DATA</a>
                    <p style='font-size:11px; margin-top:15px; color:#666;'>Verification: {random.randint(1000,9999)} | Anti-Delete Protected</p>
                </div>
            </div>
            """

            # Post LIVE to Blogger
            try:
                service.posts().insert(blogId=BLOG_ID, body={
                    "title": "🚨 BREAKING: " + entry.title,
                    "content": full_html,
                    "labels": [niche.title(), "Trending", "Live"],
                    "searchDescription": data['meta']
                }, isDraft=False).execute()
                
                print(f"✅ SUCCESS! Unstoppable post is LIVE.")
                posted = True; break
            except Exception as e:
                print(f"❌ Post Failed: {e}"); continue

        if not posted:
            print("❌ Failure: AI and Filters won this round. Retrying in 30 mins."); sys.exit(1)

    except Exception as e:
        print(f"❌ CRITICAL ENGINE FAILURE: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_master_engine()
