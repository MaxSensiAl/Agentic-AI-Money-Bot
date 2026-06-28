import os, requests, feedparser, random, json, sys, time, re

# ==========================================
# 1. AI WRITING ENGINE (HUMAN-STYLE & REAL DATA)
# ==========================================
def generate_human_article(headline, cat, g_key, mode="NEW"):
    """Gemini AI से असली, लंबा और इंसानी जैसा आर्टिकल लिखवाना"""
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key}"
    
    # मोड के हिसाब से प्रॉम्प्ट बदलना
    style_instr = "BREAKING NEWS" if mode == "NEW" else "LATEST LIVE UPDATE"
    
    prompt = f"""
    Act as a Professional Indian News Blogger and Journalist. 
    Topic: '{headline}' (Category: {cat}).
    Mode: {style_instr}.

    STRICT WRITING RULES (For 100% Human Feel):
    1. WORD COUNT: Write at least 800-1000 words of deep, engaging content.
    2. TONE: Use a personal, direct, and slightly emotional tone (First person).
    3. LANGUAGE: Use professional English, but keep the vibe like a popular Indian viral blog.
    4. NO ROBOTIC WORDS: Strictly DO NOT use: 'delve', 'moreover', 'comprehensive', 'shaping', 'in conclusion', 'furthermore'.
    5. REAL DATA ONLY: Use only verified news facts. Do not make up rumors.
    6. STRUCTURE: Start with a spicy/emotional hook. Use H2 and H3 subheadings every 200 words.
    7. SEO: Write a viral 150-character Meta Description. Include 5 'People Also Ask' FAQs with long answers.

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
        # Clean JSON from AI markdown code blocks
        clean_json = re.sub(r'```json|```', '', raw_text).strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"⚠️ Gemini Error: {e}")
        return None

# ==========================================
# 2. OAUTH2 & HISTORY CHECKER (ANTI-DUPLICATE)
# ==========================================
def get_access_token():
    """Refresh Token का उपयोग करके नया Access Token प्राप्त करना"""
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": os.getenv("BC_CLIENT_ID"),
        "client_secret": os.getenv("BC_CLIENT_SECRET"),
        "refresh_token": os.getenv("BC_REFRESH_TOKEN"),
        "grant_type": "refresh_token"
    }
    try:
        res = requests.post(url, data=data)
        if res.status_code != 200:
            print(f"❌ Google API Error: {res.text}")
            return None
        return res.json().get("access_token")
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def check_post_history(title, token, blog_id):
    """चेक करना कि खबर नई है, पुरानी है, या उसका अपडेट डालना है"""
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(url, headers=headers, params={"maxResults": 15}).json()
        if 'items' in res:
            for post in res['items']:
                # अगर टाइटल का हिस्सा मैच हो, तो इसे 'Update' माना जाएगा
                if title.lower()[:20] in post['title'].lower():
                    return "UPDATE"
        return "NEW"
    except: return "NEW"

# ==========================================
# 3. MAIN POSTING MACHINE
# ==========================================
def run_master_engine():
    # Secrets प्राप्त करना
    BLOG_ID = os.getenv("BLOG_ID").strip()
    G_KEY = os.getenv("GEMINI_API")
    S_KEY = os.getenv("SHRINKME_API")
    token = get_access_token()
    
    if not token:
        print("❌ Auth Failed! Possible cause: Invalid Secrets or Refresh Token."); sys.exit(1)

    # टॉप ट्रेंडिंग न्यूज़ सोर्सेज
    sources = [
        ("Bollywood", "https://www.pinkvilla.com/feed"),
        ("YouTube Trends", "https://news.google.com/rss/search?q=trending+youtube+india&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Gaming News", "https://www.ign.com/rss/articles/feed"),
        ("Google Trends", "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"),
        ("Tech Updates", "https://techcrunch.com/feed/")
    ]
    
    random.shuffle(sources)
    for cat, rss in sources:
        print(f"Checking {cat} Feed...")
        feed = feedparser.parse(rss)
        if not feed.entries: continue
        
        for entry in feed.entries[:5]: # ताज़ा खबरें उठाना
            
            # इतिहास चेक करें (New Post or Update?)
            mode = check_post_history(entry.title, token, BLOG_ID)
            print(f"🎯 Found: {entry.title} | Mode: {mode}")
            
            # AI आर्टिकल जनरेट करना
            data = generate_human_article(entry.title, cat, G_KEY, mode)
            if not data: continue

            # इमेज एक्सट्रैक्शन
            img_match = re.search(r'<img [^>]*src="([^"]+)"', getattr(entry, 'description', ''))
            img_url = img_match.group(1) if img_match else "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"
            
            # ShrinkMe लिंक (Money Making)
            try:
                short_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
                money_link = short_res.get("shortenedUrl", entry.link)
            except: money_link = entry.link

            # FAQ Schema SEO कोडिंग
            schema_faq = ""
            faq_html = "<div class='seo-faq' style='margin-top:40px; padding:25px; background:#f9f9f9; border-radius:12px; border:1px solid #ddd;'><h3>Frequently Asked Questions</h3>"
            for item in data['faqs']:
                faq_html += f"<b>Q: {item['q']}</b><p>A: {item['a']}</p>"
                schema_faq += f"{{\"@type\":\"Question\",\"name\":\"{item['q']}\",\"acceptedAnswer\":{{\"@type\":\"Answer\",\"text\":\"{item['a']}\"}}}},"

            # टाइटल प्रिफिक्स
            prefix = "🚨 LIVE UPDATE: " if mode == "UPDATE" else "🔴 BREAKING: "
            final_title = prefix + entry.title

            # Final HTML Design (Professional Blogger Look)
            full_html = f"""
            <div style='font-family:"Segoe UI", Roboto, sans-serif; line-height:1.8; color:#111; font-size:18px;'>
                <div style='background:red; color:white; padding:5px 15px; display:inline-block; border-radius:3px; font-weight:bold; margin-bottom:15px;'>{mode}</div>
                
                <img src='{img_url}' alt='{entry.title}' title='{entry.title}' style='width:100%; border-radius:15px; box-shadow:0 10px 30px rgba(0,0,0,0.1);'/>
                
                <p style='color:#777; font-size:14px; margin-top:10px;'>Verified Editorial Post | {time.strftime("%B %d, %Y")}</p>
                
                <div class='main-article' style='margin-top:25px;'>
                    {data['article']}
                </div>

                {faq_html}</div>
                
                <script type="application/ld+json">
                {{
                  "@context": "https://schema.org",
                  "@type": "FAQPage",
                  "mainEntity": [{schema_faq[:-1]}]
                }}
                </script>

                <div style='background:#1a1a1a; padding:35px; border-radius:15px; text-align:center; margin-top:45px; color:#fff; border: 2px solid #ff6600;'>
                    <h2 style='color:#ff6600; margin-top:0;'>📺 Watch Proof & Full Coverage</h2>
                    <p>Access the exclusive raw footage, verified documents, and high-resolution media below.</p>
                    <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:18px 45px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block; box-shadow:0 4px 15px rgba(255,102,0,0.4);'>👉 UNLOCK FULL DATA SOURCE</a>
                    <p style='font-size:11px; margin-top:15px; color:#666;'>*Source link verified by security protocols.</p>
                </div>
            </div>
            """

            # Blogger API Request
            post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            payload = {
                "kind": "blogger#post",
                "title": final_title,
                "content": full_html,
                "labels": [cat, "Trending", "Live News"] + data['tags'],
                "searchDescription": data['meta_desc']
            }
            
            res = requests.post(post_url, headers=headers, json=payload, params={"isDraft": False})
            if res.status_code == 200:
                print(f"✅ SUCCESS! Post Live: {final_title}")
                return # 30 मिनट के बाद अगली पोस्ट के लिए बाहर निकलें
            else:
                print(f"❌ Blogger Error: {res.text}")
                sys.exit(1)

if __name__ == "__main__":
    run_master_engine()
