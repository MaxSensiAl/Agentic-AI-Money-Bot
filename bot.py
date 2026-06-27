import os
import smtplib
import requests
from email.message import EmailMessage

# Secrets
B_EMAIL = os.getenv("BLOGGER_EMAIL")
S_EMAIL = os.getenv("SENDER_EMAIL")
PASS = os.getenv("GMAIL_APP_PASSWORD").replace(" ", "")
G_KEY = os.getenv("GEMINI_API")
S_KEY = os.getenv("SHRINKME_API")

def get_ai_content():
    # सीधे API कॉल (बिना किसी SDK के) - यह 100% काम करेगा
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
    payload = {"contents": [{"parts":[{"text": "Give me a trending Hollywood movie name and 3 lines review with emojis."}]}]}
    res = requests.post(url, json=payload).json()
    return res['candidates'][0]['content']['parts'][0]['text']

try:
    print("🤖 AI is generating content...")
    content = get_ai_content()
    
    # ShrinkMe Link
    link_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url=https://viralnewsai24.blogspot.com").json()
    link = link_res.get("shortenedUrl", "https://viralnewsai24.blogspot.com")

    # Creating Email
    msg = EmailMessage()
    msg['Subject'] = "Breaking AI News Update"
    msg['From'] = S_EMAIL
    msg['To'] = B_EMAIL
    
    html_body = f"""
    <div style="background:#000; color:#00f2ff; padding:20px; border:2px solid #00f2ff; border-radius:10px; font-family:sans-serif; text-align:center;">
        <h2 style="color:#7000ff;">AGENTIC AI UPDATE</h2>
        <p style="color:#ccc;">{content}</p>
        <br>
        <a href="{link}" style="background:#00f2ff; color:#000; padding:15px 30px; text-decoration:none; border-radius:50px; font-weight:bold; display:inline-block;">INITIALIZE DOWNLOAD</a>
    </div>
    """
    msg.add_alternative(html_body, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(S_EMAIL, PASS)
        server.send_message(msg)
    
    print("✅ SUCCESS! Everything is working.")

except Exception as e:
    print(f"❌ FINAL ERROR: {e}")
