import os, smtplib, requests, feedparser
from email.message import EmailMessage

def run_viral_engine():
    # Secrets
    B_EMAIL = os.getenv("BLOGGER_EMAIL")
    S_EMAIL = os.getenv("SENDER_EMAIL")
    PASS = os.getenv("GMAIL_APP_PASSWORD").replace(" ", "")
    S_KEY = os.getenv("SHRINKME_API")

    # 1. असली खबर उठाना (Google News RSS)
    news_feed = feedparser.parse("https://news.google.com/rss/search?q=bollywood+hollywood+tech&hl=en-IN&gl=IN&ceid=IN:en")
    top_news = news_feed.entries[0]
    title = top_news.title
    news_link = top_news.link

    # 2. फोटो का जुगाड़ (No API Needed)
    # यह लिंक हर बार एक नई 'Movie' या 'Cinema' की शानदार फोटो उठाएगा
    image_url = "https://loremflickr.com/800/450/movie,cinema,tech/all"

    # 3. ShrinkMe लिंक बनाना
    try:
        link_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={news_link}").json()
        money_link = link_res.get("shortenedUrl", news_link)
    except:
        money_link = news_link

    # 4. शानदार "Pro-Look" डिज़ाइन (फोटो के साथ)
    html_body = f"""
    <div style="font-family:Arial; max-width:600px; margin:auto; background:#000; color:#fff; border-radius:15px; overflow:hidden; border:2px solid #ff6600;">
        <img src="{image_url}" style="width:100%; height:auto; border-bottom:3px solid #ff6600;" alt="Breaking News">
        <div style="padding:20px;">
            <span style="background:#ff6600; color:#000; padding:5px 10px; border-radius:5px; font-weight:bold; font-size:12px;">LIVE UPDATE</span>
            <h1 style="color:#fff; font-size:24px; margin:15px 0;">{title}</h1>
            <p style="color:#ccc; line-height:1.6; font-size:16px;">
                Breaking news just reported! We have gathered all the exclusive details, leaked clips, and the full story for you. 
                Click the button below to access the high-speed data transfer.
            </p>
            <div style="text-align:center; margin-top:30px; padding:20px; background:#111; border-radius:10px;">
                <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:15px 40px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:20px; display:inline-block;">🚀 INITIALIZE DOWNLOAD</a>
                <p style="font-size:10px; color:#555; margin-top:15px;">Encrypted via Agentic AI Engine v7.0</p>
            </div>
        </div>
    </div>
    """

    # 5. ईमेल भेजना
    msg = EmailMessage()
    msg['Subject'] = "🔥 Breaking: " + title[:50]
    msg['From'] = SENDER_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(html_body, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(S_EMAIL, PASS)
        server.send_message(msg)
    print(f"✅ SUCCESS! Posted with Photo: {title}")

if __name__ == "__main__":
    run_viral_engine()
