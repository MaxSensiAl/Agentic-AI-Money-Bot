import os, smtplib, requests, feedparser, random, time
from email.message import EmailMessage
from datetime import datetime

# --- CONFIGURATION (GitHub Secrets) ---
S_EMAIL = os.getenv("SENDER_EMAIL")
B_EMAIL = os.getenv("BLOGGER_EMAIL")
PASS = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
S_KEY = os.getenv("SHRINKME_API")
G_KEY = os.getenv("GEMINI_API")

def get_human_touch_article(headline, category, persona):
    """AI को अलग-अलग किरदारों में बदल कर गहरा लेख लिखवाना"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
    
    prompt = f"""Act as a {persona}. 
    Write a DEEP, 100% UNIQUE news story (600-800 words) about: "{headline}" in the {category} niche.
    
    HUMAN-LIKE RULES:
    - Use natural transitions (e.g., 'Moving on...', 'Interestingly enough...').
    - Start with a catchy H2 sub-headline that isn't the same as the main title.
    - Break content into 5-6 detailed paragraphs.
    - Add a 'Pro Tip' or 'Fun Fact' box using a <blockquote> tag.
    - Use HTML tags: <h2>, <h3>, <b>, <ul>, <li>.
    - Include a 'User Opinion' section with mixed emojis (🤩, 🤔, 🔥).
    - NEVER use phrases like 'as an AI' or 'in conclusion'. 
    - Write like a real person sharing exclusive news with friends.
    - Return ONLY the HTML body code."""

    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=40).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h2>News Alert: {headline}</h2><p>Exclusive data regarding {category} is currently being verified by our inside sources. Full breakdown coming in the next hour.</p>"

def run_agentic_mega_bot():
    print(f"🌟 Agentic AI Engine v18.0 Waking Up...")
    
    # 1. रैंडम देरी (Human Behavior)
    time.sleep(random.randint(1, 60)) 

    # 2. 20+ प्रीमियम ताज़ा न्यूज़ और यूट्यूब सोर्सेस
    sources = {
        "YouTube India Trending": "https://news.google.com/rss/search?q=trending+india+youtube&hl=en-IN&gl=IN&ceid=IN:en",
        "Hollywood Insiders": "https://variety.com/feed/",
        "Bollywood Buzz": "https://www.pinkvilla.com/feed",
        "Gaming & Esports": "https://www.ign.com/rss/articles/feed",
        "AI & Tech Trends": "https://techcrunch.com/feed/",
        "Gadget Leaks": "https://www.theverge.com/rss/index.xml",
        "Marvel/DC Leaks": "https://screenrant.com/feed/",
        "Space & Universe": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "Cricket & Sports": "https://www.espn.com/espn/rss/news",
        "Web Series Updates": "https://www.collider.com/feed/",
        "Business Global": "https://www.forbes.com/real-time/feed/"
    }

    category, rss_url = random.choice(list(sources.items()))
    feed = feedparser.parse(rss_url)
    if not feed.entries: return
    
    item = random.choice(feed.entries[:8])
    title, orig_url = item.title, item.link

    # 3. AI Persona & Article Generation
    personas = ["Viral Content King", "Investigative Tech Journalist", "Deep-Rooted Bollywood Insider", "Hardcore Gamer", "NASA Data Analyst"]
    chosen_persona = random.choice(personas)
    print(f"🎭 Persona: {chosen_persona} | 📡 Category: {category}")
    
    article_body = get_human_touch_article(title, category, chosen_persona)

    # 4. Smart Image & ShrinkMe
    rand_id = random.randint(111111, 999999)
    # फोटो का कीवर्ड टाइटल के पहले दो शब्दों से उठाना
    img_kw = title.split()[:2]
    image_url = f"https://loremflickr.com/800/450/{','.join(img_kw)}/all?lock={rand_id}"
    
    try:
        r = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={orig_url}").json()
        money_link = r.get("shortenedUrl", orig_url)
    except:
        money_link = orig_url

    # 5. Premium Designer Template (Agentic Look)
    html_content = f"""
    <div style="font-family:'Segoe UI', Tahoma, sans-serif; max-width:800px; margin:auto; background:#fff; border:1px solid #eee; border-radius:20px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.1);">
        <img src="{image_url}" style="width:100%; height:auto; border-bottom:4px solid #ff6600;" alt="News Feed">
        <div style="padding:40px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:25px;">
                <span style="background:#ff6600; color:#000; padding:6px 12px; border-radius:5px; font-weight:bold; font-size:12px;">★ {category.upper()} EXCLUSIVE ★</span>
                <span style="color:#aaa; font-size:12px;">{datetime.now().strftime('%b %d, %H:%M')}</span>
            </div>
            <h1 style="font-size:36px; line-height:1.2; color:#000; font-weight:900; margin-bottom:25px;">{title}</h1>
            <div style="font-size:18px; line-height:1.9; color:#444; text-align:justify;">
                {article_body}
            </div>
            <div style="margin-top:50px; text-align:center; background:#000; padding:50px; border-radius:20px;">
                <h3 style="color:#fff; font-size:22px; margin-bottom:25px;">Ready to Access the Official Media Files?</h3>
                <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:20px 50px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:24px; display:inline-block; box-shadow:0 10px 30px rgba(255,102,0,0.4);">🔓 UNLOCK FULL CONTENT</a>
                <p style="font-size:10px; color:#666; margin-top:15px;">Encrypted Data Tunneling v18.0 | Human-Verified Transfer</p>
            </div>
        </div>
    </div>
    <p style="color:transparent; font-size:1px;">{rand_id} {random.choice(['news', 'leak', 'viral'])}</p>
    """

    # 6. ईमेल भेजना (Human-Style Subject)
    msg = EmailMessage()
    subject_templates = [
        f"Did you see this? {title[:40]}...",
        f"Exclusive: {title[:45]}",
        f"Just In: New Update on {title[:40]}",
        f"Urgent: {title[:45]} (Details Inside)",
        f"Breaking Update #{rand_id}"
    ]
    msg['Subject'] = random.choice(subject_templates)
    msg['From'] = S_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(html_content, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(S_EMAIL, PASS)
        server.send_message(msg)
    print(f"✅ MISSION SUCCESS! Article by '{chosen_persona}' Published.")

if __name__ == "__main__":
    run_agentic_mega_bot()
