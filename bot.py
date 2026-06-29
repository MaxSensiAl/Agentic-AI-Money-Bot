import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. VIRAL BRAIN (Trends Finder)
# ==========================================
def get_viral_topic():
    queries = [
        "breaking news india", "bollywood news today", 
        "ipl cricket controversy", "tech leaks india", "viral trending news"
    ]
    random.shuffle(queries)
    for q in queries:
        rss_url = f"https://news.google.com/rss/search?q={q.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries: return feed.entries, q
        except: continue
    return None, None

# ==========================================
# 2. AI HUMANIZER (1200+ Words + Human Vibe)
# ==========================================
def generate_powerful_article(headline, cat, g_key):
    # Gemini v1beta is more stable for large JSON
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key.strip()}"
    
    prompt = f"""
    Act as a World-Class Viral Journalist. Topic: '{headline}' (Category: {cat}).
    TASK: Write a 1200-word MASTERPIECE blog post.
    RULES: 
    - Tone: Spicy, Human, Emotional. Talk like you are revealing a secret.
    - Word Count: MINIMUM 1000 WORDS.
    - NO ROBOTIC WORDS. Use short, punchy paragraphs.
    - SEO: Include H1, H2, H3 tags. Add 5 'People Also Ask' FAQs.
    - Return ONLY a JSON object:
    {{ "meta": "150 char SEO desc", "article": "Full HTML Content", "faq": [{{"q":"?","a":".."}}] }}
    """
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=90).json()
        if 'candidates' not in res: 
            print(f"⚠️ Safety Block for: {headline[:30]}"); return None
            
        raw_text = res['candidates'][0]['content']['parts'][0]['text']
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else None
    except: return None

# ==========================================
# 3. CORE MISSION ENGINE
# ==========================================
def run_master_engine():
    print("🔋 INITIALIZING SYSTEM...")
    try:
        # Load Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        G_KEY = os.getenv("GEMINI_API").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        # Auth
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        # 1. खबर ढूँढना
        entries, niche = get_viral_topic()
        if not entries: print("❌ RSS Feed Error"); return

        success_flag = False
        for entry in entries[:10]: # 10 कोशिशें करेगा जब तक एक खबर पास न हो जाए
            print(f"🎯 Trying Topic: {entry.title}")

            # 2. AI से लिखवाना
            data = generate_powerful_article(entry.title, niche, G_KEY)
            if not data: continue

            # 3. कमाई और इमेज
            try:
                m_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=15).json()
                money_link = m_res.get("shortenedUrl", entry.link)
            except: money_link = entry.link
            
            img_url = f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"
            faq_html = "".join([f"<b>Q: {f['q']}</b><p>A: {f['a']}</p>" for f in data.get('faq', [])])
            schema_faq = "".join([f'{{"@type":"Question","name":"{f["q"]}","acceptedAnswer":{{"@type":"Answer","text":"{f["a"]}"}}}},' for f in data.get('faq', [])])

            # 4. Premium High-Conversion Template
            full_html = f"""
            <div style='font-family:Arial, sans-serif; line-height:1.9; color:#111; max-width:800px; margin:auto;'>
                <img src='{img_url}' alt='{entry.title}' style='width:100%; border-radius:20px; box-shadow:0 10px 40px rgba(0,0,0,0.2);'/>
                <h1 style='color:#000; font-size:32px;'>{entry.title}</h1>
                <div class='main-body' style='font-size:18px;'>{data['article']}</div>
                <div style='background:#f4f4f4; padding:25px; border-radius:15px; margin-top:40px;'>
                    <h3>People Also Ask (SEO)</h3>{faq_html}
                </div>
                <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:50px; border:3px solid #ff6600;'>
                    <h2 style='color:#ff6600; margin-top:0;'>📢 WATCH EXCLUSIVE LEAKED VIDEO</h2>
                    <p style='font-size:18px;'>The full original documents and raw video for this story are available below. UNLOCK NOW.</p>
                    <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block;'>🚀 UNLOCK FULL DATA SOURCE</a>
                    <p style='font-size:11px; margin-top:15px; color:#666;'>Verification: {random.randint(10000,99999)} | Secure Link</p>
                </div>
                <script type="application/ld+json">
                {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{schema_faq[:-1]}] }}
                </script>
            </div>
            """

            # 5. पब्लिश करना (DIRECT LIVE FORCE)
            print("📤 SENDING REQUEST TO BLOGGER...")
            try:
                res = service.posts().insert(blogId=BLOG_ID, body={
                    "title": "🔴 BREAKING: " + entry.title,
                    "content": full_html,
                    "labels": [niche.title(), "Trending", "Live"],
                    "searchDescription": data['meta']
                }, isDraft=False).execute()
                
                if 'id' in res:
                    print(f"✅ SUCCESS! Post is LIVE: {res.get('url')}")
                    success_flag = True
                    break # एक पोस्ट हो गई, काम खत्म।
            except Exception as blogger_err:
                print(f"❌ Blogger Rejected: {blogger_err}")
                continue

        if not success_flag:
            print("❌ System failed to post after all attempts.")
            sys.exit(1)

    except Exception as e:
        print(f"❌ CRITICAL ENGINE FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_master_engine()
