import os, requests, feedparser, random, json, sys, re, smtplib, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. AI WRITER (HUMAN-STYLE, 1000 WORDS)
# ==========================================
def generate_human_article(headline, cat, g_key):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key.strip()}"
    
    prompt = f"""
    Act as a Professional Indian Blogger. Write a 1000-word deep-dive news story about: '{headline}'.
    Category: {cat}.
    RULES: 
    1. Tone: Human-like, emotional, and engaging. 
    2. Word Count: Minimum 800-1000 words. 
    3. Structure: Use H2, H3 subheadings, bold text, and bullet points. 
    4. NO AI WORDS: Avoid 'delve', 'moreover', 'comprehensive'.
    5. SEO: Include 5 FAQs at the end.
    Return ONLY a JSON object:
    {{ "article": "HTML content" }}
    """
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=60).json()
        raw = res['candidates'][0]['content']['parts'][0]['text']
        clean_json = re.sub(r'```json|```', '', raw).strip()
        return json.loads(clean_json)
    except: return None

# ==========================================
# 2. EMAIL SENDER (The Bridge to Blogger)
# ==========================================
def send_to_blogger(title, content):
    sender = os.getenv("SENDER_EMAIL").strip()
    password = os.getenv("GMAIL_APP_PASSWORD").strip()
    receiver = os.getenv("BLOGGER_EMAIL").strip()

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = title # ईमेल का सब्जेक्ट ही ब्लॉग का टाइटल बनेगा
    msg.attach(MIMEText(content, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Mail Error: {e}")
        return False

# ==========================================
# 3. MAIN AUTOMATIC ENGINE
# ==========================================
def run_automatic_portal():
    G_KEY = os.getenv("GEMINI_API").strip()
    S_KEY = os.getenv("SHRINKME_API").strip()

    # ट्रेंडिंग सोर्स
    sources = [
        ("Tech", "https://techcrunch.com/feed/"),
        ("Bollywood", "https://www.pinkvilla.com/feed"),
        ("Gaming", "https://www.ign.com/rss/articles/feed"),
        ("India News", "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en")
    ]
    
    random.shuffle(sources)
    cat, rss = sources[0]
    feed = feedparser.parse(rss)
    entry = feed.entries[0]

    print(f"📝 Writing Human Article: {entry.title}")
    data = generate_human_article(entry.title, cat, G_KEY)
    if not data: return

    # Image Extraction
    img_match = re.search(r'<img [^>]*src="([^"]+)"', getattr(entry, 'description', ''))
    img_url = img_match.group(1) if img_match else "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"

    # ShrinkMe Link
    try:
        short_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}").json()
        money_link = short_res.get("shortenedUrl", entry.link)
    except: money_link = entry.link

    # Full HTML Design
    full_html = f"""
    <div style='font-family:Arial; line-height:1.8; color:#111; font-size:18px;'>
        <img src='{img_url}' style='width:100%; border-radius:15px; margin-bottom:20px;'/>
        {data['article']}
        <div style='background:#f9f9f9; padding:30px; border-radius:15px; text-align:center; margin-top:40px; border:2px solid #ff6600;'>
            <h2 style='color:#ff6600;'>📺 Watch Proof & Full Story</h2>
            <a href='{money_link}' style='background:#ff6600; color:#fff; padding:15px 40px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block;'>👉 UNLOCK FULL DATA</a>
        </div>
    </div>
    """

    if send_to_blogger("🔴 BREAKING: " + entry.title, full_html):
        print("✅ SUCCESS! Article sent to Blogger via Email.")
    else:
        print("❌ FAILED to send.")

if __name__ == "__main__":
    run_automatic_portal()
