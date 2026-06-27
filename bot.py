import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai

# Secrets से डेटा उठाना
BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
GEMINI_KEY = os.getenv("GEMINI_API")
SHRINKME_API = os.getenv("SHRINKME_API")

def get_ai_content():
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-pro')
    prompt = "Find a trending Hollywood movie. Write a catchy title and a 3-line viral description with emojis."
    return model.generate_content(prompt).text

def send_email_post(subject, html_body):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = BLOGGER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(html_body, 'html'))
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER_EMAIL, GMAIL_PASSWORD)
    server.sendmail(SENDER_EMAIL, BLOGGER_EMAIL, msg.as_string())
    server.quit()

try:
    print("🤖 Bot is generating viral content...")
    ai_text = get_ai_content()
    
    # ShrinkMe Link Generation
    long_url = "https://viralnewsai24.blogspot.com"
    res = requests.get(f"https://shrinkme.io/api?api={SHRINKME_API}&url={long_url}").json()
    money_link = res.get("shortenedUrl", long_url)

    # HTML Design
    final_body = f"""
    <div style="background:#000; color:#00f2ff; padding:20px; border:2px solid #00f2ff; border-radius:10px; font-family:sans-serif; text-align:center;">
        <h2 style="color:#7000ff;">AGENTIC AI UPDATE</h2>
        <p style="color:#ccc;">{ai_text}</p>
        <br>
        <a href="{money_link}" style="background:#00f2ff; color:#000; padding:15px 30px; text-decoration:none; border-radius:50px; font-weight:bold; display:inline-block;">INITIALIZE DOWNLOAD</a>
    </div>
    """
    
    send_email_post("AI Viral Update Found", final_body)
    print("✅ Success! Post Sent to Blogger via Email.")
except Exception as e:
    print(f"❌ Error: {e}")
