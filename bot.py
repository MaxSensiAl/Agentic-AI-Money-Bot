import os, smtplib, requests
from email.message import EmailMessage

def run():
    B_EMAIL = os.getenv("BLOGGER_EMAIL")
    S_EMAIL = os.getenv("SENDER_EMAIL")
    PASS = os.getenv("GMAIL_APP_PASSWORD").replace(" ", "")
    G_KEY = os.getenv("GEMINI_API")
    S_KEY = os.getenv("SHRINKME_API")

    # 1. AI Content (With Error Handling)
    content = "New trending Hollywood movie release with amazing action scenes. Check it out now!"
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
        payload = {"contents": [{"parts":[{"text": "Write a viral 2-line movie news with emojis."}]}]}
        res = requests.post(url, json=payload).json()
        if 'candidates' in res:
            content = res['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"⚠️ Gemini API Issue: {res}")
    except:
        print("Fallback to default content.")

    # 2. Money Link
    link = f"https://shrinkme.io/api?api={S_KEY}&url=https://viralnewsai24.blogspot.com"
    try:
        r = requests.get(link).json()
        final_link = r.get("shortenedUrl", "https://viralnewsai24.blogspot.com")
    except:
        final_link = "https://viralnewsai24.blogspot.com"

    # 3. Create Email
    msg = EmailMessage()
    msg['Subject'] = "Daily Viral News"
    msg['From'] = S_EMAIL
    msg['To'] = B_EMAIL
    msg.add_alternative(f"<div style='background:#000; color:#00f2ff; padding:20px;'><h2>AI Update</h2><p>{content}</p><br><a href='{final_link}'>DOWNLOAD NOW</a></div>", subtype='html')

    # 4. SEND
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(S_EMAIL, PASS)
    server.send_message(msg)
    server.quit()
    print("✅ SUCCESS!")

if __name__ == "__main__":
    run()
