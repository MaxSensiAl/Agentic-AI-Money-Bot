import os, smtplib, requests, feedparser, random
from email.message import EmailMessage

def run_viral_engine():
    # Secrets
    B_EMAIL = os.getenv("BLOGGER_EMAIL")
    S_EMAIL = os.getenv("SENDER_EMAIL")
    PASS = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    S_KEY = os.getenv("SHRINKME_API")

    # 1. अलग-अलग टॉपिक्स की लिस्ट (ताकि हर बार कुछ नया मिले)
    topics = ["bollywood+news", "hollywood+movies+leak", "new+tech+gadgets", "netflix+trending", "marvel+updates"]
    query = random.choice(topics)
    
    # 2. खबर उठाना
    print(f"📡 Fetching news for: {query}")
    news_feed = feedparser.parse(f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en")
    
    # टॉप 10 खबरों में से कोई एक रैंडम चुनना
    if len(news_feed.entries) > 0:
        entries = news_feed.entries[:10]
        selected_news = random.choice(entries)
        title = selected_news.title
        news_link = selected_news.link
    else:
        return

    # 3. फोटो (Dynamic Image based on topic)
    image_url = f"https://loremflickr.com/800/450/{query.split('+')[0]},movie/all"

    # 4. ShrinkMe लिंक
    try:
        api_url = f"https://shrinkme.io/api?api={S_KEY}&url={news_link}"
        money_link = requests.get(api_url).json().get("shortenedUrl", news_link)
    except:
        money_link = news_link

    # 5. HTML डिज़ाइन (Orange-Black AI Style)
    html_body = f"""
    <div style="font-family:Arial; max-width:600px; margin:auto; background:#000; color:#fff; border-radius:15px; overflow:hidden; border:2px solid #ff6600;">
        <img src="{image_url}" style="width:100%; height:auto; border-bottom:3px solid #ff6600;">
        <div style="padding:20px;">
            <span style="background:#ff6600; color:#000; padding:5px 10px; border-radius:5px; font-weight:bold; font-size:12px;">AGENTIC AI EXCLUSIVE</span>
            <h1 style="color:#fff; font-size:22px; margin:15px 0;">{title}</h1>
            <p style="color:#ccc; line-height:1.6;">Breaking news alert! We have detected a major update in the world of {query.replace('+', ' ')}. Get all the leaked details and official data below.</p>
            <div style="text-align:center; margin-top:20px;">
                <a href="{money_link}" style="background:#ff6600; color:#000; padding:12px 30px; text-decoration:none; border-radius:5px; font-weight:bold; display:inline-block;">🚀 ACCESS DATA NOW</a>
            </div>
        </div>
    </div>
    """

    # 6. ईमेल भेजना
    msg = EmailMessage()
    msg['Subject'] = "🔥 Breaking: " + title[:60]
    msg['From'] = S_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(html_body, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(S_EMAIL, PASS)
        server.send_message(msg)
    print("✅ SUCCESS! Fresh post sent.")

if __name__ == "__main__":
    run_viral_engine()
