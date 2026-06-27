import os
import smtplib
import requests
from email.message import EmailMessage
import google.generativeai as genai

# GitHub Secrets से डेटा उठाना
BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
GEMINI_KEY = os.getenv("GEMINI_API")
SHRINKME_API = os.getenv("SHRINKME_API")

def get_ai_content():
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-pro')
    prompt = "Find a trending Hollywood movie. Write a catchy title and a 3-line viral summary with emojis."
    return model.generate_content(prompt).text

try:
    print("🤖 Generating AI Content...")
    content = get_ai_content()
    
    # ShrinkMe Link Generation
    long_url = "https://viralnewsai24.blogspot.com"
    res = requests.get(f"https://shrinkme.io/api?api={SHRINKME_API}&url={long_url}").json()
    money_link = res.get("shortenedUrl", long_url)

    # Creating Email Post
    msg = EmailMessage()
    msg['Subject'] = "Latest AI Viral Update " + content[:20]
    msg['From'] = SENDER_EMAIL
    msg['To'] = BLOGGER_EMAIL
    
    # HTML Content for Blogger
    html_body = f"""
    <div style="background:#000; color:#00f2ff; padding:20px; border:2px solid #00f2ff; border-radius:10px; font-family:sans-serif; text-align:center;">
        <h2 style="color:#7000ff;">AGENTIC AI UPDATE</h2>
        <p style="color:#ccc;">{content}</p>
        <br>
        <a href="{money_link}" style="background:#00f2ff; color:#000; padding:15px 30px; text-decoration:none; border-radius:50px; font-weight:bold; display:inline-block;">INITIALIZE DOWNLOAD</a>
    </div>
    """
    msg.set_content("New Update Found by AI Bot") # Plain text backup
    msg.add_alternative(html_body, subtype='html')

    # Sending via SSL (More Reliable)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, GMAIL_PASSWORD)
        smtp.send_message(msg)
    
    print("✅ Success! Email sent to Blogger.")
except Exception as e:
    print(f"❌ Error: {e}")
