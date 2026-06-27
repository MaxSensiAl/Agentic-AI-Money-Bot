import os, smtplib, requests
from email.message import EmailMessage

# --- CONFIG ---
B_EMAIL = os.getenv("BLOGGER_EMAIL")
S_EMAIL = os.getenv("SENDER_EMAIL")
PASS = os.getenv("GMAIL_APP_PASSWORD").replace(" ", "") 
G_KEY = os.getenv("GEMINI_API")
S_KEY = os.getenv("SHRINKME_API")

def get_ai_pro_content():
    try:
        # AI को निर्देश: टाइटल, फोटो लिंक और खबर तीनों चाहिए
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
        prompt = "Find a trending movie or gadget news. Provide: 1) Catchy Title 2) Image URL related to it 3) 3-line description with emojis. Format: Title | ImageURL | Description"
        payload = {"contents": [{"parts":[{"text": prompt}]}]}
        res = requests.post(url, json=payload).json()
        raw_text = res['candidates'][0]['content']['parts'][0]['text']
        # डेटा को अलग-अलग करना
        parts = raw_text.split("|")
        return parts[0].strip(), parts[1].strip(), parts[2].strip()
    except:
        return "New Viral Update", "https://via.placeholder.com/800x450.png?text=Agentic+AI+News", "Exciting update found in tech and movies! Click below to see more."

try:
    print("🤖 Creating Professional Blog Post...")
    title, image_url, description = get_ai_pro_content()
    
    # ShrinkMe Link
    link_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url=https://viralnewsai24.blogspot.com").json()
    money_link = link_res.get("shortenedUrl", "https://viralnewsai24.blogspot.com")

    # --- प्रोफेशनल ब्लॉग टेम्पलेट (Professional Look) ---
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 10px; overflow: hidden; background: #fff;">
        <img src="{image_url}" style="width: 100%; height: auto; display: block;" alt="Featured Image">
        <div style="padding: 20px; text-align: center;">
            <h1 style="color: #333; font-size: 24px;">{title}</h1>
            <p style="color: #666; font-size: 16px; line-height: 1.6;">{description}</p>
            <div style="margin-top: 25px;">
                <a href="{money_link}" style="background: #e50914; color: #fff; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 18px; display: inline-block;">🚀 DOWNLOAD / VIEW FULL POST</a>
            </div>
            <p style="font-size: 12px; color: #999; margin-top: 20px;">Posted by Viral News AI Engine</p>
        </div>
    </div>
    """

    msg = EmailMessage()
    msg['Subject'] = title
    msg['From'] = SENDER_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(html_body, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(S_EMAIL, PASS)
        server.send_message(msg)
    
    print(f"✅ SUCCESS! Professional post sent: {title}")

except Exception as e:
    print(f"❌ ERROR: {e}")
