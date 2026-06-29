import os, requests, feedparser, random, json, sys, re, time

# ==========================================
# 1. AUTO-FIXER (Secrets की सफाई करने वाला सिस्टम)
# ==========================================
def clean(val):
    if not val: return ""
    # फालतू स्पेस, न्यू लाइन और गलती से आए 'https://' को हटाना
    return str(val).strip().replace("https://", "").replace("http://", "").replace("\n", "").replace("\r", "")

# ==========================================
# 2. GOOGLE OAUTH2 (Access Token Generator)
# ==========================================
def get_access_token():
    url = "https://oauth2.googleapis.com/token"
    cid = clean(os.getenv("BC_CLIENT_ID"))
    csec = clean(os.getenv("BC_CLIENT_SECRET"))
    rtoken = clean(os.getenv("BC_REFRESH_TOKEN"))

    data = {
        "client_id": cid,
        "client_secret": csec,
        "refresh_token": rtoken,
        "grant_type": "refresh_token"
    }
    try:
        res = requests.post(url, data=data)
        if res.status_code != 200:
            print(f"❌ AUTH FAILED: {res.text}")
            return None
        return res.json().get("access_token")
    except Exception as e:
        print(f"❌ Auth Connection Error: {e}")
        return None

# ==========================================
# 3. AI जर्नलिस्ट (Human-Style, 1000 Words)
# ==========================================
def generate_human_article(headline, cat, g_key, mode="NEW"):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={clean(g_key)}"
    
    update_text = "This is a LATEST LIVE UPDATE to a trending story." if mode == "UPDATE" else "This is a fresh BREAKING NEWS story."

    prompt = f"""
    Act as a Professional Indian News Blogger & SEO Specialist. 
    Topic: '{headline}' (Category: {cat}).
    Mode: {update_text}.

    INSTRUCTIONS:
    1. LENGTH: Write 800 to 1000 words. 
    2. HUMAN STYLE: Write like a real person. Use direct, emotional language (I, Me, My). 
    3. NO BOT WORDS: Strictly DO NOT use 'delve', 'moreover', 'comprehensive', 'furthermore'.
    4. STRUCTURE: Catchy introduction, H2 and H3 subheadings every 200 words.
    5. SEO: Include 5 'People Also Ask' FAQs with detailed answers.
    6. META: Write a 150-char viral search description.
    
    FORMAT: Return ONLY a JSON object:
    {{
      "meta_desc": "string",
      "article": "HTML content with h2, h3, b, p tags",
      "faqs": [ {{"q": "...", "a": "..."}} ],
      "tags": ["tag1", "tag2"]
    }}
    """
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=60).json()
        raw_text = res['candidates'][0]['content']['parts'][0]['text']
        clean_json = re.sub(r'```json|```', '', raw_text).strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"⚠️ Gemini Error: {e}")
        return None

# ==========================================
# 4. DUPLICATE & HISTORY CHECKER
# ==========================================
def check_history(title, token, blog_id):
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(url, headers=headers, params={"maxResults": 10}).json()
        if 'items' in res:
            for post in res['items']:
                # अगर टाइटल का हिस्सा मैच हो, तो इसे 'Update' मोड में डालेंगे
                if title.lower()[:20] in post['title'].lower(): return "UPDATE"
        return "NEW"
    except: return "NEW"

