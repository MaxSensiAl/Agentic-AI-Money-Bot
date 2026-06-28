import os, smtplib, requests, feedparser, random, json
from email.message import EmailMessage
from datetime import datetime

# --- CONFIGURATION (GitHub Secrets से उठाएगा) ---
S_EMAIL = os.getenv("SENDER_EMAIL") # totallivexxx@gmail.com
B_EMAIL = os.getenv("BLOGGER_EMAIL") # totallivexxx.secret@blogger.com
PASS = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
S_KEY = os.getenv("SHRINKME_API")
G_KEY = os.getenv("GEMINI_API")

def get_deep_ai_article(headline, category):
    """AI को एक असली न्यूज़ एडिटर की तरह 600 शब्दों का आर्टिकल लिखने का आदेश"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
    
    # अलग-अलग राइटिंग स्टाइल ताकि गूगल को हर बार नया लगे
    styles = ["Investigative Journalist", "Tech Geek", "Cinema Critic", "News Anchor"]
    chosen_style = random.choice(styles)
    
    prompt = f"""Act as a professional {chosen_style}. 
    Write a DEEP, UNIQUE, and HUMAN-LIKE 600-word news article about: "{headline}" in category {category}.
    
    RULES:
    1. Structure with SEO tags: <h2> catchy headline, <h3> sub-points, <b> bold facts.
    2. Add an 'Internal Leaks & Facts' section with <ul> bullets.
    3. Include a 'Public Buzz' section with emojis showing social media reaction.
    4. Write professionally. No AI robotic phrases. 
    5. Add 5 trending SEO keywords at the bottom.
    6. Return ONLY the HTML body content."""

    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=40).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h2>Report: {headline}</h2><p>Latest trending data for {category} is being analyzed by our high-speed Agentic AI engine.</p>"

def run_viral_machine():
    print(f"🚀 Initializing Viral Machine... Time: {datetime.now()}")

    # 1. 20+ प्रीमियम ताज़ा न्यूज़ और यूट्यूब सोर्सेस
    sources = {
        "YouTube India Trending": "https://news.google.com/rss/search?q=trending+on+youtube+india&hl=en-IN&gl=IN&ceid=IN:en",
        "Hollywood Leaks": "https://variety.com/feed/",
        "Bollywood Buzz": "https://www.pinkvilla.com/feed",
        "Gaming & Esports": "https://www.ign.com/rss/articles/feed",
        "Tech Trends": "https://techcrunch.com/feed/",
        "Smartphone Leaks": "https://www.gsmarena.com/rss-news-reviews.php3",
        "Netflix/Web Series": "https://www.collider.com/feed/",
        "Marvel/DC Universe": "https://screenrant.com/feed/",
        "Space & Science": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "Cricket/Sports News": "https://www.espn.com/espn/rss/news",
        "Auto/EV Updates": "https://www.autocarindia.com/rss/news",
        "Global Breaking": "https://www.aljazeera.com/xml/rss/all.xml"
    }

    # रैंडम कैटेगरी और न्यूज़ चुनना
    cat_name, rss_url = random.choice(list(sources.items()))
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        print("❌ No news found.")
        return

    # टॉप 10 में से रैंडम खबर (Uniqueness के लिए)
    item = random.choice(feed.entries[:min(len(feed.entries), 10)])
    title = item.title
    orig_link = item.link

    # 2. AI से गहरा आर्टिकल लिखवाना
    article_body = get_deep_ai_article(title, cat_name)

    # 3. Dynamic Photo & ShrinkMe Link
    rand_id = random.randint(10000, 99999)
    img_tags = ["tech", "movie", "cyber", "action", "news"]
    image_url = f"https://loremflickr.com/800/450/{random.choice(img_tags)}/all?lock={rand_id}"
    
    try:
        r = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={orig_link}").json()
        money_link = r.get("shortenedUrl", orig_link)
    except:
        money_link = orig_link

    # 4. प्रीमियम SEO डिज़ाइन (Orange-Black Theme)
    html_content = f"""
    <div style="font-family:'Segoe UI', sans-serif; max-width:800px; margin:auto; background:#fff; color:#111; border:1px solid #eee; border-radius:15px; overflow:hidden; box-shadow:0 15px 50px rgba(0,0,0,0.15);">
        <!-- JSON-LD SEO Schema for Google Ranking -->
        <script type="application/ld+json">
        {{ "@context": "https://schema.org", "@type": "NewsArticle", "headline": "{title}", "image": ["{image_url}"], "datePublished": "{datetime.now().isoformat()}" }}
        </script>
        
        <img src="{image_url}" style="width:100%; height:auto; border-bottom:5px solid #ff6600;" alt="Breaking News">
        <div style="padding:40px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
                <span style="background:#ff6600; color:#000; padding:5px 15px; border-radius:5px; font-weight:bold; font-size:12px;">★ {cat_name.upper()} EXCLUSIVE ★</span>
                <span style="color:#888; font-size:12px;">Ref: AI-BOT-{rand_id}</span>
            </div>
            <h1 style="font-size:34px; line-height:1.2; color:#000; font-weight:900; margin-bottom:25px;">{title}</h1>
            <div style="font-size:17px; line-height:1.9; color:#333; text-align:justify;">
                {article_body}
            </div>
            <div style="margin-top:50px; text-align:center; background:#0d0d0d; padding:40px; border-radius:15px;">
                <h2 style="color:#fff; font-size:24px; margin-bottom:25px;">Unlock Official Source & Detailed Files</h2>
                <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:20px 50px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block; box-shadow:0 10px 20px rgba(255,102,0,0.4);">🔓 UNLOCK CONTENT NOW</a>
                <p style="font-size:11px; color:#666; margin-top:15px;">Safe Data Transfer Protocol Enabled | Encrypted by Agentic AI</p>
            </div>
        </div>
    </div>
    """

    # 5. ईमेल भेजना (Anti-Block Subject)
    msg = EmailMessage()
    # सब्जेक्ट को रैंडम और ह्यूमन जैसा रखना ताकि गूगल ब्लॉक न करे
    msg['Subject'] = f"Report #{rand_id}: {title[:40]}..."
    msg['From'] = S_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(html_content, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(S_EMAIL, PASS)
        server.send_message(msg)
    print(f"✅ SUCCESS! Post {rand_id} Published in {cat_name}.")

if __name__ == "__main__":
    run_viral_machine()
