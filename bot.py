import os, requests, feedparser, random, json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# --- SETTINGS ---
def get_deep_human_article(headline, cat, g_key):
    """AI को एक वरिष्ठ पत्रकार की तरह 800 शब्दों का आर्टिकल लिखने का निर्देश"""
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key}"
    
    # अलग-अलग राइटिंग स्टाइल ताकि गूगल को हर बार नया और इंसानी लगे
    styles = ["Senior Investigative Journalist", "Viral Content King", "Industry Insider", "Expert Tech Critic", "Bollywood Expert"]
    style = random.choice(styles)
    
    prompt = f"""Act as a professional {style}. 
    Write a DEEP, 800-word, 100% UNIQUE blog post about: "{headline}" (Category: {cat}).
    
    STRUCTURE RULES:
    1. Shocking H2 sub-headline.
    2. 150-word introduction setting the scene.
    3. Use H3 tags for: 'The Core Investigation', 'Hidden Facts & Leaks', and 'Why it matters'.
    4. Use <ul> and <li> for 'Key Takeaways'.
    5. Add a <blockquote> with social media reaction emojis.
    6. Detailed technical specs or cast analysis.
    7. FAQ Section: 2 questions and answers for Google ranking.
    8. NO AI robotic talk. return ONLY HTML body."""

    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=45).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h2>Exclusive: {headline}</h2><p>Our global news team is analyzing the deep data behind this trending topic in {cat}. Stay tuned for the full breakdown.</p>"

def run_viral_machine():
    print(f"🚀 Initializing Master Machine v26.0...")

    # 20+ प्रीमियम सोर्सेस (YouTube, Tech, Gaming, NASA, Movies)
    sources = {
        "YouTube India Trending": "https://news.google.com/rss/search?q=trending+on+youtube+india&hl=en-IN&gl=IN&ceid=IN:en",
        "Hollywood Leaks": "https://variety.com/feed/",
        "Bollywood Buzz": "https://www.pinkvilla.com/feed",
        "Gaming & PS5": "https://www.ign.com/rss/articles/feed",
        "Tech Revolution": "https://techcrunch.com/feed/",
        "AI & Future Tech": "https://www.theverge.com/rss/index.xml",
        "Netflix/Web Series": "https://www.collider.com/feed/",
        "Marvel/DC Universe": "https://screenrant.com/feed/",
        "Space Exploration": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "Cricket/Sports News": "https://www.espn.com/espn/rss/news",
        "Auto/EV News India": "https://www.autocarindia.com/rss/news",
        "iPhone/Android Leaks": "https://www.gsmarena.com/rss-news-reviews.php3",
        "Business Strategy": "https://www.forbes.com/real-time/feed/",
        "Global Breaking News": "https://www.aljazeera.com/xml/rss/all.xml"
    }

    # रैंडम कैटेगरी और खबर चुनना (Robust Logic)
    source_list = list(sources.items())
    random.shuffle(source_list)
    item, selected_cat = None, ""

    for cat, rss in source_list:
        feed = feedparser.parse(rss)
        if feed.entries:
            item = random.choice(feed.entries[:10])
            selected_cat = cat
            break
    
    if not item: return

    # Secrets उठाना
    G_KEY = os.getenv("GEMINI_API")
    S_KEY = os.getenv("SHRINKME_API")
    BLOG_ID = os.getenv("BLOG_ID").strip()
    service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))

    print(f"📡 Selected: {item.title} | {selected_cat}")
    article_body = get_deep_human_article(item.title, selected_cat, G_KEY)

    # 1. Money Link
    try:
        r = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}").json()
        money_link = r.get("shortenedUrl", item.link)
    except:
        money_link = item.link

    # 2. Dynamic Image
    rand_id = random.randint(1000, 9999)
    image_url = f"https://loremflickr.com/800/450/news,tech,cinema?lock={rand_id}"

    # 3. प्रीमियम SEO डिज़ाइन
    html_content = f"""
    <div style="font-family:'Segoe UI', Arial; max-width:850px; margin:auto; background:#fff; color:#111; border-radius:15px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.15); border:1px solid #eee;">
        <script type="application/ld+json">
        {{ "@context": "https://schema.org", "@type": "NewsArticle", "headline": "{item.title}", "image": ["{image_url}"], "datePublished": "{datetime.now().isoformat()}" }}
        </script>
        <img src="{image_url}" style="width:100%; height:auto; border-bottom:5px solid #ff6600;" alt="News">
        <div style="padding:45px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:25px;">
                <span style="background:#ff6600; color:#000; padding:6px 15px; border-radius:4px; font-weight:bold; font-size:12px;">★ {selected_cat.upper()} SPECIAL ★</span>
                <span style="color:#999; font-size:12px;">{datetime.now().strftime('%d %b, %Y')}</span>
            </div>
            <h1 style="font-size:38px; line-height:1.2; font-weight:900; color:#000; margin-bottom:30px;">{item.title}</h1>
            <div style="font-size:18px; line-height:1.9; color:#444; text-align:justify;">{article_body}</div>
            <div style="margin-top:60px; text-align:center; background:#000; padding:50px; border-radius:20px;">
                <h2 style="color:#fff; font-size:24px; margin-bottom:25px;">Unlock Official Files & Detailed Report</h2>
                <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:22px 60px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:24px; display:inline-block; box-shadow:0 10px 30px rgba(255,102,0,0.5);">🔓 UNLOCK CONTENT NOW</a>
                <p style="font-size:11px; color:#666; margin-top:20px;">Verified Transfer v26.0 | Encrypted Agentic Protocol</p>
            </div>
        </div>
    </div>
    """

    # 4. Official API Posting (Direct & Fast)
    try:
        creds = service_account.Credentials.from_service_account_info(service_info)
        service = build('blogger', 'v3', credentials=creds)
        post_data = {{"kind": "blogger#post", "blog": {{"id": BLOG_ID}}, "title": item.title, "content": html_content}}
        service.posts().insert(blogId=BLOG_ID, body=post_data, isDraft=False).execute()
        print(f"✅ SUCCESS! Article Published: {item.title}")
    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    run_viral_machine()
