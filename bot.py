import os, requests, feedparser, random, json, sys, re, smtplib, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. THE HUMAN-SEO AI ENGINE (1000+ Words)
# ==========================================
def generate_seo_article(headline, cat, g_key):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key.strip()}"
    
    prompt = f"""
    Act as a World-Class SEO Expert and Viral News Blogger. 
    Topic: '{headline}' (Category: {cat}).
    
    STRICT CONTENT RULES:
    1. LENGTH: Write exactly 1000 to 1200 words. 
    2. TONE: First-person human tone ("I am seeing," "We found"). Use catchy and emotional words.
    3. NO ROBOTIC WORDS: Do not use 'delve', 'moreover', 'comprehensive'.
    4. BLOG STRUCTURE: 
       - Catchy Intro (Hook).
       - H2: The Hidden Truth of {headline}.
       - H3: Why this is Trending in India.
       - H3: Impact on the Industry.
       - Section: "Public Opinion & Social Media Buzz".
    5. FAQ: Generate 5 'People Also Ask' questions with long answers.
    6. KEYWORDS: Naturally include high-search volume tags for {cat}.

    FORMAT: Return ONLY a JSON object:
    {{
      "meta_desc": "string (150 chars)",
      "article": "HTML content using h2, h3, b, i, p, ul, li",
      "faqs": [ {{"q": "...", "a": "..."}} ],
      "keywords": "tag1, tag2, tag3"
    }}
    """
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=70).json()
        raw_text = res['candidates'][0]['content']['parts'][0]['text']
        clean_json = re.sub(r'```json|```', '', raw_text).strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"🔄 AI Healing: Fixing JSON/Prompt Error... {e}")
        return None

# ==========================================
# 2. IMAGE SEO ENGINE (HD & Alt Tags)
# ==========================================
def get_seo_image(entry, cat):
    img_match = re.search(r'<img [^>]*src="([^"]+)"', getattr(entry, 'description', ''))
    if img_match:
        return img_match.group(1)
    # Fallback to high-quality dynamic images
    return f"https://source.unsplash.com/1200x675/?{cat.replace(' ', '')},news"

# ==========================================
# 3. GOOGLE SCHEMA GENERATOR (Top Rank Secret)
# ==========================================
def generate_google_schema(data):
    schema_faq = ""
    for item in data['faqs']:
        schema_faq += f"""
        {{
          "@type": "Question",
          "name": "{item['q']}",
          "acceptedAnswer": {{
            "@type": "Answer",
            "text": "{item['a']}"
          }}
        }},"""
    
    return f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [{schema_faq[:-1]}]
    }}
    </script>
    """

# ==========================================
# 4. SECURE EMAIL DELIVERY (Post via Email)
# ==========================================
def post_to_blogger(title, body):
    sender = os.getenv("SENDER_EMAIL").strip()
    pwd = os.getenv("GMAIL_APP_PASSWORD").strip()
    receiver = os.getenv("BLOGGER_EMAIL").strip()

    msg = MIMEMultipart()
    msg['From'] = f"Viral News AI <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = title
    
    # Adding Labels for Blogger via Subject (if supported by your template)
    # Most Blogger email systems use body content for meta-data
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender, pwd)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Mail Delivery Failed: {e}")
        return False

# ==========================================
# 5. THE MAIN ENGINE
# ==========================================
def run_google_top_machine():
    print("🚀 Booting Ultimate SEO News Machine...")
    G_KEY = os.getenv("GEMINI_API")
    S_KEY = os.getenv("SHRINKME_API")

    # ताज़ा और असली ट्रेंडिंग सोर्सेज
    sources = [
        ("Bollywood Gossip", "https://www.pinkvilla.com/feed"),
        ("Gaming News", "https://www.ign.com/rss/articles/feed"),
        ("YouTube Trends", "https://news.google.com/rss/search?q=trending+india+viral&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Google Trends", "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en")
    ]
    
    random.shuffle(sources)
    cat, rss = sources[0]
    feed = feedparser.parse(rss)
    if not feed.entries: return
    entry = feed.entries[0]

    print(f"🎯 Target Acquired: {entry.title}")
    
    # 1. AI से 1000 शब्दों का SEO आर्टिकल लेना
    data = generate_seo_article(entry.title, cat, G_KEY)
    if not data: return

    # 2. Image SEO
    img_url = get_seo_image(entry, cat)
    
    # 3. ShrinkMe.io Money Link
    try:
        short_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}", timeout=10).json()
        money_link = short_res.get("shortenedUrl", entry.link)
    except: money_link = entry.link

    # 4. Professional Blogger HTML Template (Google Search Console Ready)
    schema_code = generate_google_schema(data)
    
    full_html = f"""
    <div style='font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; line-height:1.8; color:#1a1a1a; max-width:800px; margin:auto;'>
        
        <h1 style='color:#000; font-size:32px; text-transform:capitalize;'>{entry.title}</h1>
        
        <img src='{img_url}' alt='{entry.title}' title='{entry.title}' style='width:100%; border-radius:15px; box-shadow: 0 10px 30px rgba(0,0,0,0.15);'/>
        
        <div style='background:#fcfcfc; padding:15px; border-bottom:3px solid #ff6600; margin-bottom:30px; font-style:italic;'>
            <b>Summary:</b> {data['meta_desc']}
        </div>

        <div class='article-body' style='font-size:18px;'>
            {data['article']}
        </div>

        <hr style='border:0; border-top:1px solid #eee; margin:40px 0;'>

        <div class='faq-section' style='background:#f4f4f4; padding:30px; border-radius:15px;'>
            <h3 style='margin-top:0;'>People Also Ask (FAQs)</h3>
            {"".join([f"<b>Q: {f['q']}</b><p>A: {f['a']}</p>" for f in data['faqs']])}
        </div>

        {schema_code}

        <div style='background:#1a1a1a; padding:40px; border-radius:20px; text-align:center; color:#fff; margin-top:50px; border:2px solid #ff6600;'>
            <h2 style='color:#ff6600; margin-top:0;'>🔥 Exclusive Proof & Full Video Update</h2>
            <p style='font-size:16px;'>We have uploaded the high-resolution leaked media and verified source files to our secure cloud. Access them below:</p>
            <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block; box-shadow: 0 5px 25px rgba(255,102,0,0.5);'>👉 UNLOCK SOURCE DATA</a>
            <p style='font-size:12px; color:#666; margin-top:20px;'>Search Tags: {data['keywords']}</p>
        </div>
    </div>
    """

    # 5. पब्लिश करना
    if post_to_blogger("🔴 BREAKING: " + entry.title, full_html):
        print("✅ MISSION SUCCESS! Article is Live & SEO Optimized.")
    else:
        print("❌ Mission Failed.")

if __name__ == "__main__":
    run_google_top_machine()
