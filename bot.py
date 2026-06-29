import os, requests, feedparser, random, json, sys, re, time

# ==========================================
# 1. AUTO-FIXER: चाबियों को साफ़ करने वाला फंक्शन
# ==========================================
def clean_key(val):
    if not val: return ""
    # फालतू स्पेस, नई लाइन और गलती से पेस्ट किए गए 'https://' को हटाना
    return val.strip().replace("https://", "").replace("http://", "").replace("\n", "").replace("\r", "")

# ==========================================
# 2. गूगल ऑथेंटिकेशन (Access Token Generator)
# ==========================================
def get_access_token():
    url = "https://oauth2.googleapis.com/token"
    
    cid = clean_key(os.getenv("BC_CLIENT_ID"))
    csec = clean_key(os.getenv("BC_CLIENT_SECRET"))
    rtoken = clean_key(os.getenv("BC_REFRESH_TOKEN"))

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
# 3. AI HUMAN WRITER (800-1000 WORDS + SEO)
# ==========================================
def generate_human_article(headline, cat, g_key):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={clean_key(g_key)}"
    
    prompt = f"""
    Act as a Professional Indian Journalist & News Blogger. 
    Topic: '{headline}' (Category: {cat}).
    
    INSTRUCTIONS:
    1. LENGTH: Write 800 to 1000 words. 
    2. HUMAN STYLE: Write like a real person. Use direct, emotional, and spicy language. 
    3. NO AI WORDS: Do not use 'delve', 'moreover', 'comprehensive', 'furthermore'.
    4. STRUCTURE: Use H2/H3 subheadings every 200 words. Use bullet points and bold text.
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
        print(f"⚠️ Gemini Article Error: {e}")
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
                if title.lower()[:20] in post['title'].lower(): return "UPDATE"
        return "NEW"
    except: return "NEW"

# ==========================================
# 5. MAIN MISSION ENGINE
# ==========================================
def run_automatic_portal():
    # Clean Secrets
    BLOG_ID = clean_key(os.getenv("BLOG_ID"))
    G_KEY = clean_key(os.getenv("GEMINI_API"))
    S_KEY = clean_key(os.getenv("SHRINKME_API"))
    
    print("🚀 Starting News Machine...")
    
    token = get_access_token()
    if not token: sys.exit(1)

    # ताज़ा न्यूज़ सोर्सेज
    sources = [
        ("Bollywood", "https://www.pinkvilla.com/feed"),
        ("YouTube Trends", "https://news.google.com/rss/search?q=trending+youtube+india&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Gaming News", "https://www.ign.com/rss/articles/feed"),
        ("Google Trends", "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en")
    ]
    
    random.shuffle(sources)
    cat, rss_url = sources[0]
    feed = feedparser.parse(rss_url)
    if not feed.entries: return
    entry = feed.entries[0]

    # मोड चेक करें (New or Update?)
    mode = check_history(entry.title, token, BLOG_ID)
    print(f"🎯 News Found: {entry.title} | Mode: {mode}")

    # आर्टिकल जनरेट करें
    data = generate_human_article(entry.title, cat, G_KEY)
    if not data: return

    # फोटो निकालें
    img_match = re.search(r'<img [^>]*src="([^"]+)"', getattr(entry, 'description', ''))
    img_url = img_match.group(1) if img_match else "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"

    # ShrinkMe लिंक (Money)
    try:
        short_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}").json()
        money_link = short_res.get("shortenedUrl", entry.link)
    except: money_link = entry.link

    # SEO FAQ Schema Coding
    schema_faq = ""
    faq_html = "<div style='margin-top:30px; padding:20px; background:#f9f9f9; border-radius:10px;'><h3>Frequently Asked Questions</h3>"
    for item in data['faqs']:
        faq_html += f"<b>Q: {item['q']}</b><p>A: {item['a']}</p>"
        schema_faq += f"{{\"@type\":\"Question\",\"name\":\"{item['q']}\",\"acceptedAnswer\":{{\"@type\":\"Answer\",\"text\":\"{item['a']}\"}}}},"

    # Final HTML Design
    prefix = "🚨 LIVE UPDATE: " if mode == "UPDATE" else "🔴 BREAKING: "
    full_html = f"""
    <div style='font-family:Arial, sans-serif; line-height:1.8; color:#111; font-size:18px;'>
        <img src='{img_url}' alt='{entry.title}' title='{entry.title}' style='width:100%; border-radius:15px; box-shadow:0 8px 25px rgba(0,0,0,0.1);'/>
        <p style='color:#777; font-size:14px; margin-top:10px;'>Editorial Post | {time.strftime("%B %d, %Y")}</p>
        
        <div class='main-article'>{data['article']}</div>
        {faq_html}</div>

        <script type="application/ld+json">
        {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{schema_faq[:-1]}] }}
        </script>

        <div style='background:#1a1a1a; padding:35px; border-radius:15px; text-align:center; color:#fff; margin-top:40px; border:2px solid #ff6600;'>
            <h2 style='color:#ff6600; margin-top:0;'>📺 Watch Proof & Full Coverage</h2>
            <p>We have uploaded the leaked footage and official documents below for our readers.</p>
            <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:15px 45px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:20px; display:inline-block;'>👉 UNLOCK FULL DATA SOURCE</a>
        </div>
    </div>
    """

    # POST TO BLOGGER
    post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
    payload = {
        "kind": "blogger#post",
        "title": prefix + entry.title,
        "content": full_html,
        "labels": [cat, "Trending", "Breaking News"] + data.get('tags', []),
        "searchDescription": data['meta_desc']
    }
    
    res = requests.post(post_url, headers={"Authorization": f"Bearer {token}"}, json=payload, params={"isDraft": False})
    
    if res.status_code == 200:
        print(f"✅ SUCCESS! Post Live: {prefix + entry.title}")
    else:
        print(f"❌ Blogger Error: {res.text}")

if __name__ == "__main__":
    run_automatic_machine()