# ==========================================
# 5. MAIN POSTING MACHINE (The Engine)
# ==========================================
def run_ultimate_news_machine():
    # Clean Secrets
    BLOG_ID = clean(os.getenv("BLOG_ID"))
    G_KEY = clean(os.getenv("GEMINI_API"))
    S_KEY = clean(os.getenv("SHRINKME_API"))
    
    print("🚀 Starting Automatic News Machine...")
    
    token = get_access_token()
    if not token: sys.exit(1)

    # 100% Real & Trending Sources
    sources = [
        ("Bollywood", "https://www.pinkvilla.com/feed"),
        ("YouTube Viral", "https://news.google.com/rss/search?q=trending+youtube+india&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Google Trends", "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"),
        ("Gaming", "https://www.ign.com/rss/articles/feed"),
        ("Tech", "https://techcrunch.com/feed/")
    ]
    
    random.shuffle(sources)
    for cat, rss_url in sources:
        feed = feedparser.parse(rss_url)
        if not feed.entries: continue
        
        entry = feed.entries[0] # ताज़ा खबर उठाना
        mode = check_history(entry.title, token, BLOG_ID)
        
        print(f"🎯 News Found: {entry.title} | Mode: {mode}")

        # आर्टिकल जनरेट करना
        data = generate_human_article(entry.title, cat, G_KEY, mode)
        if not data: continue

        # इमेज एक्सट्रैक्शन + SEO Alt Tags
        img_match = re.search(r'<img [^>]*src="([^"]+)"', getattr(entry, 'description', ''))
        img_url = img_match.group(1) if img_match else "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"

        # ShrinkMe लिंक (Income)
        try:
            short_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
            money_link = short_res.get("shortenedUrl", entry.link)
        except: money_link = entry.link

        # FAQ Schema SEO Coding
        schema_faq = ""
        faq_html = "<div style='margin-top:30px; background:#f9f9f9; padding:20px; border-radius:10px;'><h3>Frequently Asked Questions</h3>"
        for item in data['faqs']:
            faq_html += f"<b>Q: {item['q']}</b><p>A: {item['a']}</p>"
            schema_faq += f"{{\"@type\":\"Question\",\"name\":\"{item['q']}\",\"acceptedAnswer\":{{\"@type\":\"Answer\",\"text\":\"{item['a']}\"}}}},"

        # प्रोफेशनल डिज़ाइन
        prefix = "🚨 LIVE UPDATE: " if mode == "UPDATE" else "🔴 BREAKING: "
        full_html = f"""
        <div style='font-family:Arial, sans-serif; line-height:1.8; color:#111; font-size:18px;'>
            <div style='background:red; color:white; padding:5px 15px; display:inline-block; border-radius:3px; font-weight:bold; margin-bottom:15px;'>{mode}</div>
            <img src='{img_url}' alt='{entry.title}' title='{entry.title}' style='width:100%; border-radius:15px; box-shadow:0 8px 25px rgba(0,0,0,0.1);'/>
            <p style='color:#777; font-size:14px; margin-top:10px;'>Verified News | {time.strftime("%B %d, %Y")}</p>
            
            <div class='main-article'>{data['article']}</div>
            
            {faq_html}</div>
            
            <script type="application/ld+json">
            {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{schema_faq[:-1]}] }}
            </script>

            <div style='background:#1a1a1a; padding:35px; border-radius:15px; text-align:center; color:#fff; margin-top:45px; border: 2px solid #ff6600;'>
                <h2 style='color:#ff6600; margin-top:0;'>📺 Watch Proof & Full Story</h2>
                <p>Access the exclusive footage, raw data, and official reports below for our readers.</p>
                <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:18px 45px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block; box-shadow:0 4px 15px rgba(255,102,0,0.4);'>👉 UNLOCK FULL DATA SOURCE</a>
            </div>
        </div>
        """

        # ब्लॉगर पर पोस्ट पब्लिश करना
        post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        payload = {
            "kind": "blogger#post",
            "title": prefix + entry.title,
            "content": full_html,
            "labels": [cat, "Trending News", "Live Updates"] + data.get('tags', []),
            "searchDescription": data['meta_desc']
        }
        
        res = requests.post(post_url, headers=headers, json=payload, params={"isDraft": False})
        if res.status_code == 200:
            print(f"✅ SUCCESS! Live: {prefix + entry.title}")
            return # हर 30 मिनट में सिर्फ एक शानदार पोस्ट
        else:
            print(f"❌ Blogger Error: {res.text}")
            sys.exit(1)

# ऐप चालू करना
if __name__ == "__main__":
    run_ultimate_news_machine()
