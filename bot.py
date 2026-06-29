import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. VIRAL BRAIN: INTERNET TRENDS TRACKER
# ==========================================
def get_world_class_topic():
    # हर बार अलग-अलग केटेगरी सर्च करेगा
    niches = [
        "breaking viral news india", "bollywood leaks gossip", 
        "gta 6 latest updates", "iphone 17 leaks tech", 
        "cricket controversy today", "trending youtube india"
    ]
    query = random.choice(niches)
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            # सबसे ताज़ा खबर उठाना
            return feed.entries[0], query
    except: return None, None

# ==========================================
# 2. THE HUMANIZER: AI ARTICLE WRITER (1200+ Words)
# ==========================================
def generate_powerful_content(headline, cat, g_key):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key.strip()}"
    
    prompt = f"""
    Act as an Investigative Journalist & Viral Content Specialist. 
    Write a 1200-word MASTERPIECE blog post on: '{headline}'.
    
    RULES FOR NO. 1 RANKING:
    1. TONE: Human-like, spicy, emotional. Talk like a person sharing a secret ("I was shocked to find...").
    2. STRUCTURE: Catchy Intro, H2 (The Hidden Reality), H3 (Public Reaction), H3 (Detailed Leak), Conclusion.
    3. NO BOT WORDS: Avoid 'shaping', 'moreover', 'delve', 'comprehensive'.
    4. WORD COUNT: MINIMUM 1000-1200 WORDS.
    5. FAQ: 5 Google-friendly FAQs with deep answers.
    6. SCHEMA: 150-char viral meta description.

    FORMAT: Return ONLY a JSON object (strictly no markdown):
    {{
      "meta": "Search description",
      "article": "HTML content using h2, h3, b, p tags",
      "faq": [ {{"q":"?","a":".."}} ],
      "tags": "trending, viral, news"
    }}
    """
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=90).json()
        raw_text = res['candidates'][0]['content']['parts'][0]['text']
        
        # --- SELF-HEALING JSON REPAIR LOGIC ---
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return None
    except: return None

# ==========================================
# 3. MONETIZATION: SHRINKME API
# ==========================================
def get_money_link(url, s_key):
    try:
        api = f"https://shrinkme.io/api?api={s_key.strip()}&url={url}"
        res = requests.get(api, timeout=15).json()
        return res.get("shortenedUrl", url)
    except: return url

# ==========================================
# 4. CORE MACHINE: THE PUBLISHER
# ==========================================
def run_god_mode_bot():
    print("🔋 Booting Up the World's Most Powerful Blogger Engine...")
    try:
        # Load Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        G_KEY = os.getenv("GEMINI_API").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        # Blogger Auth
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        # 1. वायरल खबर ढूँढना
        entry, niche = get_world_class_topic()
        if not entry: print("⏭️ No news found."); return
        print(f"🔥 Trending Topic: {entry.title}")

        # 2. AI से मास्टर आर्टिकल लिखवाना
        data = generate_powerful_content(entry.title, niche, G_KEY)
        if not data: print("❌ AI Repair Failed."); sys.exit(1)

        # 3. कमाई और फोटो सेटअप
        money_link = get_money_link(entry.link, S_KEY)
        img_url = f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"

        # 4. SEO FAQ Schema Design
        faq_html = "".join([f"<b>Q: {f['q']}</b><p>A: {f['a']}</p>" for f in data.get('faq', [])])
        faq_json = "".join([f'{{"@type":"Question","name":"{f["q"]}","acceptedAnswer":{{"@type":"Answer","text":"{f["a"]}"}}}},' for f in data.get('faq', [])])

        # 5. Premium High-Conversion Design
        final_html = f"""
        <div style='font-family:Segoe UI, sans-serif; line-height:1.9; color:#111; max-width:800px; margin:auto;'>
            <img src='{img_url}' alt='{entry.title}' style='width:100%; border-radius:20px; box-shadow:0 15px 40px rgba(0,0,0,0.2);'/>
            <p style='color:#666; font-size:13px; margin-top:10px;'>⚡ Live Global Update | Updated: {time.strftime("%B %d, %Y")}</p>
            
            <div class='article-content' style='font-size:18px;'>{data['article']}</div>
            
            <div style='background:#f4f4f4; padding:25px; border-radius:15px; margin-top:40px;'>
                <h3 style='color:#e67e22;'>People Also Ask (SEO)</h3>
                {faq_html}
            </div>

            <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:50px; border:3px solid #ff6600;'>
                <h2 style='color:#ff6600; margin-top:0;'>📢 WATCH EXCLUSIVE LEAKED MEDIA</h2>
                <p style='font-size:18px;'>The original unedited raw footage and official verified report for this story are available below. Access them before they are taken down.</p>
                <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:26px; display:inline-block; box-shadow: 0 10px 20px rgba(255,102,0,0.5);'>🚀 UNLOCK FULL DATA</a>
                <p style='font-size:11px; margin-top:15px; color:#666;'>Verification ID: {random.randint(10000,99999)} | Secure Link</p>
            </div>

            <script type="application/ld+json">
            {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{faq_json[:-1]}] }}
            </script>
        </div>
        """

        # 6. पब्लिश करना (DIRECT LIVE)
        print("📤 Sending Power Post to Blogger...")
        service.posts().insert(blogId=BLOG_ID, body={
            "title": "🔴 BREAKING: " + entry.title,
            "content": final_html,
            "labels": [niche.title(), "Viral", "Trending"],
            "searchDescription": data['meta']
        }, isDraft=False).execute()

        print(f"✅ MISSION SUCCESS! World's Best Article is now Live.")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_god_mode_bot()
