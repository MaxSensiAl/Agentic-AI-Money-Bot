import os, smtplib, requests
from email.message import EmailMessage

def run():
    # Secrets उठाना
    B_EMAIL = os.getenv("BLOGGER_EMAIL")
    S_EMAIL = os.getenv("SENDER_EMAIL")
    PASS = os.getenv("GMAIL_APP_PASSWORD").replace(" ", "")
    G_KEY = os.getenv("GEMINI_API")
    S_KEY = os.getenv("SHRINKME_API")

    print(f"📡 Sending from: {S_EMAIL} to {B_EMAIL}")

    # 1. AI Content (Direct API)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
    payload = {"contents": [{"parts":[{"text": "Give me a trending Hollywood movie news headline and 2 lines summary with emojis."}]}]}
    res = requests.post(url, json=payload).json()
    content = res['candidates'][0]['content']['parts'][0]['text']
    print("🤖 AI Content Generated.")

    # 2. Money Link
    link_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url=https://viralnewsai24.blogspot.com").json()
    link = link_res.get("shortenedUrl", "https://viralnewsai24.blogspot.com")

    # 3. Create Email
    msg = EmailMessage()
    msg['Subject'] = "Breaking AI News"
    msg['From'] = S_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(f"<h2>AI Update</h2><p>{content}</p><br><a href='{link}'>READ FULL STORY</a>", subtype='html')

    # 4. SEND (Using Port 465 SSL)
    print("📧 Attempting to login and send email...")
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(S_EMAIL, PASS)
    server.send_message(msg)
    server.quit()
    print("✅ SUCCESS! Email actually sent.")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        exit(1) # GitHub को फेल दिखाएगा ताकि हम गड़बड़ पकड़ सकें
