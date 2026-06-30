import os, requests, feedparser, random, json, sys, re, time
from duckduckgo_search import DDGS
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. THE AI AGENT (Human-Style & Real Data)
# ==========================================
def ai_agent_write(headline, cat, update_mode=False):
    """बिना किसी चाबी के न्यूज़ लिखने वाला मास्टर एजेंट"""
    
    # अगर खबर पुरानी है लेकिन ट्रेंडिंग है, तो एंगल बदल जाएगा
    angle = "Write it from a fresh perspective (like public reaction or hidden facts)" if update_mode else "Write it as an explosive breaking news story"
    
    prompt = f"""
    Act as a World-Class investigative Journalist. Topic: '{headline}'. Category: {cat}.
    Task: {angle}.
    
    RULES:
    1. LENGTH: Exactly 1200-1500 words. 
    2. HUMAN TONE: Use spicy, emotional, and first-person language. No robotic intros.
    3. STRUCTURE: H1 Title, H2 (The Deep Truth), H3 (Exclusive Leaks), H3 (Global Impact).
    4. NO AI WORDS: Avoid 'delve', 'moreover', 'shaping', 'landmark', 'comprehensive'.
    5. SEO: Include 5 'People Also Ask' FAQs and 10 viral tags.
    6. REAL NEWS ONLY: Use verified facts. Return ONLY HTML content. No markdown.
    """

    for attempt in range(3):
        try:
            with DDGS() as ddgs:
                response = ddgs.chat(prompt, model='llama-3.1-70b')
                if response and len(response) > 600: return response
        except: time.sleep(5)
    return None

# ==========================================
# 2. 100+ CATEGORY TREND HUNTER
# ==========================================
def get_ultimate_trending_topic():
    # 100+ कैटेगरी को कवर करने के लिए मास्टर लिस्ट
    categories = [
        "Bollywood Leaks", "IPL Cricket Controversy", "GTA 6 Leaks", "iPhone 17 Shocking",
        "India Breaking News", "Space Discovery", "AI News Today", "Global Stock Market",
        "Viral YouTube India", "Hollywood Gossip", "Automobile Launch", "Defense News India"
    ]
    random.shuffle(categories)
    query = categories[0]
    
    # Google News RSS (Top Search Logic)
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            return feed.entries[0], query
    except: return None, None

# ==========================================
# 3. SMART UPDATE CHECKER
# ==========================================
def get_post_status(title, service, blog_id):
    """चेक करना कि ये नया है या इसका अपडेट डालना है"""
    try:
        posts = service.posts().list(blogId=blog_id, maxResults=20).execute()
        if 'items' in posts:
            for p in posts['items']:
                if title.lower()[:30] in p['title'].lower():
                    return "UPDATE" # टाइटल मैच हुआ मतलब अपडेट मोड
        return "NEW"
    except: return "NEW"

# ==========================================
# 4. MAIN ENGINE (Money Machine)
# ==========================================
def run_power_bot():
    print("🔋 BOOTING GOD-MODE NEWS AGENT v400...")
    try:
        # Load Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        # Blogger Auth
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        # 1. 100 कैटेगरी में से ट्रेंडिंग खबर ढूंढना
        entry, cat_name = get_ultimate_trending_topic()
        if not entry: return

        # 2. स्टेटस चेक करना (New or Update?)
        status = get_post_status(entry.title, service, BLOG_ID)
        print(f"🎯 News Found: {entry.title} | Status: {status}")

        # 3. एजेंट से लिखवाना
        article_html = ai_agent_write(entry.title, cat_name, update_mode=(status == "UPDATE"))
        if not article_html: sys.exit(1)

        # 4. कमाई और इमेज (Unsplash HD)
        money_link = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}").json().get("shortenedUrl", entry.link)
        img_url = f"https://source.unsplash.com/1200x675/?{cat_name.replace(' ','')},viral"

        # 5. Final God-Mode Design
        prefix = "🚨 LIVE UPDATE: " if status == "UPDATE" else "🔴 BREAKING: "
        
        final_html = f"""
        <div style='font-family:Arial; line-height:1.9; color:#111; max-width:850px; margin:auto;'>
            <div style='background:red; color:white; padding:5px 15px; display:inline-block; border-radius:3px; font-weight:bold;'>{status}</div>
            <img src='{img_url}' style='width:100%; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.2); margin-top:15px;'/>
            <h1 style='font-size:35px;'>{entry.title}</h1>
            <p style='color:#777;'>Verified Source | {time.strftime("%B %d, %Y")}</p>
            <div class='article-body' style='font-size:18px;'>{article_html}</div>
            
            <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:50px; border:3px solid #ff6600;'>
                <h2 style='color:#ff6600; margin-top:0;'>📢 WATCH EXCLUSIVE FOOTAGE & SOURCE</h2>
                <p>The original unedited leaked video and official report for this story are available below. Access them before they are taken down.</p>
                <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block; box-shadow:0 5px 25px rgba(255,102,0,0.5);'>🚀 UNLOCK FULL DATA</a>
            </div>
        </div>
        """

        # 6. पब्लिश करना
        service.posts().insert(blogId=BLOG_ID, body={
            "title": prefix + entry.title,
            "content": final_html,
            "labels": [cat_name.title(), "Trending", "Viral"],
            "searchDescription": entry.title[:150]
        }, isDraft=False).execute()

        print(f"✅ SUCCESS! {status} Post is Live.")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_power_bot()
