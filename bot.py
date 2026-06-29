import os, requests, feedparser, random, json, sys, re, smtplib, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. SMART AI ENGINE (1000+ Words & SEO)
# ==========================================
def generate_viral_article(headline, cat, g_key):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key.strip()}"
    
    prompt = f"""
    Act as a Viral Content King. Write a 1200-word explosive news blog on: '{headline}' ({cat}).
    - Use Human-like spicy Hindi-English mix or pure English.
    - Break content into 6-7 subheadings (H2, H3).
    - Add a 'Public Controversy' section.
    - Write 5 FAQs.
    - Provide a 150-char SEO Meta Description.
    FORMAT: Return ONLY JSON:
    {{ "article": "HTML content", "meta": "description", "tags": "tag1, tag2" }}
    """
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=80).json()
        raw_text = res['candidates'][0]['content']['parts'][0]['text']
        clean_json = re.sub(r'```json|```', '', raw_text).strip()
        return json.loads(clean_json)
    except: return None

# ==========================================
# 2. EARNING ENGINE (ShrinkMe + CTA Design)
# ==========================================
def get_earning_link(original_url, s_key):
    try:
        # ShrinkMe API Call
        api_url = f"https://shrinkme.io/api?api={s_key.strip()}&url={original_url}"
        res = requests.get(api_url, timeout=15).json()
        if res.get("status") == "success":
            return res.get("shortenedUrl")
        return original_url
    except:
        return original_url

# ==========================================
# 3. NEWS RECOVERY (Never Fails)
# ==========================================
def fetch_trending_topic():
    sources = [
        ("Bollywood", "https://www.pinkvilla.com/feed"),
        ("Gaming", "https://www.ign.com/rss/articles/feed"),
        ("YouTube Viral", "https://news.google.com/rss/search?q=trending+india+youtube&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Breaking News", "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en")
    ]
    random.shuffle(sources)
    for cat, rss in sources:
        try:
            feed = feedparser.parse(rss)
            if feed.entries: return feed.entries[0], cat
        except: continue
    return None, None

# ==========================================
# 4. SECURE DELIVERY ENGINE
# ==========================================
def send_to_blogger(title, content):
    sender = os.getenv("SENDER_EMAIL").strip()
    pwd = os.getenv("GMAIL_APP_PASSWORD").strip()
    receiver = os.getenv("BLOGGER_EMAIL").strip()

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = title
    msg.attach(MIMEText(content, 'html'))

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender, pwd)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Mail Error: {e}")
        return False

# ==========================================
# 5. MAIN ORCHESTRATOR
# ==========================================
def start_bot():
    print("🚀 Booting Earning Machine...")
    G_KEY = os.getenv("GEMINI_API")
    S_KEY = os.getenv("SHRINKME_API")

    # खबर और कमाई वाला लिंक
    entry, cat = fetch_trending_topic()
    if not entry: return
    
    print(f"🔥 Found: {entry.title}")
    money_link = get_earning_link(entry.link, S_KEY)

    # AI आर्टिकल
    data = generate_viral_article(entry.title, cat, G_KEY)
    if not data: return

    # Image Extraction
    img_match = re.search(r'<img [^>]*src="([^"]+)"', getattr(entry, 'description', ''))
    img_url = img_match.group(1) if img_match else f"https://source.unsplash.com/1200x675/?{cat},viral"

    # --- Full Premium HTML Design (High Clicks) ---
    final_html = f"""
    <div style='font-family: Arial; line-height:1.8; color:#222; max-width:700px; margin:auto;'>
        <h1 style='font-size:30px; color:#d35400;'>{entry.title}</h1>
        <img src='{img_url}' style='width:100%; border-radius:15px; box-shadow:0 10px 30px rgba(0,0,0,0.1);'/>
        
        <div style='margin-top:20px;'>
            {data['article']}
        </div>

        <div style='background:#fff0f0; border:2px dashed #ff4444; padding:30px; border-radius:20px; text-align:center; margin-top:50px;'>
            <h2 style='color:#ff0000; margin-top:0;'>🛑 LEAKED MEDIA & SOURCE DATA</h2>
            <p style='font-size:18px;'>The original unedited video and full PDF report are available for a limited time. Click below to verify.</p>
            <a href='{money_link}' rel='nofollow' style='background:#ff0000; color:#fff; padding:20px 45px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:24px; display:inline-block; box-shadow:0 10px 20px rgba(255,0,0,0.4);'>👉 UNLOCK FULL DATA SOURCE</a>
            <p style='font-size:12px; color:#999; margin-top:15px;'>*Link secure. Verified by ViralBot Security.</p>
        </div>
        
        <p style='color:white; font-size:1px;'>Tags: {data['tags']}, google search, trending news</p>
    </div>
    """

    # पब्लिश करना
    if send_to_blogger("🚨 BREAKING: " + entry.title, final_html):
        print(f"✅ SUCCESS! Post is LIVE and Earning is Active.")
    else:
        print("❌ Failed to send email.")

if __name__ == "__main__":
    start_bot()
