import os, smtplib, requests, feedparser, random, json
from email.message import EmailMessage
from datetime import datetime

def get_pro_human_article(headline, category, g_key):
    """AI को मजबूर करना कि वह 600-800 शब्दों का असली और गहरा न्यूज़ आर्टिकल लिखे"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    
    # अलग-अलग राइटिंग स्टाइल ताकि गूगल को 'इंसानी' अहसास हो
    styles = ["Senior Editor", "Viral Journalist", "Tech Geek", "Cinema Critic"]
    style = random.choice(styles)
    
    prompt = f"""Act as a professional {style}. 
    Write a DEEP, ENGAGING, and 100% UNIQUE news article about: "{headline}" in category {category}.
    
    STRUCTURE RULES:
    1. Start with a shocking or catchy sub-headline (H2).
    2. Write a 100-word introduction setting the stage.
    3. Detailed Body: Break down the full story, include 'hidden facts' and background.
    4. Bullet Points: Use <ul> and <li> for 'Key Highlights'.
    5. Social Buzz: Create a <blockquote> with what people are saying on X/Twitter with emojis.
    6. Future Outlook: What happens next?
    7. FAQ Section: 2 questions and answers related to this news.
    
    FORMATTING:
    - Use HTML tags: <h2>, <h3>, <b>, <ul>, <li>, <blockquote>.
    - Professional, exciting tone. No 'In conclusion'. No AI robot talk.
    - Write at least 600 words. Return ONLY HTML body."""
    
    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=35).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Gemini Error: {e}")
        return f"<h2>Breaking Update: {headline}</h2><p>Latest verified reports on {category} suggest a major shift in trends. Our team is tracking real-time data to bring you the full investigation soon.</p>"

def run_viral_machine():
    # Secrets
    B_EMAIL = os.getenv("BLOGGER_EMAIL")
    S_EMAIL = os.getenv("SENDER_EMAIL")
    PASS = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    S_KEY = os.getenv("SHRINKME_API")
    G_KEY = os.getenv("GEMINI_API")

    # 20+ प्रीमियम ताज़ा सोर्स (Variety of Categories)
    sources = {
        "YouTube India Trending": "https://news.google.com/rss/search?q=trending+on+youtube+india&hl=en-IN&gl=IN&ceid=IN:en",
        "Hollywood Leaks": "https://variety.com/feed/",
        "Bollywood Buzz": "https://www.pinkvilla.com/feed",
        "PS5/Xbox Gaming": "https://www.ign.com/rss/articles/feed",
        "Smartphone Tech": "https://techcrunch.com/feed/",
        "AI & Future": "https://www.theverge.com/rss/index.xml",
        "Netflix Originals": "https://www.collider.com/feed/",
        "Marvel/Disney+": "https://screenrant.com/feed/",
        "Space Exploration": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "Cricket Updates": "https://www.espn.com/espn/rss/news",
        "Auto/EV News": "https://www.autocarindia.com/rss/news",
        "Web Series Leaks": "https://news.google.com/rss/search?q=web+series+leaks+india&hl=en-IN&gl=IN&ceid=IN:en"
    }

    category, rss_url = random.choice(list(sources.items()))
    print(f"📡 Fetching from: {category}")
    
    feed = feedparser.parse(rss_url)
    if not feed.entries: return

    # रैंडम टॉप 10 में से एक उठाना (Uniqueness)
    item = random.choice(feed.entries[:min(len(feed.entries), 10)])
    title = item.title
    orig_link = item.link

    # AI Article Generation
    print(f"🤖 AI is writing deep article for: {title}")
    article_body = get_pro_human_article(title, category, G_KEY)

    # Image & Money Link
    rand_id = random.randint(1000, 9999)
    # रैंडम फोटो ताकि ब्लॉगर इमेज को पहचाने
    img_tags = ["cinema", "neon", "robot", "news", "viral", "tech"]
    image_url = f"https://loremflickr.com/800/450/{random.choice(img_tags)}/all?lock={rand_id}"
    
    try:
        r = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={orig_link}").json()
        money_link = r.get("shortenedUrl", orig_link)
    except:
        money_link = orig_link

    # --- हाई-क्वालिटी 'AGENTIC' डिज़ाइन ---
    html_content = f"""
    <div style="font-family:'Segoe UI', Arial; max-width:800px; margin:auto; background:#fff; color:#111; border-radius:15px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.1); border:1px solid #eee;">
        <img src="{image_url}" style="width:100%; height:auto; border-bottom:5px solid #ff6600;" alt="Featured">
        <div style="padding:45px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:25px;">
                <span style="background:#ff6600; color:#000; padding:6px 15px; border-radius:4px; font-weight:bold; font-size:12px;">LIVE: {category.upper()}</span>
                <span style="color:#999; font-size:12px;">{datetime.now().strftime('%d %B, %H:%M')}</span>
            </div>
            
            <h1 style="font-size:38px; line-height:1.2; font-weight:900; color:#000; margin-bottom:30px;">{title}</h1>
            
            <div style="font-size:18px; line-height:1.9; color:#444; text-align:justify;">
                {article_body}
            </div>

            <div style="margin-top:60px; text-align:center; background:#000; padding:50px; border-radius:20px;">
                <h2 style="color:#fff; font-size:26px; margin-bottom:25px;">Ready to Access the Full Media?</h2>
                <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:22px 60px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:24px; display:inline-block; box-shadow:0 10px 30px rgba(255,102,0,0.5);">🔓 UNLOCK CONTENT NOW</a>
                <p style="font-size:11px; color:#666; margin-top:20px;">Encrypted via Agentic AI Secure Protocol v12.0 | ID: {rand_id}</p>
            </div>
        </div>
    </div>
    """

    # ईमेल भेजना (Safety First)
    msg = EmailMessage()
    msg['Subject'] = f"Update #{rand_id}: {title[:50]}..."
    msg['From'] = S_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(html_content, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(S_EMAIL, PASS)
        server.send_message(msg)
    
    print(f"✅ MISSION SUCCESS! Published in {category}")

if __name__ == "__main__":
    run_viral_machine()
