import os, smtplib, requests
from email.message import EmailMessage

# Secrets
B_EMAIL = os.getenv("BLOGGER_EMAIL")
S_EMAIL = os.getenv("SENDER_EMAIL")
PASS = os.getenv("GMAIL_APP_PASSWORD").replace(" ", "")
G_KEY = os.getenv("GEMINI_API")
S_KEY = os.getenv("SHRINKME_API")

def get_real_trending_content():
    # AI को एक बहुत ही सख्त निर्देश देना (Prompt Engineering)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
    prompt = """Search the internet for the most trending movie or tech news in the last 12 hours. 
    Provide the response strictly in this format:
    TITLE: [Catchy Viral Title]
    IMAGE: [Direct public URL of a related image or poster]
    STORY: [3 paragraphs of exciting details with emojis]
    DETAILS: [Release Date | Rating | Genre]
    """
    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload).json()
        raw = res['candidates'][0]['content']['parts'][0]['text']
        return raw
    except:
        return "No News | https://via.placeholder.com/600x400 | Stay tuned for updates. | N/A"

try:
    print("🚀 AI Bot is searching social media trending news...")
    raw_data = get_real_trending_content()
    
    # डेटा को टुकड़ों में बाँटना
    lines = raw_data.split('\n')
    title = [l for l in lines if "TITLE:" in l][0].replace("TITLE:", "").strip()
    img = [l for l in lines if "IMAGE:" in l][0].replace("IMAGE:", "").strip()
    story = [l for l in lines if "STORY:" in l][0].replace("STORY:", "").strip()
    info = [l for l in lines if "DETAILS:" in l][0].replace("DETAILS:", "").strip()

    # ShrinkMe Link
    money_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url=https://viralnewsai24.blogspot.com").json()
    link = money_res.get("shortenedUrl", "https://viralnewsai24.blogspot.com")

    # --- ADVANCED HTML TEMPLATE (अट्रैक्टिव लुक) ---
    html_post = f"""
    <div style="font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width:100%; border:1px solid #333; background:#111; color:#fff; border-radius:15px; overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,0.5);">
        <img src="{img}" style="width:100%; height:auto; border-bottom:3px solid #ff6600;" alt="Poster">
        <div style="padding:20px;">
            <span style="background:#ff6600; color:#000; padding:5px 10px; border-radius:5px; font-weight:bold; font-size:12px;">TRENDING NOW</span>
            <h1 style="font-size:26px; margin:15px 0; color:#fff;">{title}</h1>
            <p style="color:#ff6600; font-weight:bold; font-size:14px;">📊 Info: {info}</p>
            <hr style="border:0.5px solid #333;">
            <p style="color:#ccc; line-height:1.8; font-size:16px;">{story}</p>
            <div style="text-align:center; margin-top:30px; padding:20px; background:#1a1a1a; border-radius:10px;">
                <h3 style="margin-bottom:20px;">Want to See More?</h3>
                <a href="{link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:15px 40px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:20px; display:inline-block; transition:0.3s;">🚀 ACCESS DATA NOW</a>
                <p style="font-size:10px; color:#555; margin-top:15px;">Secure Transfer via Agentic AI Engine v5.0</p>
            </div>
        </div>
    </div>
    """

    # Email Sending
    msg = EmailMessage()
    msg['Subject'] = "🔥 " + title
    msg['From'] = SENDER_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(html_post, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, PASS)
        server.send_message(msg)
    print("✅ SUCCESS! Viral post sent.")

except Exception as e:
    print(f"❌ ERROR: {e}")
