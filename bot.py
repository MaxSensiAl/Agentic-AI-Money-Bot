import os, smtplib, requests, feedparser, random
from email.message import EmailMessage

def get_unique_ai_article(headline, g_key):
    """AI से खबर लिखवाना"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    prompt = f"Act as an Investigative Journalist. Write a UNIQUE 400-word blog post about: '{headline}'. Add sections for Facts, Cast/Specs, and Public Opinion with emojis. Use HTML tags like <h3> and <b>."
    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=15).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h3>News Update</h3><p>Detailed analysis for {headline} is being processed.</p>"

def run_viral_engine():
    # 1. सभी चाबियाँ (Secrets) लोड करना - यहाँ नाम सही कर दिए गए हैं
    BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL") 
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    SHRINKME_API = os.getenv("SHRINKME_API")
    GEMINI_API = os.getenv("GEMINI_API")

    if not SENDER_EMAIL or not GMAIL_APP_PASSWORD:
        print("❌ Error: Email Secrets missing!")
        return

    # 2. असली न्यूज़ सोर्सेस
    sources = [
        "https://www.pinkvilla.com/feed",
        "https://techcrunch.com/feed/",
        "https://variety.com/feed/",
        "https://deadline.com/feed/"
    ]
    
    source_url = random.choice(sources)
    news_feed = feedparser.parse(source_url)
    
    if not news_feed.entries:
        print("❌ No news found.")
        return
    
    # टॉप 10 में से रैंडम खबर
    top_news = random.choice(news_feed.entries[:min(len(news_feed.entries), 10)])
    title = top_news.title
    original_link = top_news.link
    print(f"📡 Selected: {title}")

    # 3. AI से आर्टिकल लिखवाना
    detailed_content = get_unique_ai_article(title, GEMINI_API)

    # 4. फोटो और लिंक
    rand_id = random.randint(1, 9999)
    image_url = f"https://loremflickr.com/800/450/cinema,gadget,viral/all?lock={rand_id}"
    
    try:
        api_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={original_link}"
        money_link = requests.get(api_url).json().get("shortenedUrl", original_link)
    except:
        money_link = original_link

    # 5. प्रीमियम डिज़ाइन (Orange-Black Theme)
    html_body = f"""
    <div style="font-family:sans-serif; max-width:700px; margin:auto; background:#ffffff; border:1px solid #ddd; border-radius:12px; overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,0.1);">
        <img src="{image_url}" style="width:100%; height:auto; border-bottom:4px solid #ff6600;">
        <div style="padding:30px;">
            <span style="background:#ff6600; color:#000; padding:5px 10px; border-radius:4px; font-weight:bold; font-size:12px;">EXCLUSIVE UPDATE</span>
            <h1 style="color:#000; margin:20px 0;">{title}</h1>
            <div style="color:#333; line-height:1.8; font-size:16px;">{detailed_content}</div>
            <div style="margin-top:35px; text-align:center; background:#f4f4f4; padding:25px; border-radius:10px;">
                <h3 style="margin-bottom:20px; color:#000;">Ready to Watch or Read more?</h3>
                <a href="{money_link}" style="background:#000; color:#fff; padding:15px 40px; text-decoration:none; border-radius:5px; font-weight:bold; font-size:20px; display:inline-block; box-shadow:0 5px 15px rgba(0,0,0,0.2);">🚀 ACCESS NOW</a>
            </div>
        </div>
    </div>
    """

    # 6. ईमेल भेजना
    msg = EmailMessage()
    msg['Subject'] = f"💎 Exclusive: {title[:50]}..."
    msg['From'] = SENDER_EMAIL
    msg['To'] = BLOGGER_EMAIL
    msg.add_alternative(html_body, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
        server.send_message(msg)
    print(f"✅ SUCCESS! Post sent to Blogger.")

if __name__ == "__main__":
    run_viral_engine()
