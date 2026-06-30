import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. THE AI ENGINE (Pollinations - No Limits)
# ==========================================
def ai_agent_write(headline, cat, is_update=False):
    print(f"🤖 AI Agent is generating a unique 1200-word story for: {headline}...")
    
    prompt = f"""
    Write a 1200-word highly engaging, viral, and human-like blog post about: '{headline}'. 
    Category: {cat}. Mode: {"Live Follow-up" if is_update else "Breaking News"}.
    
    STRICT RULES:
    1. STYLE: Fast-paced, emotional, Indian Blogger Style. Use first-person language.
    2. STRUCTURE: Use H1 Title, 7-8 subheadings (H2, H3), bold names, and bullet points.
    3. NO ROBOTIC WORDS: Avoid 'delve', 'moreover', 'comprehensive', 'shaping'.
    4. FAQ: Include 5 'People Also Ask' questions with long answers.
    5. SEO: Meta description (150 chars) and 10 trending keywords.
    6. RETURN: ONLY the HTML content. No markdown blocks.
    """

    encoded_prompt = requests.utils.quote(prompt)
    url = f"https://text.pollinations.ai/{encoded_prompt}?model=llama"

    try:
        res = requests.get(url, timeout=120)
        if res.status_code == 200 and len(res.text) > 500:
            return res.text
    except: return None

# ==========================================
# 2. 100+ CATEGORY TREND HUNTER
# ==========================================
def get_world_viral_topic():
    # 100+ ट्रेंडिंग टॉपिक्स और सर्च क्वेरीज़
    topics = [
        "GTA 6 leaked gameplay and map details", "iPhone 17 Pro Max shocking leaks", 
        "Bollywood actress secret marriage viral", "IPL 2025 mega auction leaks", 
        "New AI robot discovery 2025", "Indian stock market big crash news", 
        "Space NASA alien discovery news", "Viral YouTube India fight and drama", 
        "Upcoming movies 2025 budget and leaks", "Gold price massive drop news india",
        "Defense news India new missiles", "UFO sightings over India news"
    ]
    random.shuffle(topics)
    query = topics[0]
    
    # गूगल न्यूज़ सर्च से ताज़ा डेटा उठाना
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            return feed.entries[0], query
    except: return None, None

# ==========================================
# 3. CORE MISSION CONTROL
# ==========================================
def run_power_bot():
    print("🔋 STARTING GOD-MODE NEWS MACHINE v700.0...")
    try:
        # Load & Clean Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID", "").strip()
        S_KEY = os.getenv("SHRINKME_API", "").strip()

        # Blogger API Auth
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        # 1. ताज़ा वायरल खबर ढूँढना (100+ Categories)
        entry, cat_name = get_world_viral_topic()
        if not entry: print("⏭️ No news found."); return

        # 2. चेक करना कि नया पोस्ट है या अपडेट (Smart Logic)
        mode = "NEW"
        try:
            posts = service.posts().list(blogId=BLOG_ID, maxResults=10).execute()
            if 'items' in posts:
                for p in posts['items']:
                    if entry.title.lower()[:20] in p['title'].lower(): mode = "UPDATE"
        except: pass

        print(f"🎯 Target: {entry.title} | Mode: {mode}")

        # 3. AI जर्नलिस्ट से लिखवाना
        article_html = ai_agent_write(entry.title, cat_name, is_update=(mode=="UPDATE"))
        if not article_html: 
            print("❌ AI Failed. Retrying in next cycle."); sys.exit(1)

        # 4. कमाई वाला लिंक और इमेज
        try:
            m_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
            money_link = m_res.get("shortenedUrl", entry.link)
        except: money_link = entry.link
        
        img_url = f"https://source.unsplash.com/1200x675/?{cat_name.replace(' ','')},news"

        # 5. Premium High-Click Design
        prefix = "🚨 BIG UPDATE: " if mode == "UPDATE" else "🔴 BREAKING: "
        final_html = f"""
        <div style='font-family:Arial, sans-serif; line-height:1.9; color:#111; max-width:850px; margin:auto;'>
            <div style='background:red; color:white; padding:5px 15px; display:inline-block; border-radius:5px; font-weight:bold;'>{mode} EXCLUSIVE</div>
            <img src='{img_url}' alt='{entry.title}' style='width:100%; border-radius:20px; box-shadow:0 15px 40px rgba(0,0,0,0.15); margin-top:15px;'/>
            <h1 style='font-size:35px;'>{entry.title}</h1>
            <p style='color:#777;'>Verified Official Source | {time.strftime("%B %d, %Y")}</p>
            <div class='article-body' style='font-size:19px;'>{article_html}</div>
            
            <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:50px; border:3px solid #ff6600;'>
                <h2 style='color:#ff6600; margin-top:0;'>📢 WATCH EXCLUSIVE LEAKED VIDEO</h2>
                <p style='font-size:18px;'>The original unedited raw footage and full data report for this story are available below. UNLOCK NOW.</p>
                <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block; box-shadow:0 5px 25px rgba(255,102,0,0.5);'>🚀 UNLOCK FULL DATA SOURCE</a>
                <p style='font-size:11px; margin-top:15px; color:#666;'>Verification: Secure | ID {random.randint(1000,9999)}</p>
            </div>
        </div>
        """

        # 6. पब्लिश करना (With URL Printing)
        print("📤 Sending request to Blogger API...")
        result = service.posts().insert(blogId=BLOG_ID, body={
            "title": prefix + entry.title,
            "content": final_html,
            "labels": [cat_name.title(), "Trending", "Viral"],
            "searchDescription": entry.title[:150]
        }, isDraft=False).execute()

        if 'id' in result:
            print(f"✅ SUCCESS! Article Published.")
            print(f"🔗 LIVE LINK: {result.get('url')}")
        else:
            print(f"❌ Blogger Rejection: {result}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_power_bot()
