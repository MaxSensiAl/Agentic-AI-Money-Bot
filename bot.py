import os, requests, feedparser, random, json, sys, time, re

# ==========================================
# 1. AI WRITING ENGINE (HUMAN-STYLE & REAL DATA)
# ==========================================
def generate_human_article(headline, cat, g_key, mode="NEW"):
    """Gemini AI से असली, लंबा और इंसानी जैसा आर्टिकल लिखवाना"""
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key}"
    
    style_instr = "BREAKING NEWS" if mode == "NEW" else "LATEST LIVE UPDATE"
    
    prompt = f"""
    Act as a Professional Indian News Blogger and Journalist. 
    Topic: '{headline}' (Category: {cat}).
    Mode: {style_instr}.

    STRICT WRITING RULES (For 100% Human Feel):
    1. WORD COUNT: Write at least 800-1000 words.
    2. TONE: Use a personal, engaging, and slightly emotional tone.
    3. LANGUAGE: Use professional English (direct and spicy). 
    4. NO ROBOTIC WORDS: DO NOT use: 'delve', 'moreover', 'comprehensive', 'shaping', 'in conclusion'.
    5. REAL DATA ONLY: Use only verified news facts. 
    6. STRUCTURE: Start with a 'Hook'. Use H2 and H3 subheadings.
    7. SEO: Write 150-character Meta Description and 5 FAQs.

    FORMAT: Return ONLY a JSON object:
    {{
      "meta_desc": "string",
      "article": "HTML content with h2, h3, b, p tags",
      "faqs": [ {{"q": "...", "a": "..."}} ],
      "tags": ["tag1", "tag2", "tag3"]
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
# 2. OAUTH2 & HISTORY CHECKER (ANTI-DUPLICATE)
# ==========================================
def get_access_token():
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": os.getenv("BC_CLIENT_ID"),
        "client_secret": os.getenv("BC_CLIENT_SECRET"),
        "refresh_token": os.getenv("BC_REFRESH_TOKEN"),
        "grant_type": "refresh_token"
    }
    try:
        res = requests.post(url, data=data).json()
        return res.get("access_token")
    except: return None

def check_post_history(title, token, blog_id):
    """चेक करना कि खबर नई है या उसका अपडेट डालना है"""
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(url, headers=headers, params={"maxResults": 20}).json()
        if 'items' in res:
            for post in res['items']:
                if title.lower()[:25] in post['title'].lower():
                    return "UPDATE"
        return "NEW"
    except: return "NEW"

# ==========================================
# 3. MAIN POSTING MACHINE
# ==========================================
def run_master_engine():
    BLOG_ID = os.getenv("BLOG_ID").strip()
    G_KEY = os.getenv("GEMINI_API")
    S_KEY = os.getenv("SHRINKME_API")
    token = get_access_token()
    
    if not token:
        print("❌ Auth Failed! Check Secrets."); sys.exit(1)

    sources = [
        ("Bollywood", "https://www.pinkvilla.com/feed"),
        ("YouTube Viral", "https://news.google.com/rss/search?q=trending+youtube+india&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Gaming", "https://www.ign.com/rss/articles/feed"),
        ("Google Trends India", "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"),
        ("Tech Updates", "https://techcrunch.com/feed/")
    ]
    
    random.shuffle(sources)
    for cat, rss in sources:
        feed = feedparser.parse(rss)
        for entry in feed.entries[:5]:
            
            mode = check_post_history(entry.title, token, BLOG_ID)
            print(f"💎 Topic Found: {entry.title} | Mode: {mode}")
            
            data = generate_human_article(entry.title, cat, G_KEY, mode)
            if not data: continue

            img_match = re.search(r'<img [^>]*src="([^"]+)"', getattr(entry, 'description', ''))
            img_url = img_match.group(1) if img_match else "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"
            
            try:
                short_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
                money_link = short_res.get("shortenedUrl", entry.link)
            except: money_link = entry.link

            schema_faq = ""
            faq_html = "<div style='margin-top:30px; padding:20px; background:#f9f9f9; border-radius:10px;'><h3>Frequently Asked Questions (FAQ)</h3>"
            for item in data['faqs']:
                faq_html += f"<b>Q: {item['q']}</b><p>A: {item['a']}</p>"
                schema_faq += f"{{\"@type\":\"Question\",\"name\":\"{item['q']}\",\"acceptedAnswer\":{{\"@type\":\"Answer\",\"text\":\"{item['a']}\"}}}},"

            prefix = "🚨 LIVE UPDATE: " if mode == "UPDATE" else "🔴 BREAKING: "
            final_title = prefix + entry.title

            full_html = f"""
            <div style='font-family:Segoe UI, sans-serif; line-height:1.8; color:#111; font-size:18px;'>
                <img src='{img_url}' alt='{entry.title}' style='width:100%; border-radius:15px; box-shadow:0 10px 30px rgba(0,0,0,0.1);'/>
                <p style='color:#777; font-size:14px;'>By Editorial Team | Verified News | {time.strftime("%B %d, %Y")}</p>
                <div class='main-article'>{data['article']}</div>
                {faq_html}
                <script type="application/ld+json">
                {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{schema_faq[:-1]}] }}
                </script>
                <div style='background:#1a1a1a; padding:35px; border-radius:15px; text-align:center; margin-top:40px; color:#fff;'>
                    <h2 style='color:#ff6600;'>Watch Full Proof Coverage</h2>
                    <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:18px 45px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block;'>👉 CLICK TO UNLOCK FULL DATA</a>
                </div>
            </div>
            """

            post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            payload = {
                "kind": "blogger#post",
                "title": final_title,
                "content": full_html,
                "labels": [cat, "Live News", "Trending"] + data['tags'],
                "searchDescription": data['meta_desc']
            }
            
            res = requests.post(post_url, headers=headers, json=payload, params={"isDraft": False})
            if res.status_code == 200:
                print(f"✅ SUCCESS! Live: {final_title}")
                return 
            else:
                print(f"❌ Blogger Error: {res.text}"); sys.exit(1)

if __name__ == "__main__":
    run_master_engine()
