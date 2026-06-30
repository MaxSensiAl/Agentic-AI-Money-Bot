import os, requests, feedparser, random, json, sys, re, time
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. THE GOD-MODE AI ENGINE (Official Gemini SDK)
# ==========================================
def generate_masterpiece_article(headline, cat):
    print(f"🤖 Official Gemini AI is writing: {headline}...")
    
    # API Key from Secrets
    genai.configure(api_key=os.getenv("GEMINI_API").strip())

    # --- SAFETY BYPASS: यह गूगल के फिल्टर को कुचल देगा ---
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]

    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    Act as a World-Class News Journalist. Write a 1500-word deep-dive explosive article on: '{headline}'.
    Category: {cat}.
    
    INSTRUCTIONS:
    1. STYLE: Human-like, spicy, emotional, and first-person. Use "I found out," "Leaked data shows."
    2. STRUCTURE: H1 Title, 8 subheadings (H2, H3), bold text, bullet points.
    3. NO BOT WORDS: Avoid 'delve', 'moreover', 'comprehensive', 'shaping'. 
    4. SEO: Include 5 'People Also Ask' FAQs with detailed answers.
    5. FORMAT: Return ONLY HTML content. No markdown code blocks. Start with <h1>.
    """

    try:
        response = model.generate_content(prompt, safety_settings=safety_settings)
        if response.text:
            return response.text
        return None
    except Exception as e:
        print(f"⚠️ AI Generation Error: {e}")
        return None

# ==========================================
# 2. VIRAL TOPIC INTELLIGENCE (100+ Categories)
# ==========================================
def get_viral_topic():
    # हर बार अलग ट्रेंड ढूँढना
    trends = [
        "GTA 6 map leaks and gameplay", "iPhone 17 Pro Max surprising updates", 
        "IPL 2026 latest transfer rumors", "Bollywood secret leaked news today",
        "Upcoming movies 2025 teaser trailers", "Space NASA mysterious discovery",
        "India Breaking News Today live", "Viral YouTube India fight drama"
    ]
    random.shuffle(trends)
    query = trends[0]
    
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        feed = feedparser.parse(rss_url)
        return feed.entries, query
    except: return None, None

# ==========================================
# 3. CORE SYSTEM CONTROL
# ==========================================
def run_power_bot():
    print("🔋 BOOTING FINAL STAGE ENGINE v900...")
    try:
        # Load Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        # Blogger Auth
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        # 1. खबर ढूँढना
        entries, cat_name = get_viral_topic()
        if not entries: return

        posted = False
        for entry in entries[:15]: # 15 आर्टिकल्स ट्राई करना
            print(f"🎯 Testing Target: {entry.title}")
            
            # Duplicate Check (पिछले 5 पोस्ट चेक करना)
            posts = service.posts().list(blogId=BLOG_ID, maxResults=5).execute()
            is_dup = False
            if 'items' in posts:
                for p in posts['items']:
                    if entry.title.lower()[:20] in p['title'].lower(): is_dup = True
            if is_dup: continue

            # 2. आर्टिकल लिखवाना (Official SDK)
            article_html = generate_masterpiece_article(entry.title, cat_name)
            if not article_html or len(article_html) < 500:
                print("⏭️ AI Safety Blocked even with bypass. Trying next..."); continue

            # 3. कमाई और फोटो
            try:
                m_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
                money_link = m_res.get("shortenedUrl", entry.link)
            except: money_link = entry.link
            
            img_url = f"https://source.unsplash.com/1200x675/?{cat_name.replace(' ','')},viral"

            # 4. Premium Design
            final_html = f"""
            <div style='font-family:Arial, sans-serif; line-height:1.9; color:#111; max-width:850px; margin:auto;'>
                <img src='{img_url}' style='width:100%; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.15);'/>
                <div class='content'>{article_html}</div>
                <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:60px; border:4px solid #ff6600;'>
                    <h2 style='color:#ff6600;'>📢 WATCH EXCLUSIVE FOOTAGE</h2>
                    <p style='font-size:18px;'>Access the full original report and unedited leaked video below. UNLOCK NOW.</p>
                    <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block;'>👉 UNLOCK FULL DATA</a>
                </div>
            </div>
            """

            # 5. पब्लिश करना (LIVE)
            service.posts().insert(blogId=BLOG_ID, body={
                "title": "🔴 BREAKING: " + entry.title,
                "content": final_html,
                "labels": [cat_name.title(), "Trending", "Live Update"],
                "searchDescription": entry.title[:150]
            }, isDraft=False).execute()

            print(f"✅ SUCCESS! Post is LIVE: {entry.title}")
            posted = True; break

        if not posted:
            print("❌ Failure: All attempts failed."); sys.exit(1)

    except Exception as e:
        print(f"❌ SYSTEM ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_power_bot()
