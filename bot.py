import os, requests, feedparser, random, json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# --- CONFIG ---
service_json = os.getenv("SERVICE_ACCOUNT_JSON")
service_info = json.loads(service_json)
BLOG_ID = os.getenv("BLOG_ID")
G_KEY = os.getenv("GEMINI_API")
S_KEY = os.getenv("SHRINKME_API")

def get_human_article(headline, cat):
    """AI को असली न्यूज़ एडिटर की तरह 700 शब्दों का आर्टिकल लिखने का निर्देश"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
    prompt = f"Act as a professional Viral News Strategist. Write a 700-word DEEP, SEO-friendly, and 100% UNIQUE blog post about: '{headline}' in category {cat}. Use HTML tags (h2, h3, b, ul, blockquote). Add an FAQ section with 2 questions. Return ONLY HTML."
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=40).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h2>Analysis: {headline}</h2><p>Latest verified reports for {cat} are emerging. Our team is tracking the data for a full breakdown.</p>"

def run_viral_machine():
    print(f"🚀 Initializing API Machine v22.1...")

    sources = {
        "Hollywood": "https://variety.com/feed/",
        "Bollywood": "https://www.pinkvilla.com/feed",
        "Gaming": "https://www.ign.com/rss/articles/feed",
        "Tech News": "https://techcrunch.com/feed/",
        "Gadgets": "https://www.theverge.com/rss/index.xml",
        "Netflix": "https://www.collider.com/feed/",
        "Space": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "Business": "https://www.forbes.com/real-time/feed/",
        "YouTube Trending": "https://news.google.com/rss/search?q=trending+on+youtube+india&hl=en-IN&gl=IN&ceid=IN:en"
    }

    # --- Robust Fetching Logic ---
    news_items = []
    selected_cat = ""
    
    # सोर्सेस को रैंडमली शफल (Shuffle) करना
    source_list = list(sources.items())
    random.shuffle(source_list)

    for cat, rss_url in source_list:
        print(f"📡 Trying source: {cat}")
        feed = feedparser.parse(rss_url)
        if feed.entries:
            news_items = feed.entries
            selected_cat = cat
            break # खबर मिल गई, अब आगे बढ़ने की ज़रूरत नहीं
    
    if not news_items:
        print("❌ All sources empty. Stopping.")
        return

    item = random.choice(news_items[:10])
    print(f"✅ Selected News from {selected_cat}: {item.title}")

    # 1. AI Article & Link
    article = get_human_article(item.title, selected_cat)
    rand_id = random.randint(1000, 9999)
    image_url = f"https://loremflickr.com/800/450/news,tech,cinema?lock={rand_id}"
    
    try:
        r = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}").json()
        money_link = r.get("shortenedUrl", item.link)
    except:
        money_link = item.link

    # 2. डिज़ाइन
    html_body = f"""
    <div style="font-family:sans-serif; max-width:800px; margin:auto; background:#fff; color:#111; border:1px solid #eee; border-radius:15px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.1);">
        <script type="application/ld+json">
        {{ "@context": "https://schema.org", "@type": "NewsArticle", "headline": "{item.title}", "image": ["{image_url}"], "datePublished": "{datetime.now().isoformat()}" }}
        </script>
        <img src="{image_url}" style="width:100%; height:auto; border-bottom:5px solid #ff6600;">
        <div style="padding:40px;">
            <h1 style="color:#000; font-size:32px; font-weight:900;">{item.title}</h1>
            <div style="color:#444; line-height:1.9; font-size:17px;">{article}</div>
            <div style="margin-top:40px; text-align:center; background:#000; padding:40px; border-radius:15px;">
                <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:15px 40px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block;">🚀 UNLOCK FULL DATA NOW</a>
            </div>
        </div>
    </div>
    """

    # 3. Official Blogger API Post
    creds = service_account.Credentials.from_service_account_info(service_info)
    service = build('blogger', 'v3', credentials=creds)
    post_data = {"kind": "blogger#post", "blog": {"id": BLOG_ID}, "title": item.title, "content": html_body}
    service.posts().insert(blogId=BLOG_ID, body=post_data).execute()
    print(f"✅ SUCCESS! Mission Accomplished.")

if __name__ == "__main__":
    run_viral_machine()
