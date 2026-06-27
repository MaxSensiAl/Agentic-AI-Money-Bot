import os, smtplib, requests
from email.message import EmailMessage
import google.generativeai as genai

try:
    # Secrets
    B_EMAIL = os.getenv("BLOGGER_EMAIL")
    S_EMAIL = os.getenv("SENDER_EMAIL")
    PASS = os.getenv("GMAIL_APP_PASSWORD").replace(" ", "")
    G_KEY = os.getenv("GEMINI_API")
    S_KEY = os.getenv("SHRINKME_API")

    # 1. AI Content (Model changed to gemini-1.5-flash)
    genai.configure(api_key=G_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    content = model.generate_content("Give me a trending Hollywood movie news headline and 3 lines about it with emojis.").text

    # 2. Money Link
    r = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url=https://viralnewsai24.blogspot.com").json()
    link = r.get("shortenedUrl", "https://viralnewsai24.blogspot.com")

    # 3. Send Email
    msg = EmailMessage()
    msg['Subject'] = "Breaking AI Viral News"
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
    print("✅ SUCCESS! Post sent to Blogger.")

except Exception as e:
    print(f"❌ ERROR: {e}")
    raise e
