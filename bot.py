import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. THE UNSTOPPABLE AI AGENT (Pollinations)
# ==========================================
def ai_agent_write(headline, cat, is_update=False):
    """बिना किसी लिमिट के न्यूज़ लिखने वाला एजेंट"""
    print(f"🤖 AI Agent is generating content for: {headline}...")
    
    status_text = "LATEST UPDATE" if is_update else "BREAKING NEWS"
    
    prompt = f"""
    Act as a World-Class Viral Blogger. Write a 1500-word explosive news article on: '{headline}'. 
    Category: {cat}. Status: {status_text}.
    
    STRICT RULES:
    1. WORD COUNT: MINIMUM 1200-1500 words. Keep it very detailed.
    2. STYLE: 100% Human-like, emotional, and spicy. Use "I discovered," "Insiders revealed."
    3. NO BOT WORDS: Avoid 'delve', 'moreover', 'comprehensive', 'shaping'.
    4. STRUCTURE: Use H1 for title, 6-7 H2/H3 subheadings, bullet points, and bold text.
    5. SEO: Meta description (150 chars) and 5 viral FAQs.
    6. FORMAT: Return ONLY HTML content. Do not include any intro or outro text.
    """

    # Pollinations AI - Free & Reliable for GitHub
    encoded_prompt = requests.utils.quote(prompt)
    url = f"https://text.pollinations.ai/{encoded_prompt}?model=llama"

    for attempt in range(3):
        try:
            res = requests.get(url, timeout=120)
            if res.status_code == 200 and len(res.text) > 800:
                return res.text
            print(f"🔄 Retry {attempt+1}: AI response too short.")
            time.sleep(10)
        except: time.sleep(10)
    return None

# ==========================================
# 2. 100+ CATEGORY TREND HUNTER
# ==========================================
def get_ultimate_viral_topic():
    # 100+ केटेगरी की मास्टर लिस्ट (Tech, Sports, Celebs, Gaming, etc.)
    categories = [
        "GTA 6 Leaks Today", "IPL 2025 Shocking Update", "Bollywood Secret Gossip",
        "iPhone 17 Pro Leaks", "Space Discovery NASA", "AI Robots Future", 
        "Global Market Crash News", "Viral YouTube India Controversy", "Upcoming Movies 2025",
        "Military Weapons Update India", "Smartphone Launch India", "Gold Price Shocking Trend"
    ]
    random.shuffle(categories)
    query = categories[0]
    
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries: return feed.entries[0], query
    except: return None, None

# ==========================================
# 3. SMART UPDATE CHECKER
# ==========================================
def get_post_mode(title, service, blog_id):
    try:
        posts = service.posts().list(blogId=blog_id, maxResults=15).execute()
        if 'items' in posts:
            for p in posts['items']:
                if title.lower()[:25] in p['title'].lower(): return "UPDATE"
        return "NEW"
    except: return "NEW"

# ==========================================
# 4. MAIN MISSION ENGINE
# ==========================================
def run_power_bot():
    print("🔋 BOOTING UNSTOPPABLE NEWS ENGINE v600...")
    try:
        # Load Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        # Blogger Auth
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        # 1. वायरल खबर ढूँढना
        entry, cat_name = get_ultimate_viral_topic()
        if not entry: return

        # 2. स्टेटस चेक करना (New or Update?)
        mode = get_post_mode(entry.title, service, BLOG_ID)
        print(f"🎯 Target: {entry.title} | Mode: {mode}")

        # 3. एजेंट से लिखवाना (Pollinations AI)
        article_html = ai_agent_write(entry.title, cat_name, is_update=(mode == "UPDATE"))
        if not article_html:
            print("❌ AI Agent Failure. Switching to backup topic..."); return

        # 4. कमाई और इमेज
        try:
            m_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
            money_link = m_res.get("shortenedUrl", entry.link)
        except: money_link = entry.link
        
        img_url = f"https://source.unsplash.com/1200x675/?{cat_name.replace(' ','')},viral"

        # 5. Final God-Mode Design
        prefix = "🚨 LIVE UPDATE: " if mode == "UPDATE" else "🔴 BREAKING: "
        
        final_html = f"""
        <div style='font-family:Arial, sans-serif; line-height:1.9; color:#111; max-width:850px; margin:auto;'>
            <div style='background:red; color:white; padding:5px 15px; display:inline-block; border-radius:3px; font-weight:bold;'>{mode} STORY</div>
            <img src='{img_url}' style='width:100%; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.2); margin-top:15px;'/>
            <h1 style='font-size:35px;'>{entry.title}</h1>
            <div class='content' style='font-size:18px;'>{article_html}</div>
            
            <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:60px; border:3px solid #ff6600;'>
                <h2 style='color:#ff6600; margin-top:0;'>📢 WATCH EXCLUSIVE VIDEO & PROOF</h2>
                <p style='font-size:18px;'>Full original leaked data and verified report are available below. Access now.</p>
                <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:18px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block; box-shadow:0 5px 25px rgba(255,102,0,0.5);'>🚀 UNLOCK FULL DATA</a>
            </div>
        </div>
        """

        # 6. पब्लिश करना (LIVE)
        service.posts().insert(blogId=BLOG_ID, body={
            "title": prefix + entry.title,
            "content": final_html,
            "labels": [cat_name.title(), "Viral", "Trending"],
            "searchDescription": entry.title[:150]
        }, isDraft=False).execute()

        print(f"✅ MISSION ACCOMPLISHED! Post is LIVE.")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_power_bot()
