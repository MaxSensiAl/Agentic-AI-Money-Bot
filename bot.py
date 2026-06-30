import os, requests, feedparser, random, json, sys, re, time
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. THE GOD-MODE AI ENGINE (Stable SDK Fix)
# ==========================================
def generate_article(headline, cat):
    g_key = os.getenv("GEMINI_API")
    if not g_key:
        print("❌ GEMINI_API missing!"); return None
        
    # API Configure
    genai.configure(api_key=g_key.strip())
    
    # Safety Bypass: यह सेटिंग AI को कुछ भी लिखने की आज़ादी देती है
    safety = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]

    # मॉडल का नाम सही किया गया है (Fixes 404 Error)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Act as India's No.1 Viral Blogger. Write a 1500-word deep-dive explosive article on: '{headline}'. 
    Category: {cat}. 
    RULES: 
    - 100% Human Style, Spicy language, emotional tone. 
    - Use H1, H2, H3 tags, bold text, and lists.
    - Write a huge article (minimum 1200 words).
    - Include a viral intro and 5 detailed FAQs at the end.
    Return ONLY HTML content. No markdown code blocks.
    """

    try:
        # Generation call
        response = model.generate_content(prompt, safety_settings=safety)
        if response and response.text:
            return response.text
        return None
    except Exception as e:
        print(f"⚠️ AI Generation Error: {e}")
        return None

# ==========================================
# 2. 100+ CATEGORY TREND HUNTER
# ==========================================
def get_viral_topic():
    queries = [
        "GTA 6 map leaks", "iPhone 17 Pro Max surprises", 
        "IPL 2026 biggest rumors", "Bollywood secret leaked news",
        "Upcoming movies 2025 teaser", "India Breaking News live"
    ]
    random.shuffle(queries)
    query = queries[0]
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            return feed.entries, query
    except: return None, None

# ==========================================
# 3. CORE MISSION ENGINE
# ==========================================
def run_power_bot():
    print("🔋 BOOTING STABLE ENGINE v1000.0...")
    try:
        # Load Secrets
        service_json = os.getenv("SERVICE_ACCOUNT_JSON")
        BLOG_ID = os.getenv("BLOG_ID").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        if not service_json:
            print("❌ SERVICE_ACCOUNT_JSON missing!"); sys.exit(1)

        # Blogger Auth
        service_info = json.loads(service_json)
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        entries, cat = get_viral_topic()
        if not entries: return

        posted = False
        # टॉप 15 खबरों को चेक करना
        for entry in entries[:15]:
            print(f"🎯 Testing: {entry.title}")
            
            # AI Article Generation
            article_html = generate_article(entry.title, cat)
            
            if not article_html or len(article_html) < 500:
                print("⏭️ AI Safety Blocked even with bypass. Trying next..."); continue

            # Earning Link (Money)
            try:
                m_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
                money_link = m_res.get("shortenedUrl", entry.link)
            except: money_link = entry.link
            
            img_url = f"https://source.unsplash.com/1200x675/?{cat.replace(' ','')},news"

            final_html = f"""
            <div style='font-family:Arial, sans-serif; line-height:1.9; color:#111; max-width:850px; margin:auto;'>
                <img src='{img_url}' style='width:100%; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.15);'/>
                <div class='content'>{article_html}</div>
                <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:50px; border:3px solid #ff6600;'>
                    <h2 style='color:#ff6600; margin-top:0;'>📢 WATCH EXCLUSIVE FOOTAGE</h2>
                    <p style='font-size:18px;'>Access the original unedited leaked media and verified source report below.</p>
                    <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block;'>👉 UNLOCK FULL DATA</a>
                </div>
            </div>
            """

            # पब्लिश करना (LIVE)
            service.posts().insert(blogId=BLOG_ID, body={
                "title": "🔴 BREAKING: " + entry.title,
                "content": final_html,
                "labels": [cat.title(), "Viral", "Trending"],
                "searchDescription": entry.title[:150]
            }, isDraft=False).execute()

            print(f"✅ SUCCESS! Post is LIVE: {entry.title}")
            posted = True; break

        if not posted:
            print("❌ Failed: All 15 topics were blocked by AI."); sys.exit(1)

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_power_bot()
