import os, smtplib, requests
from email.message import EmailMessage

# Secrets
B_EMAIL = os.getenv("BLOGGER_EMAIL")
S_EMAIL = os.getenv("SENDER_EMAIL")
PASS = os.getenv("GMAIL_APP_PASSWORD").replace(" ", "")
G_KEY = os.getenv("GEMINI_API")
S_KEY = os.getenv("SHRINKME_API")

def get_viral_data():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
    # AI को साफ़ निर्देश कि हमें फोटो और खबर दोनों चाहिए
    prompt = "Find a trending Hollywood/Bollywood movie news. Provide in 3 lines: Title, News Summary, and a high-quality Poster URL. Keep it very exciting."
    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload).json()
        text = res['candidates'][0]['content']['parts'][0]['text']
        return text
    except:
        return "New Viral Update Found! | Check the latest details about today's trending news. | https://via.placeholder.com/800x450.png?text=Agentic+AI+News"

try:
    print("🚀 Fetching Trending News...")
    ai_content = get_viral_data()
    
    # ShrinkMe Link
    money_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url=https://viralnewsai24.blogspot.com").json()
    link = money_res.get("shortenedUrl", "https://viralnewsai24.blogspot.com")

    # --- प्रोफेशनल कार्ड डिज़ाइन (Attraction) ---
    html_post = f"""
    <div style="font-family:Arial; background:#111; color:#fff; border-radius:15px; overflow:hidden; border:2px solid #ff6600;">
        <div style="background:#ff6600; padding:10px; text-align:center; color:#000; font-weight:bold;">🔥 TRENDING ALERT</div>
        <div style="padding:20px;">
            <h2 style="color:#ff6600; margin-bottom:10px;">New AI Update</h2>
            <p style="color:#ccc; font-size:16px; line-height:1.6;">{ai_content}</p>
            <div style="margin-top:30px; text-align:center; background:#222; padding:20px; border-radius:10px;">
                <h3 style="color:#fff;">Unlock Full Data</h3>
                <a href="{link}" style="background:#ff6600; color:#000; padding:15px 30px; text-decoration:none; border-radius:5px; font-weight:bold; display:inline-block;">🚀 INITIALIZE DOWNLOAD</a>
            </div>
        </div>
    </div>
    """

    msg = EmailMessage()
    msg['Subject'] = "🔥 Viral AI Update Found!"
    msg['From'] = SENDER_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(html_post, subtype='html')

    # Send
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(S_EMAIL, PASS)
        server.send_message(msg)
    print("✅ SUCCESS! Check Blogger in 5 minutes.")

except Exception as e:
    print(f"❌ ERROR: {e}")
