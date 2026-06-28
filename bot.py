import os, requests, feedparser, random, json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# --- SETTINGS (GitHub Secrets) ---
service_account_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
BLOG_ID = os.getenv("BLOG_ID")
G_KEY = os.getenv("GEMINI_API")
S_KEY = os.getenv("SHRINKME_API")

def get_deep_article(headline, cat):
    """AI को एक असली एक्सपर्ट की तरह आर्टिकल लिखने का निर्देश"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
    
    # अलग-अलग राइटिंग स्टाइल ताकि गूगल इसे 'असली' माने
    style = random.choice(["Investigative Journalist", "Tech Geek", "Storyteller", "Expert Critic"])
    
    prompt = f"""Act as a {style}. Write a 600-word DEEP, ENGAGING, and HUMAN-LIKE news article about: "{headline}" in category {cat}.
    Structure with HTML: <h2> Catchy Subtitle, <h3> Detailed Breakdowns, <ul> Points, <b> Highlights.
    Include:
    1. A detailed backstory.
    2. Exclusive facts & rumors section.
    3. Public reaction with emojis.
    4. 5 Trending Meta Keywords at the end.
    Return ONLY HTML body."""

    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=40).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h2>Analysis: {headline}</h2><p>Latest verified reports for {cat} are emerging. Stay tuned for the full breakdown.</p>"

def run_api_machine():
    print(f"🚀 Starting Agentic Engine v21.0...")

    # 20+ सोर्सेस (YouTube Trending + Major News)
    news_sources = {
        "Gaming": "https://www.ign.com/rss/articles/feed",
        "Hollywood": "https://variety.com/feed/",
        "Bollywood": "https://www.pinkvilla.com/feed",
        "Tech Trends": "https://techcrunch.com/feed/",
        "AI Revolution": "https://www.theverge.com/rss/index.xml",
        "Marvel/DC Universe": "https://screenrant.com/feed/",
        "Netflix/Web Series": "https://www.collider.com/feed/",
        "Gadget Leaks": "https://www.gsmarena.com/rss-news-reviews.php3",
        "Space & NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "Sports/Cricket": "https://www.espn.com/espn/rss/news",
        "Business Global": "https://www.forbes.com/real-time/feed/",
        "Auto/EV Updates": "https://www.autocarindia.com/rss/news",
        "Crypto News": "https://cointelegraph.com/rss",
        "YouTube Trending India": "https://news.google.com/rss/search?q=trending+on+youtube+india&hl=en-IN&ceid=IN:en"
    }

    # रैंडम कैटेगरी और टॉप खबर चुनना
    cat_name, rss_url = random.choice(list(news_sources.items()))
    feed = feedparser.parse(rss_url)
    if not feed.entries: return
    item = random.choice(feed.entries[:10])
    
    # AI Article & Money Link
    article = get_deep_article(item.title, cat_name)
    rand_id = random.randint(1000, 9999)
    image_url = f"https://loremflickr.com/800/450/{cat_name.lower().replace(' ', '')}/all?lock={rand_id}"
    
    try:
        r = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}").json()
        money_link = r.get("shortenedUrl", item.link)
    except:
        money_link = item.link

    # --- प्रीमियम 'AGENTIC' डिज़ाइन ---
    html_body = f"""
    <div style="font-family:'Segoe UI', Arial; max-width:800px; margin:auto; background:#fff; color:#111; border:1px solid #eee; border-radius:15px; overflow:hidden; box-shadow:0 15px 40px rgba(0,0,0,0.1);">
        <img src="{image_url}" style="width:100%; height:auto; border-bottom:5px solid #ff6600;">
        <div style="padding:40px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
                <span style="background:#ff6600; color:#000; padding:5px 12px; border-radius:4px; font-weight:bold; font-size:12px;">★ {cat_name.upper()} SPECIAL ★</span>
                <span style="color:#aaa; font-size:11px;">Ref ID: {rand_id}</span>
            </div>
            <h1 style="font-size:32px; line-height:1.2; font-weight:900; color:#000; margin-bottom:25px;">{item.title}</h1>
            <div style="font-size:18px; line-height:1.9; color:#333; text-align:justify;">{article}</div>
            <div style="margin-top:50px; text-align:center; background:#000; padding:45px; border-radius:20px;">
                <h3 style="color:#fff;">Want to Unlock Original Media & Files?</h3>
                <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:18px 50px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block; box-shadow:0 10px 20px rgba(255,102,0,0.4);">🔓 UNLOCK DATA NOW</a>
            </div>
        </div>
    </div>
    """

    # --- Official Blogger API Post ---
    try:
        creds = service_account.Credentials.from_service_account_info(service_account_info)
        service = build('blogger', 'v3', credentials=creds)
        
        post_data = {"kind": "blogger#post", "blog": {"id": BLOG_ID}, "title": item.title, "content": html_body}
        service.posts().insert(blogId=BLOG_ID, body=post_data).execute()
        print(f"✅ SUCCESS! Article Published: {item.title}")
    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    run_api_machine()
