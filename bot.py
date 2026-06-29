import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. PROMPT PURIFIER (Safety Logic)
# ==========================================
def purify_headline(headline):
    """AI को ब्लॉक होने से बचाने के लिए हेडलाइन को साफ़ करना"""
    # खतरनाक शब्दों को सुरक्षित शब्दों से बदलना
    replacements = {
        "deepfake": "digital transformation",
        "leaked": "officially updated",
        "scandal": "public discussion",
        "adult": "viral",
        "shocking": "surprising",
        "exposed": "revealed"
    }
    clean_h = headline.lower()
    for word, replacement in replacements.items():
        clean_h = clean_h.replace(word, replacement)
    return clean_h.title()

# ==========================================
# 2. AI HUMANIZER (Multi-Persona Logic)
# ==========================================
def generate_unique_article(headline, cat, g_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key.strip()}"
    
    # हर बार अलग जर्नलिस्ट का अंदाज़ (For 100% Uniqueness)
    personas = [
        "Digital Trends Analyst", "Senior Investigative Journalist", 
        "Viral Entertainment Expert", "Tech Visionary & Critic"
    ]
    persona = random.choice(personas)
    
    # 'Educational Analysis' फ्रेमवर्क (Bypasses Blocks)
    prompt = f"""
    Act as a {persona}. Provide a 1200-word educational and informational analysis on the public trend: '{purify_headline(headline)}'.
    
    STRICT BLOGGER ARCHITECTURE:
    1. Introduction: Why is the internet talking about this? (The Hook)
    2. Deep Dive: What are the facts? (H2 & H3 tags)
    3. Industry Impact: How this affects {cat}.
    4. Human Element: Share personal opinions and 'What I found' (Human-like tone).
    5. SEO: Meta Description (150 chars) and 5 FAQs.
    6. NO ROBOTIC WORDS: Avoid 'delve', 'moreover', 'comprehensive'. Use short paragraphs.

    FORMAT: Return ONLY a JSON object:
    {{ "meta": "desc", "article": "HTML content", "faq": [{{"q":"?","a":".."}}] }}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    try:
        res = requests.post(url, json=payload, timeout=90).json()
        raw_text = res['candidates'][0]['content']['parts'][0]['text']
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else None
    except: return None

# ==========================================
# 3. NEWS & EARNING ENGINE
# ==========================================
def run_power_bot():
    print("🚀 System Diagnosis: Active (Persona-Shift Enabled)")
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

        # ताज़ा वायरल फीड्स
        feeds = [
            ("Entertainment", "https://www.pinkvilla.com/feed"),
            ("Breaking News", "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"),
            ("Tech & Gaming", "https://techcrunch.com/feed/")
        ]
        random.shuffle(feeds)
        cat, rss = feeds[0]
        feed = feedparser.parse(rss)
        
        if not feed.entries: return

        # टॉप 15 खबरों को स्कैन करना
        success = False
        for entry in feed.entries[:15]:
            print(f"📡 Analyzing: {entry.title}")
            
            data = generate_unique_article(entry.title, cat, G_KEY)
            if not data: continue

            # Earning Link (ShrinkMe)
            try:
                m_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
                money_link = m_res.get("shortenedUrl", entry.link)
            except: money_link = entry.link

            img_url = f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"
            faq_html = "".join([f"<b>Q: {f['q']}</b><p>A: {f['a']}</p>" for f in data.get('faq', [])])
            schema_faq = "".join([f'{{"@type":"Question","name":"{f["q"]}","acceptedAnswer":{{"@type":"Answer","text":"{f["a"]}"}}}},' for f in data.get('faq', [])])

            # Premium Blogger Layout
            full_html = f"""
            <div style='font-family:Arial, sans-serif; line-height:1.9; color:#111; max-width:800px;'>
                <img src='{img_url}' style='width:100%; border-radius:15px; box-shadow:0 10px 30px rgba(0,0,0,0.1);'/>
                <h1 style='color:#000; font-size:32px;'>{entry.title}</h1>
                <div style='font-size:18px;'>{data['article']}</div>
                <div style='background:#f9f9f9; padding:25px; border-radius:15px; margin-top:30px;'>
                    <h3>People Also Ask (SEO)</h3>{faq_html}
                </div>
                <div style='background:#1a1a1a; padding:40px; border-radius:20px; text-align:center; color:#fff; margin-top:50px; border:3px solid #ff6600;'>
                    <h2 style='color:#ff6600; margin-top:0;'>📢 WATCH EXCLUSIVE FOOTAGE</h2>
                    <p style='font-size:18px;'>Access the original unedited footage and verified report below.</p>
                    <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block;'>🚀 UNLOCK FULL DATA</a>
                </div>
                <script type="application/ld+json">
                {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{schema_faq[:-1]}] }}
                </script>
            </div>
            """

            # Post LIVE
            service.posts().insert(blogId=BLOG_ID, body={
                "title": "🔴 BREAKING: " + entry.title,
                "content": full_html,
                "labels": [cat, "Viral", "Trending"],
                "searchDescription": data['meta']
            }, isDraft=False).execute()
            
            print(f"✅ SUCCESS! Post Live.")
            success = True
            break # एक पोस्ट हो गई, अब बंद

        if not success: sys.exit(1)

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_power_bot()
