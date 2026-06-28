import os, smtplib, requests, feedparser, random
from email.message import EmailMessage
from datetime import datetime

def get_deep_ai_article(headline, category, g_key):
    """AI को एक प्रोफेशनल लेखक की तरह 500 शब्दों का आर्टिकल लिखने का निर्देश"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    
    prompt = f"""Act as an expert journalist specializing in {category}.
    Write a DEEP, ENGAGING, and HUMAN-LIKE 500-word blog post about: "{headline}".
    
    Structure the article with these HTML tags:
    - <h2> Catchy, clickbait sub-headline.
    - <p> Detailed introduction (what happened and why it's viral).
    - <h3> Deep Dive & Exclusive Details (Internal facts and rumors).
    - <ul> List of key takeaways or facts.
    - <blockquote> A fake 'social media reaction' quote.
    - <p> Professional analysis and future predictions.
    
    Important: Use emojis, bold text (<b>), and professional vocabulary. 
    Make it look like a high-end news portal article. Avoid 'AI-sounding' words."""

    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=25).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h2>Analysis of {headline}</h2><p>Our team is currently investigating the latest developments in {category}. Full report coming soon.</p>"

def run_mega_bot():
    # 1. सभी चाबियाँ लोड करना
    B_EMAIL = os.getenv("BLOGGER_EMAIL")
    S_EMAIL = os.getenv("SENDER_EMAIL")
    PASS = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    S_KEY = os.getenv("SHRINKME_API")
    G_KEY = os.getenv("GEMINI_API")

    # 2. 20+ असली न्यूज़ सोर्सेस (Variety of Categories)
    news_sources = {
        "Gaming": "https://www.ign.com/rss/articles/feed",
        "Hollywood": "https://variety.com/feed/",
        "Bollywood": "https://www.pinkvilla.com/feed",
        "Tech News": "https://techcrunch.com/feed/",
        "Gadgets": "https://www.theverge.com/rss/index.xml",
        "Marvel/DC": "https://screenrant.com/feed/",
        "Netflix/Streaming": "https://www.collider.com/feed/",
        "Space/Science": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "Sports": "https://www.espn.com/espn/rss/news",
        "Mobile/iOS": "https://www.gsmarena.com/rss-news-reviews.php3",
        "Business": "https://www.forbes.com/real-time/feed/",
        "Crypto": "https://cointelegraph.com/rss"
    }

    # रैंडम कैटेगरी और न्यूज़ चुनना
    cat_name, rss_url = random.choice(list(news_sources.items()))
    print(f"📡 Category Selected: {cat_name}")
    
    feed = feedparser.parse(rss_url)
    if not feed.entries: return

    # टॉप 10 में से रैंडम न्यूज़ (ताकि कंटेंट रिपीट न हो)
    top_entries = feed.entries[:min(len(feed.entries), 10)]
    selected = random.choice(top_entries)
    title = selected.title
    source_link = selected.link

    # 3. AI से गहरा आर्टिकल लिखवाना
    article_body = get_deep_ai_article(title, cat_name, G_KEY)

    # 4. फोटो और ShrinkMe लिंक
    rand_id = random.randint(10000, 99999)
    image_url = f"https://loremflickr.com/800/450/{cat_name.lower().replace(' ', '')}/all?lock={rand_id}"
    
    try:
        api_url = f"https://shrinkme.io/api?api={S_KEY}&url={source_link}"
        money_link = requests.get(api_url).json().get("shortenedUrl", source_link)
    except:
        money_link = source_link

    # 5. प्रीमियम "Agentic AI" डिजाइन (इंसानी अहसास के साथ)
    html_content = f"""
    <div style="font-family:'Helvetica Neue', Arial; max-width:800px; margin:auto; background:#fff; color:#111; border:1px solid #eee; border-radius:12px; overflow:hidden; box-shadow:0 15px 50px rgba(0,0,0,0.1);">
        <img src="{image_url}" style="width:100%; height:auto; border-bottom:4px solid #ff6600;" alt="Breaking">
        <div style="padding:40px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
                <span style="background:#000; color:#ff6600; padding:5px 15px; border-radius:4px; font-weight:bold; font-size:12px;">{cat_name.upper()} EXCLUSIVE</span>
                <span style="color:#888; font-size:12px;">{datetime.now().strftime('%d %B, %Y')}</span>
            </div>
            <h1 style="font-size:36px; line-height:1.2; margin-bottom:30px; color:#000; font-weight:900;">{title}</h1>
            <div style="font-size:17px; line-height:1.8; color:#333; text-align:justify;">
                {article_body}
            </div>
            <div style="margin-top:50px; text-align:center; background:#f9f9f9; padding:40px; border-radius:20px; border:1px dashed #ff6600;">
                <h2 style="font-size:24px; margin-bottom:20px;">Unlock Full Report & Official Media</h2>
                <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:20px 60px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block; box-shadow:0 10px 25px rgba(255,102,0,0.3);">🔓 ACCESS CONTENT NOW</a>
                <p style="font-size:11px; color:#999; margin-top:20px;">Security Verified by Agentic AI Protocol v10.1 | Token: {rand_id}</p>
            </div>
        </div>
    </div>
    """

    # 6. ईमेल भेजना (Anti-Block Subject)
    msg = EmailMessage()
    msg['Subject'] = f"Update: {title[:60]}... (#{rand_id})"
    msg['From'] = S_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(html_content, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(S_EMAIL, PASS)
        server.send_message(msg)
    print(f"✅ Post Published! Category: {cat_name} | ID: {rand_id}")

if __name__ == "__main__":
    run_mega_bot()
