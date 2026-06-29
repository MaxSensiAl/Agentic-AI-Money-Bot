import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. BRAIN: TRENDING TOPIC FINDER (Interent Tracker)
# ==========================================
def get_most_viral_topic():
    """यह फंक्शन इंटरनेट पर सबसे ज़्यादा सर्च होने वाली चीज़ें ढूँढता है"""
    search_queries = [
        "trending news india", "bollywood leaked gossip", "breaking news today", 
        "youtube trending india", "latest tech launch india", "gaming leaks"
    ]
    query = random.choice(search_queries)
    # Google News RSS with Dynamic Search
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            # टॉप 5 में से कोई एक ताज़ा खबर उठाना
            return feed.entries[random.randint(0, 4)], query
    except:
        return None, None

# ==========================================
# 2. AI WRITER: THE HUMAN JOURNALIST (1200+ Words)
# ==========================================
def write_viral_article(headline, cat, g_key):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key.strip()}"
    
    prompt = f"""
    Act as the World's #1 Viral News Blogger. Your goal is to rank #1 on Google.
    Topic: '{headline}' (Category: {cat}).
    
    STRICT CONTENT ARCHITECTURE:
    1. Hook: Start with a shocking revelation or emotional hook. (100 words)
    2. Deep Dive: Write 1200 words of original analysis. Use first-person ("I found", "Our sources say").
    3. NO BOT WORDS: Strictly DO NOT use 'delve', 'moreover', 'comprehensive', 'era', 'shaping'. 
    4. Spice: Keep it fast-paced, direct, and slightly controversial (Indian style).
    5. Hierarchy: Use one H1, four H2s, and six H3 subheadings.
    6. Keywords: Injected high-volume SEO keywords naturally.
    7. FAQ: 5 'People Also Ask' questions with long, helpful answers.
    8. Meta: Write a 150-char viral meta description.
    
    FORMAT: Return ONLY a JSON object:
    {{ "article": "HTML content", "meta": "description", "tags": "tag1, tag2", "faq_schema": [ {{"q":"?","a":".."}} ] }}
    """
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=90).json()
        raw_text = res['candidates'][0]['content']['parts'][0]['text']
        clean_json = re.sub(r'```json|```', '', raw_text).strip()
        return json.loads(clean_json)
    except: return None

# ==========================================
# 3. EARNINGS: SHRINKME LINK INJECTOR
# ==========================================
def get_money_link(url, s_key):
    try:
        res = requests.get(f"https://shrinkme.io/api?api={s_key.strip()}&url={url}", timeout=15).json()
        return res.get("shortenedUrl", url)
    except: return url

# ==========================================
# 4. DUPLICATE CHECKER (Anti-Spam)
# ==========================================
def is_already_on_blog(title, service, blog_id):
    posts = service.posts().list(blogId=blog_id, maxResults=15).execute()
    if 'items' in posts:
        for p in posts['items']:
            if title.lower()[:30] in p['title'].lower(): return True
    return False

# ==========================================
# 5. CORE ENGINE (The Orchestrator)
# ==========================================
def run_power_blogger():
    print("🔋 Powering Up the World's Most Powerful Blogger Engine...")
    try:
        # Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        G_KEY = os.getenv("GEMINI_API").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        # Auth
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        # 1. वायरल टॉपिक ढूंढना
        entry, cat_name = get_most_viral_topic()
        if not entry: sys.exit(0)
        
        if is_already_on_blog(entry.title, service, BLOG_ID):
            print(f"⏭️ Old news skipped: {entry.title}"); return

        print(f"🔥 Trending Now: {entry.title}")

        # 2. AI से 1200 शब्दों का मास्टर आर्टिकल लिखवाना
        data = write_viral_article(entry.title, cat_name, G_KEY)
        if not data: sys.exit(1)

        # 3. कमाई और इमेज सेटअप
        money_link = get_money_link(entry.link, S_KEY)
        img_url = f"https://source.unsplash.com/1200x675/?{cat_name.replace(' ','')},viral,news"
        
        # 4. Google Rich Snippets (SEO Schema)
        faq_html = "".join([f"<b>Q: {f['q']}</b><p>A: {f['a']}</p>" for f in data['faq_schema']])
        schema_json = "".join([f'{{"@type":"Question","name":"{f["q"]}","acceptedAnswer":{{"@type":"Answer","text":"{f["a"]}"}}}},' for f in data['faq_schema']])

        # 5. High-Conversion HTML Design
        full_html = f"""
        <div style='font-family:Arial; line-height:1.8; color:#111; max-width:800px; margin:auto;'>
            <img src='{img_url}' alt='{entry.title}' style='width:100%; border-radius:20px; box-shadow:0 10px 40px rgba(0,0,0,0.2);'/>
            <div style='margin-top:25px;'>{data['article']}</div>
            
            <div style='background:#f9f9f9; padding:30px; border-radius:15px; margin-top:40px;'>
                <h3 style='color:#ff6600;'>People Also Ask (SEO)</h3>
                {faq_html}
            </div>

            <div style='background:#1a1a1a; padding:40px; border-radius:20px; text-align:center; color:#fff; margin-top:50px; border:3px solid #ff6600;'>
                <h2 style='color:#ff6600; margin-top:0;'>📢 WATCH EXCLUSIVE FOOTAGE & PROOF</h2>
                <p style='font-size:18px;'>The full original documents and raw video for this report are linked below. Access our private server now.</p>
                <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:26px; display:inline-block; box-shadow:0 5px 25px rgba(255,102,0,0.5);'>🚀 UNLOCK FULL DATA</a>
            </div>

            <script type="application/ld+json">
            {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{schema_json[:-1]}] }}
            </script>
        </div>
        """

        # 6. पब्लिश करना (LIVE)
        service.posts().insert(blogId=BLOG_ID, body={
            "kind": "blogger#post",
            "title": "🔴 BREAKING: " + entry.title,
            "content": full_html,
            "labels": [cat_name, "Trending", "Live Update", "Viral"],
            "searchDescription": data['meta']
        }, isDraft=False).execute()

        print(f"✅ POWER POST PUBLISHED! Google Top Ranking Initiated.")

    except Exception as e:
        print(f"❌ SYSTEM ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_power_blogger()
