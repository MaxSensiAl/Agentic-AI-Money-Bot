import os, requests, feedparser, random, json, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

def get_deep_human_article(headline, cat, g_key):
    """AI को मजबूर करना कि वह 800 शब्दों का असली और गहरा न्यूज़ आर्टिकल लिखे"""
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key}"
    styles = ["Investigative Journalist", "Industry Insider", "Viral Content King", "Tech Critic"]
    style = random.choice(styles)
    
    prompt = f"""Act as a professional {style}. 
    Write a 800-word DEEP, UNIQUE, and HIGHLY ENGAGING news story about: "{headline}" in category {cat}.
    
    STRUCTURE RULES:
    1. Start with a shocking H2 headline.
    2. Write a detailed 150-word introduction.
    3. Detailed Body: Use H3 tags for: 'The Core Facts', 'Hidden Leaks', and 'Why it matters'.
    4. Bullet Points: Use <ul> and <li> for 'Key Highlights'.
    5. Social Buzz: Add a <blockquote> with emojis (🤩, 🤔, 🔥).
    6. Future Outlook: What happens next?
    7. FAQ Section: 2 questions and answers.
    8. Meta Data: Add 5 trending keywords at the bottom.
    
    Note: NO robot talk. return ONLY HTML body."""

    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=45).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h2>Exclusive Analysis: {headline}</h2><p>Latest verified reports on {cat} are emerging. Stay tuned for the full breakdown.</p>"

def run_agentic_system():
    print(f"🚀 Mission Started at {datetime.now()}")
    try:
        # Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        G_KEY = os.getenv("GEMINI_API")
        S_KEY = os.getenv("SHRINKME_API")

        # 20+ प्रीमियम सोर्सेस
        sources = {
            "YouTube Trending": "https://news.google.com/rss/search?q=trending+on+youtube+india&hl=en-IN&gl=IN&ceid=IN:en",
            "Hollywood": "https://variety.com/feed/",
            "Bollywood": "https://www.pinkvilla.com/feed",
            "Gaming": "https://www.ign.com/rss/articles/feed",
            "Tech": "https://techcrunch.com/feed/",
            "Science": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
            "Marvel/DC": "https://screenrant.com/feed/",
            "Netflix": "https://www.collider.com/feed/",
            "Cricket": "https://www.espn.com/espn/rss/news",
            "Gadgets": "https://www.theverge.com/rss/index.xml"
        }

        cat, rss = random.choice(list(sources.items()))
        feed = feedparser.parse(rss)
        item = random.choice(feed.entries[:10])
        print(f"📡 Selected: {item.title} | {cat}")

        # AI Content & Money Link
        article = get_deep_human_article(item.title, cat, G_KEY)
        money_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}").json()
        money_link = money_res.get("shortenedUrl", item.link)

        # Image
        image_url = f"https://loremflickr.com/800/450/news,viral,tech?lock={random.randint(1,999)}"

        # डिज़ाइन (Agentic Look)
        html_body = f"""
        <div style="font-family:sans-serif; max-width:800px; margin:auto; background:#fff; color:#111; border:1px solid #eee; border-radius:15px; overflow:hidden; box-shadow:0 15px 50px rgba(0,0,0,0.1);">
            <script type="application/ld+json">
            {{ "@context": "https://schema.org", "@type": "NewsArticle", "headline": "{item.title}", "image": ["{image_url}"], "datePublished": "{datetime.now().isoformat()}" }}
            </script>
            <img src="{image_url}" style="width:100%; border-bottom:5px solid #ff6600;">
            <div style="padding:40px;">
                <h1 style="color:#000; font-size:34px; font-weight:900;">{item.title}</h1>
                <div style="color:#444; line-height:1.9; font-size:18px;">{article}</div>
                <div style="margin-top:50px; text-align:center; background:#000; padding:45px; border-radius:20px;">
                    <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:20px 60px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block;">🚀 UNLOCK FULL CONTENT NOW</a>
                </div>
            </div>
        </div>
        """

        # Official API Posting
        creds = service_account.Credentials.from_service_account_info(service_info)
        service = build('blogger', 'v3', credentials=creds)
        post_data = {{"kind": "blogger#post", "blog": {{"id": BLOG_ID}}, "title": item.title, "content": html_body}}
        
        # Post Live
        result = service.posts().insert(blogId=BLOG_ID, body=post_data, isDraft=False).execute()
        print(f"✅ SUCCESS! Article Published: {{result.get('url')}}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    run_agentic_system()
