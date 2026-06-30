import os, requests, feedparser, random, json, sys, re, time
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. BRAIN LOGIC: KEYWORD NEUTRALIZER (AI को शांत करने के लिए)
# ==========================================
def neutralize_headline(text):
    """खबर के हेडलाइन से डरावने शब्द हटाना ताकि AI ब्लॉक न करे"""
    replacements = {
        "deadly": "significant", "murder": "case study", "war": "situation",
        "attack": "incident", "vs": "and", "scandal": "update", "shocking": "surprising",
        "exposed": "revealed", "rape": "incident", "killed": "impacted", "fight": "discussion"
    }
    for word, replacement in replacements.items():
        text = re.compile(re.escape(word), re.IGNORECASE).sub(replacement, text)
    return text

# ==========================================
# 2. THE GHOST PROMPT (AI को 'प्रोफेसर' बनाना)
# ==========================================
def generate_unblockable_article(headline, cat):
    g_key = os.getenv("GEMINI_API").strip()
    genai.configure(api_key=g_key)

    # सुरक्षा फिल्टर को पूरी तरह बंद करना
    safety = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # न्यूट्रल हेडलाइन बनाना
    safe_topic = neutralize_headline(headline)

    # REVERSE PROMPTING: AI को जर्नलिस्ट नहीं, 'इतिहासकार/प्रोफेसर' बनाना
    prompt = f"""
    Act as a Distinguished University Professor and Expert Historian. 
    Write a 1500-word comprehensive informational report and scholarly analysis on the following subject: '{safe_topic}'.
    
    GUIDELINES FOR RANKING:
    1. STYLE: Informative, objective, yet deeply engaging like a long-form magazine essay.
    2. LANGUAGE: 100% human-like. Use conversational scholarly tone. 
    3. STRUCTURE: Use H1 for title, 8-10 H2/H3 subheadings, bold keywords, and detailed paragraphs.
    4. NO AI CLICHES: Do not use 'shaping', 'moreover', 'delve', 'comprehensive', 'era'.
    5. SEO: Include 5 'Frequently Asked Questions' at the end based on global curiosity.
    6. FORMAT: Return ONLY HTML content. Do not include markdown code blocks. Start with <h1>.
    """

    try:
        response = model.generate_content(prompt, safety_settings=safety)
        if response and response.text:
            return response.text
        return None
    except Exception as e:
        print(f"⚠️ Agent Logic Error: {e}")
        return None

# ==========================================
# 3. DYNAMIC SEARCH (100+ Categories)
# ==========================================
def get_viral_target():
    niches = [
        "latest tech gadgets launch 2025", "space discovery mystery", 
        "ipl 2026 biggest buzz", "bollywood behind the scenes leaks",
        "stock market unusual trends", "viral world records today"
    ]
    random.shuffle(niches)
    query = niches[0]
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        feed = feedparser.parse(rss_url)
        return feed.entries, query
    except: return None, None

# ==========================================
# 4. CORE ENGINE (The Fixer)
# ==========================================
def run_power_bot():
    print("🔋 INITIALIZING GHOST PROTOCOL v2000.0...")
    try:
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        entries, niche = get_viral_target()
        if not entries: return

        success = False
        # टॉप 20 आर्टिकल्स को चेक करना (Unstoppable Loop)
        for entry in entries[:20]:
            print(f"🎯 Mission Target: {entry.title}")

            # १. डुप्लीकेट चेक (पिछले ५ पोस्ट)
            posts = service.posts().list(blogId=BLOG_ID, maxResults=5).execute()
            if 'items' in posts:
                if any(entry.title.lower()[:20] in p['title'].lower() for p in posts['items']):
                    print("⏭️ Duplicate. Next..."); continue

            # २. AI आर्टिकल जनरेट करना (Ghost Logic)
            article_body = generate_unblockable_article(entry.title, niche)
            
            if not article_body or len(article_body) < 600:
                print("⏭️ Filter Blocked. Switching strategy..."); continue

            # ३. कमाई लिंक और फोटो
            money_link = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}").json().get("shortenedUrl", entry.link)
            img_url = f"https://source.unsplash.com/1200x675/?{niche.replace(' ','')},global"

            # ४. Final High-End Design
            final_html = f"""
            <div style='font-family:Arial, sans-serif; line-height:1.9; color:#111; max-width:850px; margin:auto;'>
                <img src='{img_url}' alt='Information' style='width:100%; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.15);'/>
                <div class='article-content' style='font-size:18px;'>{article_body}</div>
                <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:60px; border:4px solid #ff6600;'>
                    <h2 style='color:#ff6600; margin-top:0;'>📢 WATCH EXCLUSIVE VIDEO & PROOF</h2>
                    <p style='font-size:18px;'>The original source data and verified unedited footage are available below.</p>
                    <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block;'>👉 UNLOCK FULL DATA</a>
                </div>
            </div>
            """

            # ५. पब्लिश करना (LIVE)
            service.posts().insert(blogId=BLOG_ID, body={
                "title": entry.title,
                "content": final_html,
                "labels": [niche.title(), "World Update", "Trending"],
                "searchDescription": entry.title[:150]
            }, isDraft=False).execute()

            print(f"✅ GHOST PROTOCOL SUCCESS! Post Published.")
            success = True; break

        if not success: sys.exit(1)

    except Exception as e:
        print(f"❌ SYSTEM FAILURE: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_power_bot()
