import os, requests, feedparser, random, json, sys, re, time
from duckduckgo_search import DDGS
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. THE AI AGENT (Unblockable & Human-Like)
# ==========================================
def ai_agent_write(headline, cat):
    """बिना किसी चाबी के Llama 3.1 का उपयोग करके लेख लिखना"""
    print(f"🤖 Agent is researching on: {headline}...")
    
    prompt = f"""
    Act as India's Most Famous News Blogger. Write a 1200-word explosive, engaging, and in-depth blog post on: '{headline}'.
    Topic Category: {cat}.
    
    BLOGGER RULES (Rank #1 on Google):
    1. STYLE: Fast-paced, emotional, spicy, and 100% human-like. Use phrases like "You won't believe this," "I just found out."
    2. STRUCTURE: Use H1 for title, four H2 subheadings (The Truth, The Leak, Public Reaction, The Future), and H3 tags.
    3. NO BOT WORDS: Avoid 'delve', 'moreover', 'comprehensive', 'shaping', 'landmark'.
    4. LENGTH: Minimum 1000-1200 words. Keep paragraphs short (2-3 lines).
    5. FAQ: Include 5 'People Also Ask' questions with long answers.
    6. SEO: Include a viral search description (150 chars) and 10 trending tags.

    FORMAT: Return ONLY the HTML content. No markdown code blocks. Start directly with <h1>.
    """

    for attempt in range(3):
        try:
            with DDGS() as ddgs:
                # DuckDuckGo AI Agent (Llama 3.1 70B)
                response = ddgs.chat(prompt, model='llama-3.1-70b')
                if response and len(response) > 500:
                    return response
                print(f"🔄 Retry {attempt+1}: Agent gave short response.")
        except Exception as e:
            print(f"⚠️ Agent Busy: {e}")
            time.sleep(10)
    return None

# ==========================================
# 2. TREND HUNTER (YouTube & Google Search Trends)
# ==========================================
def get_trending_topic():
    # सबसे वायरल कीवर्ड्स जो आज सर्च हो रहे हैं
    trending_queries = [
        "GTA 6 latest leaks and release date",
        "IPL breaking news today india",
        "Viral Bollywood gossip leaked",
        "Upcoming iPhone 17 shocking leaks",
        "Trending YouTube video india today",
        "New upcoming movies india 2025"
    ]
    query = random.choice(trending_queries)
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            return feed.entries[0], query
    except: return None, None

# ==========================================
# 3. DUPLICATE CHECKER (Never Repost)
# ==========================================
def is_already_posted(title, service, blog_id):
    try:
        posts = service.posts().list(blogId=blog_id, maxResults=15).execute()
        if 'items' in posts:
            for p in posts['items']:
                if title.lower()[:30] in p['title'].lower(): return True
        return False
    except: return False

# ==========================================
# 4. CORE MISSION ENGINE (Unstoppable)
# ==========================================
def run_power_bot():
    print("🔋 POWERING UP DUCKDUCKGO AI AGENT...")
    try:
        # Load Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        # Blogger API Setup
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        # 1. ट्रेंडिंग टॉपिक उठाना
        entry, cat_name = get_trending_topic()
        if not entry: sys.exit(0)

        if is_already_posted(entry.title, service, BLOG_ID):
            print(f"⏭️ Skipping (Already Posted): {entry.title}"); return

        print(f"🔥 Target Topic: {entry.title}")

        # 2. एजेंट से आर्टिकल लिखवाना (The Masterwork)
        article_html = ai_agent_write(entry.title, cat_name)
        if not article_html:
            print("❌ Agent Failure. Retrying next cycle."); sys.exit(1)

        # 3. Earning Link (ShrinkMe)
        try:
            m_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=15).json()
            money_link = m_res.get("shortenedUrl", entry.link)
        except: money_link = entry.link

        # HD Image for Google SEO
        img_url = f"https://source.unsplash.com/1200x675/?{cat_name.replace(' ','')},viral"

        # 4. Final God-Mode Design
        final_html = f"""
        <div style='font-family:Arial, sans-serif; line-height:1.9; color:#111; max-width:850px; margin:auto;'>
            <img src='{img_url}' alt='{entry.title}' style='width:100%; border-radius:20px; box-shadow:0 15px 45px rgba(0,0,0,0.2);'/>
            <br><p style='color:#666; font-size:13px; margin-top:10px;'>⚡ Official Report | Verified Source | Updated: {time.strftime("%B %d, %Y")}</p>
            
            <div class='article-body' style='font-size:19px; margin-top:25px;'>
                {article_html}
            </div>

            <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:60px; border:4px solid #ff6600;'>
                <h2 style='color:#ff6600; margin-top:0; font-size:30px;'>📢 WATCH LEAKED MEDIA & SOURCE</h2>
                <p style='font-size:18px;'>The original high-resolution video and verified PDF report for this story are available on our private server.</p>
                <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:26px; display:inline-block; box-shadow:0 10px 30px rgba(255,102,0,0.5);'>🚀 UNLOCK FULL DATA SOURCE</a>
                <p style='font-size:12px; color:#666; margin-top:20px;'>*Security Verification: Success | 256-bit Encrypted Link</p>
            </div>
        </div>
        """

        # 5. पब्लिश करना (DIRECT LIVE)
        service.posts().insert(blogId=BLOG_ID, body={
            "title": "🔴 BREAKING: " + entry.title,
            "content": final_html,
            "labels": [cat_name.title(), "Viral", "Trending"],
            "searchDescription": entry.title[:150]
        }, isDraft=False).execute()

        print(f"✅ SUCCESS! Agent has posted a MASTERPIECE.")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_power_bot()
