import os, smtplib, requests, feedparser, random, json
from email.message import EmailMessage
from datetime import datetime

# --- SETTINGS ---
SHRINKME_API = os.getenv("SHRINKME_API")
GEMINI_API = os.getenv("GEMINI_API")
BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")

def get_human_article(headline, category, g_key):
    """AI को मजबूर करना कि वह एक असली इंसान की तरह 500-600 शब्दों का गहरा लेख लिखे"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    
    # अलग-अलग राइटिंग स्टाइल ताकि गूगल को 'रोबोट' न लगे
    styles = ["Investigative Reporter", "Industry Insider", "Storyteller", "Expert Critic"]
    chosen_style = random.choice(styles)
    
    prompt = f"""Act as a professional {chosen_style}. 
    Write a 600-word DEEP and HIGHLY UNIQUE blog post about: "{headline}" in category {category}.
    
    RULES:
    1. Structure with SEO-friendly HTML: use <h2>, <h3>, <b>, and <ul> tags.
    2. Add an 'Internal Fact Check' section.
    3. Include a 'Why this is Trending' analysis.
    4. Write a 'Public Social Media Reaction' section with emojis.
    5. Use professional, engaging vocabulary (Human-like touch).
    6. Ensure the tone is exciting but credible.
    7. Add a 'Metadata Keywords' section at the end for Google SEO.
    
    Return ONLY the HTML body content."""
    
    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=30).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h2>Exclusive Report: {headline}</h2><p>Our experts are analyzing the latest data on {category}. Stay tuned for the full breakdown.</p>"

def run_viral_machine():
    print(f"🚀 Machine Initialized: {datetime.now()}")

    # 1. 20+ प्रीमियम न्यूज़ और यूट्यूब सोर्सेस
    sources = {
        "YouTube Trending": "https://www.youtube.com/feeds/videos.xml?channel_id=UC3Izv8457G-N5_Tyz7T2v7w",
        "Hollywood Leaks": "https://variety.com/feed/",
        "Bollywood Buzz": "https://www.pinkvilla.com/feed",
        "Gaming News": "https://www.ign.com/rss/articles/feed",
        "Tech Trends": "https://techcrunch.com/feed/",
        "AI Revolution": "https://www.theverge.com/rss/index.xml",
        "Space Secrets": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "Global News": "https://www.aljazeera.com/xml/rss/all.xml",
        "Marvel/DC": "https://screenrant.com/feed/",
        "Netflix Updates": "https://www.collider.com/feed/",
        "Gadget Reviews": "https://www.gsmarena.com/rss-news-reviews.php3",
        "Business Insider": "https://www.forbes.com/real-time/feed/",
        "Cricket/Sports": "https://www.espn.com/espn/rss/news"
    }

    # रैंडम सोर्स चुनना (Variety के लिए)
    category, rss_url = random.choice(list(sources.items()))
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        print("❌ No news found at the moment.")
        return

    # टॉप 10 में से रैंडम खबर (Uniqueness के लिए)
    item = random.choice(feed.entries[:min(len(feed.entries), 10)])
    title = item.title
    orig_link = item.link

    # 2. AI से गहरा लेख लिखवाना
    detailed_article = get_human_article(title, category, GEMINI_API)

    # 3. Dynamic Photo & ShrinkMe Link
    rand_id = random.randint(10000, 99999)
    # रैंडम फोटो कीवर्ड्स
    img_tag = random.choice(["cinema", "robot", "tech", "trending", "superhero"])
    image_url = f"https://loremflickr.com/800/450/{img_tag}/all?lock={rand_id}"
    
    try:
        short_res = requests.get(f"https://shrinkme.io/api?api={SHRINKME_API}&url={orig_link}").json()
        money_link = short_res.get("shortenedUrl", orig_link)
    except:
        money_link = orig_link

    # 4. SEO-optimized High-Conversion Design
    html_content = f"""
    <div style="font-family:'Segoe UI', sans-serif; max-width:800px; margin:auto; background:#fff; color:#111; border:1px solid #eee; border-radius:15px; overflow:hidden; box-shadow:0 15px 50px rgba(0,0,0,0.15);">
        <!-- JSON-LD SEO Schema for Google -->
        <script type="application/ld+json">
        {{ "@context": "https://schema.org", "@type": "NewsArticle", "headline": "{title}", "image": ["{image_url}"], "datePublished": "{datetime.now().isoformat()}" }}
        </script>
        
        <img src="{image_url}" style="width:100%; height:auto; border-bottom:5px solid #ff6600;" alt="News Banner">
        
        <div style="padding:40px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
                <span style="background:#ff6600; color:#000; padding:5px 15px; border-radius:5px; font-weight:bold; font-size:12px;">★ {category.upper()} SPECIAL ★</span>
                <span style="color:#aaa; font-size:12px;">Verified Report: {rand_id}</span>
            </div>
            
            <h1 style="font-size:34px; line-height:1.2; color:#000; font-weight:900; margin-bottom:25px;">{title}</h1>
            
            <div style="font-size:17px; line-height:1.9; color:#333; text-align:justify; border-left:4px solid #eee; padding-left:20px;">
                {detailed_article}
            </div>

            <div style="margin-top:50px; text-align:center; background:#0a0a0a; padding:45px; border-radius:15px;">
                <h2 style="color:#fff; font-size:24px; margin-bottom:20px;">Unlock Official Source & Detailed Files</h2>
                <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:18px 50px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block; box-shadow:0 10px 25px rgba(255,102,0,0.4);">🔓 UNLOCK CONTENT NOW</a>
                <p style="font-size:11px; color:#555; margin-top:20px;">Safe Data Transfer Protocol Enabled | Encrypted by Agentic AI</p>
            </div>
        </div>
    </div>
    """

    # 5. ईमेल भेजना (Anti-Block Subject)
    msg = EmailMessage()
    msg['Subject'] = f"New Update: {title[:50]}... (#{rand_id})" # Unique subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = BLOGGER_EMAIL
    msg.add_alternative(html_content, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, GMAIL_PASS)
        server.send_message(msg)
    
    print(f"✅ SUCCESS! Professional post sent. Category: {category}")

if __name__ == "__main__":
    run_viral_machine()
