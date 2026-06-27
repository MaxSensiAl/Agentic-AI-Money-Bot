import os
import smtplib
import requests
from email.message import EmailMessage
import google.generativeai as genai

# Secrets (पक्का करें कि ये GitHub Settings में सही भरे हैं)
BLOGGER_EMAIL = os.getenv("BLOGGER_EMAIL")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD") 
GEMINI_KEY = os.getenv("GEMINI_API")
SHRINK_API = os.getenv("SHRINKME_API")

# 1. AI से कंटेंट लेना
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Give me a trending tech news headline and 3 lines about it.")
content = response.text

# 2. ShrinkMe लिंक बनाना
long_url = "https://viralnewsai24.blogspot.com"
short_res = requests.get(f"https://shrinkme.io/api?api={SHR_API}&url={long_url}").json()
money_link = short_res.get("shortenedUrl", long_url)

# 3. ईमेल तैयार करना
msg = EmailMessage()
msg['Subject'] = "Breaking AI Update"
msg['From'] = SENDER_EMAIL
msg['To'] = BLOGGER_EMAIL

html_body = f"<h2>Robot Update</h2><p>{content}</p><br><a href='{money_link}'>CLICK HERE</a>"
msg.add_alternative(html_body, subtype='html')

# 4. ईमेल भेजना (SSL के साथ)
# यहाँ अगर पासवर्ड गलत होगा तो GitHub पर Error दिखेगा
server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
server.login(SENDER_EMAIL, GMAIL_PASSWORD)
server.send_message(msg)
server.quit()

print("✅ EMAIL SENT SUCCESSFULLY!")
