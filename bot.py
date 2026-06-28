import os, smtplib, requests, feedparser, random
from email.message import EmailMessage

# --- CONFIG ---
B_EMAIL = os.getenv("BLOGGER_EMAIL")
S_EMAIL = os.getenv("SENDER_EMAIL")
PASS = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
S_KEY = os.getenv("SHRINKME_API")
G_KEY = os.getenv("GEMINI_API")

def get_unique_ai_article(headline):
    """AI को मजबूर करना कि वह खबर को बिल्कुल अलग और गहरी जानकारी के साथ लिखे"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
    
    prompt = f"""Act as an Investigative Journalist. 
    Write a DEEP and UNIQUE 400-word blog post about: "{headline}". 
    Instructions:
    1. Do not repeat old patterns. Find a fresh angle.
    2. Add 'Hidden Facts' or 'Latest Rumors' section.
    3. Include a 'Cast & Crew' or 'Technical Specs' deep-dive.
    4. Provide a 'Public Reaction' section using emojis.
    5. Use high-quality professional vocabulary.
    6. Ensure the content is different even if the topic is same as before.
    Format with HTML tags like <h3> and <b> for professional look."""
    
    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h3>Update on {headline}</h3><p>Detailed analysis is being processed. Stay tuned for the full investigation.</p>"

def run_viral_engine():
    # 1. सोर्सेस की बड़ी लिस्ट (RSS Feeds)
    sources = [
        "https://www.youtube.com/feeds/videos.xml?channel_id=UC3Izv8457G-N5_Tyz7T2v7w", # T-Series
        "https://variety.com/feed/", 
        "https://www.pinkvilla.com/feed",
        "https://techcrunch.com/feed/",
        "https://www.hollywoodreporter.com/feed/",
        "https://deadline.com/feed/",
        "https://www.gsmarena.com/rss-news-reviews.php3"
    ]
    
    # रैंडम सोर्स चुनना
    source_url = random.choice(sources)
    news_feed = feedparser.parse(source_url)
    
    if not news_feed.entries: return
    
    # 2. टॉप 10 में से रैंडम खबर चुनना (ताकि हर बार अलग हो)
    sample_size = min(len(news_feed.entries), 10)
    top_news = random.choice(news_feed.entries[:sample_size])
    title = top_news.title
    original_link = top_news.link

    print(f"📡 Selected News: {title}")

    # 3. AI से यूनिक आर्टिकल लिखवाना
    detailed_content = get_unique_ai_article(title)

    # 4. फोटो (Dynamic & Fresh)
    # रैंडम कीवर्ड और लॉक का इस्तेमाल ताकि फोटो रिपीट न हो
    rand_id = random.randint(1, 9999)
    image_url = f"https://loremflickr.com/800/450/cinema,tech,trending/all?lock={rand_id}"

    # 5. ShrinkMe लिंक
    try:
        api_url = f"https://shrinkme.io/api?api={S_KEY}&url={original_link}"
        money_link = requests.get(api_url).json().get("shortenedUrl", original_link)
    except:
        money_link = original_link

    # 6. प्रीमियम कार्ड डिज़ाइन
    html_body = f"""
    <div style="font-family: 'Helvetica', sans-serif; max-width: 750px; margin: auto; background: #ffffff; color: #111; border: 1px solid #ddd; border-radius: 12px; overflow: hidden; box-shadow: 0 15px 35px rgba(0,0,0,0.1);">
        <img src="{image_url}" style="width: 100%; height: auto; border-bottom: 5px solid #e50914;" alt="Breaking News">
        <div style="padding: 35px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <span style="background: #e50914; color: #fff; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold;">SPECIAL REPORT</span>
                <span style="color: #888; font-size: 12px;">Ref: #{rand_id}</span>
            </div>
            <h1 style="font-size: 32px; color: #000; margin-bottom: 25px; line-height: 1.2; font-weight: 800;">{title}</h1>
            <div style="font-size: 16px; color: #333; line-height: 1.8; text-align: justify;">
                {detailed_content}
            </div>
            <div style="margin-top: 45px; text-align: center; background: #f4f4f4; padding: 30px; border-radius: 15px;">
                <h2 style="font-size: 22px; color: #000; margin-bottom: 20px;">Want to see the Official Video/Source?</h2>
                <a href="{money_link}" style="background: #000; color: #fff; padding: 20px 50px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 22px; display: inline-block; box-shadow: 0 10px 20px rgba(0,0,0,0.2);">🔓 UNLOCK CONTENT NOW</a>
                <p style="font-size: 12px; color: #777; margin-top: 20px;">Safe & Secure Data Pipeline via Agentic AI Engine v9.0</p>
            </div>
        </div>
    </div>
    """

    # 7. ईमेल भेजना
    msg = EmailMessage()
    msg['Subject'] = f"💎 Exclusive Update: {title[:55]}..."
    msg['From'] = SENDER_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(html_body, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(S_EMAIL, PASS)
        server.send_message(msg)
    print(f"✅ SUCCESS! Unique Post Published: {title}")

if __name__ == "__main__":
    run_viral_engine()
