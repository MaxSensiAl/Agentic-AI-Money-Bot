import os, smtplib, requests, feedparser
from email.message import EmailMessage

def run_viral_engine():
    # 1. सभी चाबियाँ (Secrets) यहाँ परिभाषित करें
    B_EMAIL = os.getenv("BLOGGER_EMAIL")
    S_EMAIL = os.getenv("SENDER_EMAIL")
    PASS = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    S_KEY = os.getenv("SHRINKME_API")

    # चेक करें कि क्या सब कुछ मिल गया है
    if not S_EMAIL or not PASS:
        print("❌ Error: Email Secrets are missing!")
        return

    # 2. ताज़ा खबर उठाना
    print("📡 Fetching real-time news...")
    news_feed = feedparser.parse("https://news.google.com/rss/search?q=bollywood+hollywood+tech&hl=en-IN&gl=IN&ceid=IN:en")
    top_news = news_feed.entries[0]
    title = top_news.title
    news_link = top_news.link

    # 3. फोटो (Dynamic Image)
    image_url = "https://loremflickr.com/800/450/movie,tech/all"

    # 4. ShrinkMe लिंक बनाना
    try:
        api_url = f"https://shrinkme.io/api?api={S_KEY}&url={news_link}"
        money_link = requests.get(api_url).json().get("shortenedUrl", news_link)
    except:
        money_link = news_link

    # 5. HTML डिज़ाइन
    html_body = f"""
    <div style="font-family:Arial; max-width:600px; margin:auto; background:#000; color:#fff; border-radius:15px; overflow:hidden; border:2px solid #ff6600;">
        <img src="{image_url}" style="width:100%; height:auto;">
        <div style="padding:20px;">
            <h1 style="color:#fff; font-size:22px;">{title}</h1>
            <p style="color:#ccc;">Breaking update found! Click below to access full data and exclusive content.</p>
            <div style="text-align:center; margin-top:20px;">
                <a href="{money_link}" style="background:#ff6600; color:#000; padding:12px 30px; text-decoration:none; border-radius:5px; font-weight:bold; display:inline-block;">🚀 ACCESS DATA NOW</a>
            </div>
        </div>
    </div>
    """

    # 6. ईमेल भेजना (SSL के ज़रिए)
    msg = EmailMessage()
    msg['Subject'] = "🔥 Breaking: " + title[:50]
    msg['From'] = S_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(html_body, subtype='html')

    print(f"📧 Sending from {S_EMAIL} to Blogger...")
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(S_EMAIL, PASS)
        server.send_message(msg)
    print("✅ SUCCESS! Post sent to Blogger.")

if __name__ == "__main__":
    run_viral_engine()
