import os, requests, feedparser, random, json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# --- CONFIG ---
service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
BLOG_ID = os.getenv("BLOG_ID")
G_KEY = os.getenv("GEMINI_API")
S_KEY = os.getenv("SHRINKME_API")

def get_human_article(headline, cat):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
    # AI को असली न्यूज़ एडिटर की तरह लिखने का निर्देश
    prompt = f"""Act as a Viral Content Strategist. Write a 700-word DEEP and 100% UNIQUE blog post about: "{headline}" (Category: {cat}).
    Use professional HTML tags (h2, h3, b, ul, blockquote).
    - Start with a shocking H2 subtitle.
    - Write a detailed intro, internal leaks section, and 'Social Media Reaction' with emojis.
    - Add an FAQ section with 2 questions for Google SEO.
    - Sound like a real human journalist. Return ONLY HTML body."""
    
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=35).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h2>Breaking Update: {headline}</h2><p>Latest verified reports for {cat} are emerging. Stay tuned for the full breakdown.</p>"

def run_viral_machine():
    print(f"🚀 Initializing API Machine at {datetime.now()}")

    # 25+ प्रीमियम सोर्सेस
    sources = {
        "Hollywood Leaks": "https://variety.com/feed/",
        "Bollywood Buzz": "https://www.pinkvilla.com/feed",
        "Gaming/GTA 6": "https://www.ign.com/rss/articles/feed",
        "Tech/AI News": "https://techcrunch.com/feed/",
        "Gadget Reviews": "https://www.theverge.com/rss/index.xml",
        "Marvel/DC": "https://screenrant.com/feed/",
        "Space & Science": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "Cricket/Sports": "https://www.espn.com/espn/rss/news",
        "Netflix Updates": "https://www.collider.com/feed/",
        "Global Trends": "https://news.google.com/rss/search?q=viral+trending+news&hl=en-IN&gl=IN&ceid=IN:en",
        "YouTube Trending": "https://news.google.com/rss/search?q=trending+on+youtube+india&hl=en-IN&gl=IN&ceid=IN:en"
    }

    cat, rss = random.choice(list(sources.items()))
    feed = feedparser.parse(rss)
    item = random.choice(feed.entries[:10])
    
    # Content & Money Link
    article = get_human_article(item.title, cat)
    rand_id = random.randint(1000, 9999)
    image_url = f"https://loremflickr.com/800/450/news,tech,movie/all?lock={rand_id}"
    
    try:
        short_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}").json()
        money_link = short_res.get("shortenedUrl", item.link)
    except:
        money_link = item.link

    # --- हाई-क्वालिटी 'AGENTIC' डिज़ाइन ---
    html_body = f"""
    <div style="font-family:sans-serif; max-width:800px; margin:auto; background:#fff; color:#222; border:1px solid #eee; padding:35px; border-radius:15px; box-shadow:0 15px 40px rgba(0,0,0,0.1);">
        <script type="application/ld+json">
        {{ "@context": "https://schema.org", "@type": "NewsArticle", "headline": "{item.title}", "image": ["{image_url}"], "datePublished": "{datetime.now().isoformat()}" }}
        </script>
        <img src="{image_url}" style="width:100%; border-radius:10px; border-bottom:5px solid #ff6600;">
        <h1 style="color:#000; font-size:32px; font-weight:900; margin:20px 0;">{item.title}</h1>
        <div style="color:#444; line-height:1.8; font-size:17px;">{article}</div>
        <div style="margin-top:40px; text-align:center; background:#000; padding:40px; border-radius:15px;">
            <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:15px 40px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:20px; display:inline-block;">🚀 UNLOCK FULL DATA NOW</a>
            <p style="color:#666; font-size:10px; margin-top:15px;">Ref ID: {rand_id} | Verified by Agentic AI Protocol</p>
        </div>
    </div>
    """

    # --- Official Blogger API Post ---
    creds = service_account.Credentials.from_service_account_info(service_info)
    service = build('blogger', 'v3', credentials=creds)
    post_data = {"kind": "blogger#post", "blog": {"id": BLOG_ID}, "title": item.title, "content": html_body}
    service.posts().insert(blogId=BLOG_ID, body=post_data).execute()
    print(f"✅ SUCCESS! Article Published: {item.title}")

if __name__ == "__main__":
    run_viral_machine()
