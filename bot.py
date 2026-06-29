import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. VIRAL BRAIN (Trends Finder)
# ==========================================
def get_viral_topic():
    queries = ["breaking news india", "bollywood leaked gossip", "tech trends india", "gaming leaks", "viral news today"]
    random.shuffle(queries)
    
    for query in queries:
        rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries:
                return feed.entries, query # सारे आर्टिकल्स भेजें ताकि ब्लॉक होने पर अगला ट्राई हो सके
        except: continue
    return None, None

# ==========================================
# 2. AI HUMANIZER (With Safety Failover)
# ==========================================
def generate_safe_article(headline, cat, g_key):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key.strip()}"
    
    prompt = f"""
    Act as a Professional Viral Blogger. Write a 1200-word deep-dive news article on: '{headline}'. 
    Category: {cat}.
    RULES: 100% Human tone. Use H2, H3 tags. NO BOT WORDS. Include 5 FAQs. 
    FORMAT: Return ONLY a JSON object. No Markdown.
    {{ "meta": "Search desc", "article": "HTML content", "faq": [{{"q":"?","a":".."}}] }}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=90).json()
        
        # --- Safety Check ---
        if 'candidates' not in res or not res['candidates']:
            print(f"⚠️ Safety Block or API Issue for: {headline[:30]}...")
            return None # अगले आर्टिकल की कोशिश करेंगे
            
        raw_text = res['candidates'][0]['content']['parts'][0]['text']
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else None
    except: return None

# ==========================================
# 3. CORE ENGINE (With Auto-Retry Loop)
# ==========================================
def run_master_bot():
    print("🔋 Booting Up God-Mode News Bot...")
    try:
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        G_KEY = os.getenv("GEMINI_API").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        # Auth
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        # 1. ताज़ा खबरें लें
        entries, niche = get_viral_topic()
        if not entries: return

        # 2. आर्टिकल्स पर लूप (अगर एक ब्लॉक हो तो दूसरा ट्राई करो)
        success = False
        for entry in entries[:10]: # टॉप 10 खबरों में से जो भी पास हो जाए
            print(f"🎯 Checking Topic: {entry.title}")
            
            # आर्टिकल जनरेट करना
            data = generate_safe_article(entry.title, niche, G_KEY)
            if not data:
                print("⏭️ AI refused this topic. Trying next news...")
                continue # अगली खबर पर जाएँ

            # --- खबर पास हो गई! अब प्रोसेस पूरा करें ---
            try:
                money_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
                money_link = money_res.get("shortenedUrl", entry.link)
            except: money_link = entry.link
            
            img_url = f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"
            faq_html = "".join([f"<b>Q: {f.get('q','')}</b><p>A: {f.get('a','')}</p>" for f in data.get('faq', [])])
            
            final_html = f"""
            <div style='font-family:Arial; line-height:1.8; color:#111; max-width:800px; margin:auto;'>
                <img src='{img_url}' style='width:100%; border-radius:15px;'/>
                <h1>{entry.title}</h1>
                <div style='font-size:18px;'>{data.get('article','')}</div>
                <div style='background:#f4f4f4; padding:25px; border-radius:15px; margin-top:40px;'>
                    <h3>People Also Ask (SEO)</h3>{faq_html}
                </div>
                <div style='background:#1a1a1a; padding:40px; border-radius:20px; text-align:center; color:#fff; margin-top:50px; border:3px solid #ff6600;'>
                    <h2 style='color:#ff6600;'>📢 WATCH EXCLUSIVE FOOTAGE</h2>
                    <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:15px 40px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block;'>🚀 UNLOCK FULL DATA</a>
                </div>
            </div>
            """

            # 3. पब्लिश
            service.posts().insert(blogId=BLOG_ID, body={
                "title": "🔴 BREAKING: " + entry.title,
                "content": final_html,
                "labels": [niche.title(), "Trending", "Viral"],
                "searchDescription": data.get('meta', entry.title[:150])
            }, isDraft=False).execute()

            print(f"✅ SUCCESS! Posted: {entry.title}")
            success = True
            break # एक पोस्ट हो गई, अब 30 मिनट का इंतज़ार

        if not success:
            print("❌ Could not find any suitable news to post after 10 attempts.")

    except Exception as e:
        print(f"❌ CRITICAL SYSTEM ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_master_bot()
