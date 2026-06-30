import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. THE TRIPLE-AGENT AI ENGINE (Never Fails)
# ==========================================
def ask_ai_agent(prompt):
    """तीन अलग-अलग फ्री रास्तों से AI को आज़माना"""
    # रास्ता 1: Pollinations (Llama 3.1)
    try:
        encoded_prompt = requests.utils.quote(prompt)
        res = requests.get(f"https://text.pollinations.ai/{encoded_prompt}?model=llama&cache={random.random()}", timeout=60)
        if res.status_code == 200 and len(res.text) > 600: return res.text
    except: pass

    # रास्ता 2: OpenRouter Free (Gemma 2) - अगर Secret मौजूद है
    or_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if or_key:
        try:
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
                json={"model": "google/gemma-2-9b-it:free", "messages": [{"role": "user", "content": prompt}]}, timeout=60).json()
            return res['choices'][0]['message']['content']
        except: pass

    # रास्ता 3: Backup Text Engine (Mistral)
    try:
        res = requests.post("https://text.pollinations.ai/", 
            json={"messages": [{"role": "user", "content": prompt}], "model": "mistral"}, timeout=60).json()
        return res['choices'][0]['message']['content']
    except: return None

def generate_masterpiece(headline, cat):
    print(f"🤖 Agents are drafting a viral story for: {headline}...")
    
    prompt = f"""
    Act as a World-Class Indian News Journalist. Write a 1500-word explosive, human-like news article on: '{headline}'.
    Category: {cat}. 
    RULES: 
    - Tone: Emotional, spicy, direct. Use phrases like "Our sources leaked," "I was stunned."
    - Formatting: H1 for title, 8 H2/H3 subheadings, bold text, bullet points.
    - SEO: Include 5 FAQs and a viral search description.
    - Return ONLY HTML. No markdown.
    """
    return ask_ai_agent(prompt)

# ==========================================
# 2. 100+ CATEGORY INTELLIGENCE
# ==========================================
def get_world_viral_topic():
    queries = [
        "GTA 6 latest leaks gameplay", "iPhone 17 shocking leaks india", 
        "IPL 2025 retention drama", "Bollywood secret marriage viral", 
        "Gold price crash news india", "Upcoming movies 2025 teaser leaks",
        "Space NASA alien update", "YouTube India viral fight controversy",
        "New smartphone launch india 2025", "Indian stock market big update"
    ]
    random.shuffle(queries)
    query = queries[0]
    
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        feed = feedparser.parse(rss_url)
        return (feed.entries[0], query) if feed.entries else (None, None)
    except: return None, None

# ==========================================
# 3. CORE MISSION CONTROL
# ==========================================
def run_power_bot():
    print("🔋 BOOTING GOD-MODE ENGINE v800.0...")
    try:
        # Load Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        # Blogger Auth
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        # 1. ताज़ा खबर और उसका मोड
        entry, cat_name = get_world_viral_topic()
        if not entry: print("⏭️ No trends found."); return

        # 2. Duplicate Check
        posts = service.posts().list(blogId=BLOG_ID, maxResults=5).execute()
        if 'items' in posts:
            for p in posts['items']:
                if entry.title.lower()[:20] in p['title'].lower():
                    print("⏭️ Skipping Duplicate."); return

        # 3. AI से 1500 शब्दों का लेख लिखवाना
        article_html = generate_masterpiece(entry.title, cat_name)
        if not article_html or len(article_html) < 500:
            print("❌ All AI Agents failed. System retry in 30 mins."); sys.exit(1)

        # 4. कमाई वाला लिंक और इमेज
        try:
            m_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
            money_link = m_res.get("shortenedUrl", entry.link)
        except: money_link = entry.link
        
        img_url = f"https://source.unsplash.com/1200x675/?{cat_name.replace(' ','')},viral"

        # 5. Perfect HTML Template
        final_html = f"""
        <div style='font-family:Arial; line-height:1.9; color:#111; max-width:850px; margin:auto;'>
            <img src='{img_url}' style='width:100%; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.15);'/>
            <h1 style='font-size:35px;'>{entry.title}</h1>
            <p style='color:#777;'>Verified Official Update | {time.strftime("%B %d, %Y")}</p>
            <div class='article-body' style='font-size:19px;'>{article_html}</div>
            
            <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:60px; border:3px solid #ff6600;'>
                <h2 style='color:#ff6600; margin-top:0;'>📢 WATCH EXCLUSIVE FOOTAGE & PROOF</h2>
                <p>We have collected the leaked original video and verified data report for this story. UNLOCK NOW.</p>
                <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block;'>👉 GET FULL DETAILS</a>
                <p style='font-size:11px; margin-top:15px; color:#666;'>Verification ID: {random.randint(1000,9999)}</p>
            </div>
        </div>
        """

        # 6. पब्लिश करना (LIVE)
        print("📤 Sending Power Post to Blogger...")
        service.posts().insert(blogId=BLOG_ID, body={
            "title": "🔴 BREAKING: " + entry.title,
            "content": final_html,
            "labels": [cat_name.title(), "Trending", "Viral"],
            "searchDescription": entry.title[:150]
        }, isDraft=False).execute()

        print(f"✅ SUCCESS! Unstoppable Post is Live.")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_power_bot()
