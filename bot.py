import os, requests, feedparser, random, json, time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

def get_deep_human_article(headline, cat, g_key):
    """AI को मजबूर करना कि वह एक असली प्रोफेशनल पत्रकार की तरह 800 शब्दों का गहरा लेख लिखे"""
    # Gemini का सबसे लेटेस्ट और पक्का API रास्ता (v1)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key}"
    
    # अलग-अलग राइटिंग स्टाइल ताकि गूगल को हर बार नया और इंसानी लगे
    styles = ["Senior Investigative Journalist", "Industry Insider", "Viral Content Specialist", "Tech Critic"]
    style = random.choice(styles)
    
    prompt = f"""Act as a {style}. Write a 800-word DEEP, UNIQUE, and HIGHLY ENGAGING news article about: "{headline}" in category {cat}.
    
    STRUCTURE RULES:
    1. Start with a catchy H2 headline that creates curiosity.
    2. Write a 150-word introduction setting the scene.
    3. Detailed Body: Use H3 tags for different sections like 'The Core Facts', 'Hidden Leaks', and 'Behind the Scenes'.
    4. Bullet Points: Use <ul> and <li> for 'Key Highlights' or 'Specs'.
    5. Social Media Reaction: Add a <blockquote> with emojis (🤩, 🤔, 🔥).
    6. Future Predictions: What does this mean for the industry?
    7. FAQ Section: 2 important questions and answers.
    8. Tone: Professional, human, and exciting. NO AI robot talk.
    
    Return ONLY the HTML body content."""

    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=40).json()
        if 'candidates' in res:
            return res['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"<h2>Analysis: {headline}</h2><p>Latest verified reports for {cat} are emerging. Our team is tracking the full story for a deep-dive investigation shortly.</p>"
    except:
        return f"<h2>Exclusive Update: {headline}</h2><p>Global trends in {cat} are shifting. Here is the first verified look at what is happening on the ground.</p>"

def run_viral_machine():
    print(f"🚀 Initializing Master Machine v24.0 at {datetime.now()}")

    # 1. 20+ प्रीमियम ताज़ा न्यूज़ और यूट्यूब सोर्सेस (Variety of Categories)
    sources = {
        "YouTube India Trending": "https://news.google.com/rss/search?q=trending+on+youtube+india&hl=en-IN&gl=IN&ceid=IN:en",
        "Hollywood Leaks": "https://variety.com/feed/",
        "Bollywood Buzz": "https://www.pinkvilla.com/feed",
        "Gaming & PS5": "https://www.ign.com/rss/articles/feed",
        "Tech Trends": "https://techcrunch.com/feed/",
        "AI Revolution": "https://www.theverge.com/rss/index.xml",
        "Marvel/DC Universe": "https://screenrant.com/feed/",
        "Netflix Updates": "https://www.collider.com/feed/",
        "NASA/Science": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "Cricket/Sports": "https://www.espn.com/espn/rss/news",
        "Gadget Reviews": "https://www.gsmarena.com/rss-news-reviews.php3",
        "Business Global": "https://www.forbes.com/real-time/feed/",
        "Auto News": "https://www.autocarindia.com/rss/news",
        "Web Series Leaks": "https://news.google.com/rss/search?q=web+series+india+leaks&hl=en-IN&gl=IN&ceid=IN:en"
    }

    # रैंडम कैटेगरी और ताज़ा खबर चुनना (Retry logic included)
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

    # 2. AI Article & Money Link
    G_KEY = os.getenv("GEMINI_API")
    S_KEY = os.getenv("SHRINKME_API")
    BLOG_ID = os.getenv("BLOG_ID").strip()
    service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))

    print(f"📡 Selected: {item.title} from {selected_cat}")
    article_body = get_deep_human_article(item.title, selected_cat, G_KEY)

    try:
        r = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}").json()
        money_link = r.get("shortenedUrl", item.link)
    except:
        money_link = item.link

    # 3. Dynamic Image & Premium Design
    rand_id = random.randint(1000, 9999)
    image_url = f"https://loremflickr.com/800/450/viral,news,cinema,tech?lock={rand_id}"

    html_content = f"""
    <div style="font-family:'Segoe UI', sans-serif; max-width:800px; margin:auto; background:#fff; color:#111; border-radius:15px; overflow:hidden; box-shadow:0 15px 50px rgba(0,0,0,0.15); border:1px solid #eee;">
        <!-- JSON-LD SEO Schema for Google Ranking -->
        <script type="application/ld+json">
        {{ "@context": "https://schema.org", "@type": "NewsArticle", "headline": "{item.title}", "image": ["{image_url}"], "datePublished": "{datetime.now().isoformat()}" }}
        </script>
        
        <img src="{image_url}" style="width:100%; height:auto; border-bottom:5px solid #ff6600;" alt="News">
        <div style="padding:40px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
                <span style="background:#ff6600; color:#000; padding:6px 15px; border-radius:4px; font-weight:bold; font-size:12px;">★ {selected_cat.upper()} ★</span>
                <span style="color:#aaa; font-size:12px;">Verified Report: {rand_id}</span>
            </div>
            <h1 style="font-size:36px; line-height:1.2; font-weight:900; color:#000; margin-bottom:30px;">{item.title}</h1>
            <div style="font-size:18px; line-height:1.9; color:#333; text-align:justify;">{article_body}</div>
            <div style="margin-top:50px; text-align:center; background:#000; padding:45px; border-radius:20px;">
                <h2 style="color:#fff; font-size:24px; margin-bottom:25px;">Unlock Official Media & Detailed Files</h2>
                <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:20px 60px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:24px; display:inline-block; box-shadow:0 10px 25px rgba(255,102,0,0.4);">🔓 UNLOCK CONTENT NOW</a>
                <p style="font-size:11px; color:#666; margin-top:20px;">Safe Data Transfer | Encrypted by Agentic AI Protocol</p>
            </div>
        </div>
    </div>
    """

    # 4. Official API Posting (No Email)
    try:
        creds = service_account.Credentials.from_service_account_info(service_info)
        service = build('blogger', 'v3', credentials=creds)
        post_data = {"kind": "blogger#post", "blog": {"id": BLOG_ID}, "title": item.title, "content": html_content}
        service.posts().insert(blogId=BLOG_ID, body=post_data).execute()
        print(f"✅ MISSION SUCCESS! Published in {selected_cat}")
    except Exception as e:
        print(f"❌ Blogger API Error: {e}")

if __name__ == "__main__":
    run_viral_machine()
