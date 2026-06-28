import os, smtplib, requests, feedparser, random
from email.message import EmailMessage
from datetime import datetime

def get_deep_ai_article(headline, g_key):
    """AI को एक असली लेखक की तरह सोचने पर मजबूर करना"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={g_key}"
    
    # अलग-अलग राइटिंग स्टाइल ताकि ब्लॉग 'इंसानी' लगे
    styles = ["Investigative Journalist", "Tech Enthusiast", "Bollywood Insider", "Film Critic"]
    chosen_style = random.choice(styles)
    
    prompt = f"""Act as a {chosen_style}. 
    Write a DEEP, ENGAGING, and UNIQUE 500-word blog post about the news: "{headline}". 
    Structure the response with HTML tags:
    - <h3> A catchy unique sub-headline.
    - <p> Detailed background story (why this is viral).
    - <b> Key Facts & Leaks section.
    - <p> Public & Social Media Reaction using emojis.
    - <h3> Final verdict or what to expect next.
    Note: Do not use typical AI phrases like 'In conclusion'. Make it sound like a real human wrote it. 
    Use professional vocabulary and keep it exciting!"""
    
    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=20).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h3>Update on {headline}</h3><p>Detailed analysis of this viral trend is being prepared by our team. Stay tuned for exclusive data.</p>"

def run_viral_engine():
    # 1. सभी चाबियाँ (Secrets) लोड करना
    B_EMAIL = os.getenv("BLOGGER_EMAIL")
    S_EMAIL = os.getenv("SENDER_EMAIL") 
    PASS = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    S_KEY = os.getenv("SHRINKME_API")
    G_KEY = os.getenv("GEMINI_API")

    if not S_EMAIL or not PASS:
        print("❌ Error: Missing Secrets!")
        return

    # 2. मल्टी-प्लेटफॉर्म न्यूज़ सोर्सेस (YouTube, Tech, Movie)
    sources = [
        "https://www.youtube.com/feeds/videos.xml?channel_id=UC3Izv8457G-N5_Tyz7T2v7w", # YouTube Trending (T-Series)
        "https://variety.com/feed/", # Hollywood
        "https://www.pinkvilla.com/feed", # Bollywood
        "https://techcrunch.com/feed/", # Tech
        "https://www.theverge.com/rss/index.xml" # Gadgets
    ]
    
    source_url = random.choice(sources)
    news_feed = feedparser.parse(source_url)
    
    if not news_feed.entries:
        print("❌ No fresh data found.")
        return
    
    # टॉप 10 में से रैंडम खबर ताकि रिपिटेशन न हो
    selected_news = random.choice(news_feed.entries[:min(len(news_feed.entries), 10)])
    title = selected_news.title
    original_link = selected_news.link
    print(f"📡 Bot selected today's topic: {title}")

    # 3. AI से गहरा आर्टिकल लिखवाना
    detailed_article = get_deep_ai_article(title, G_KEY)

    # 4. फोटो और लिंक का जुगाड़
    rand_id = random.randint(1000, 9999)
    # रैंडम कैटेगरी फोटो ताकि हर बार विज़ुअल अलग हो
    img_keywords = ["cinema", "neon", "robot", "galaxy", "digital"]
    image_url = f"https://loremflickr.com/800/450/{random.choice(img_keywords)}/all?lock={rand_id}"
    
    try:
        api_url = f"https://shrinkme.io/api?api={S_KEY}&url={original_link}"
        money_link = requests.get(api_url).json().get("shortenedUrl", original_link)
    except:
        money_link = original_link

    # 5. प्रीमियम "Agentic AI" डिज़ाइन (Black & Orange)
    html_body = f"""
    <div style="font-family:'Segoe UI', sans-serif; max-width:750px; margin:auto; background:#ffffff; color:#111; border:1px solid #eee; border-radius:15px; overflow:hidden; box-shadow:0 15px 40px rgba(0,0,0,0.1);">
        <img src="{image_url}" style="width:100%; height:auto; border-bottom:4px solid #ff6600;">
        <div style="padding:35px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
                <span style="background:#ff6600; color:#000; padding:5px 15px; border-radius:5px; font-weight:bold; font-size:12px;">★ AGENTIC AI EXCLUSIVE ★</span>
                <span style="color:#aaa; font-size:12px;">{datetime.now().strftime('%d %b, %H:%M')}</span>
            </div>
            <h1 style="font-size:32px; color:#000; margin-bottom:25px; line-height:1.2; font-weight:800;">{title}</h1>
            <div style="font-size:16px; color:#333; line-height:1.9; text-align:justify;">
                {detailed_article}
            </div>
            <div style="margin-top:45px; text-align:center; background:#0d0d0d; padding:40px; border-radius:15px;">
                <h2 style="color:#fff; font-size:24px; margin-bottom:25px;">Want to see the Official Source?</h2>
                <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:20px 50px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:22px; display:inline-block; box-shadow:0 10px 20px rgba(255,102,0,0.3);">🔓 UNLOCK CONTENT NOW</a>
                <p style="font-size:11px; color:#555; margin-top:20px;">Verified Real Data Transfer // Security Token: {rand_id}</p>
            </div>
        </div>
    </div>
    """

    # 6. ईमेल भेजना (Fixed Anti-Spam Security)
    msg = EmailMessage()
    msg['Subject'] = f"💎 Exclusive Update: {title[:50]}... ({rand_id})"
    msg['From'] = S_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(html_body, subtype='html')

    print(f"📧 Sending from {S_EMAIL}...")
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(S_EMAIL, PASS)
        server.send_message(msg)
    print(f"✅ SUCCESS! Professional Post #{rand_id} Published.")

if __name__ == "__main__":
    run_viral_engine()
