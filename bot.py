import os, requests, feedparser, random, json, sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# --- SETTINGS ---
def get_deep_human_article(headline, cat, g_key):
    """AI को असली न्यूज़ एडिटर की तरह 800 शब्दों का यूनिक आर्टिकल लिखने का निर्देश"""
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key}"
    
    styles = ["Investigative Journalist", "Viral Content Strategist", "Senior Tech Critic", "Bollywood Insider"]
    prompt = f"""Act as a professional {random.choice(styles)}. 
    Write a 800-word DEEP, UNIQUE, and HIGHLY ENGAGING news story about: "{headline}" (Category: {cat}).
    
    STRUCTURE RULES:
    1. Catchy H2 sub-headline.
    2. 150-word introduction.
    3. Use H3 tags for: 'Internal Leaks', 'Deep Analysis', and 'Social Media Reaction'.
    4. Bullet Points (<ul>) for 'Key Highlights'.
    5. Blockquote with emojis for Public Opinion.
    6. FAQ section with 2 questions for Google Ranking.
    7. Professional tone, no robot phrases. Return ONLY HTML body."""

    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=45).json()
        return res['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"<h2>Exclusive Report: {headline}</h2><p>Our team is analyzing the latest trends in {cat}. Full breakdown coming soon.</p>"

def run_viral_machine():
    print(f"🚀 Initializing Viral Machine v26.0 at {datetime.now()}")
    
    try:
        # Secrets उठाना
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        G_KEY = os.getenv("GEMINI_API")
        S_KEY = os.getenv("SHRINKME_API")

        # 25+ प्रीमियम न्यूज़ और यूट्यूब सोर्सेस
        sources = {
            "YouTube Trending India": "https://news.google.com/rss/search?q=trending+on+youtube+india&hl=en-IN&gl=IN&ceid=IN:en",
            "Gaming & Esports": "https://www.ign.com/rss/articles/feed",
            "Hollywood Insider": "https://variety.com/feed/",
            "Bollywood Buzz": "https://www.pinkvilla.com/feed",
            "Tech Revolution": "https://techcrunch.com/feed/",
            "Smartphone Leaks": "https://www.gsmarena.com/rss-news-reviews.php3",
            "Marvel/DC Universe": "https://screenrant.com/feed/",
            "Netflix Updates": "https://www.collider.com/feed/",
            "Space & NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss"
        }

        # रैंडम न्यूज़ चुनना (Retry Logic)
        cat_list = list(sources.items())
        random.shuffle(cat_list)
        item, cat = None, ""
        for c, rss in cat_list:
            feed = feedparser.parse(rss)
            if feed.entries:
                item = random.choice(feed.entries[:10])
                cat = c
                break
        
        if not item: return

        # AI Article & Money Link
        article = get_deep_human_article(item.title, cat, G_KEY)
        rand_id = random.randint(1000, 9999)
        image_url = f"https://loremflickr.com/800/450/news,viral,cinema?lock={rand_id}"
        
        money_res = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={item.link}").json()
        money_link = money_res.get("shortenedUrl", item.link)

        # --- प्रीमियम डिज़ाइन ---
        html_body = f"""
        <div style="font-family:'Segoe UI', sans-serif; max-width:850px; margin:auto; background:#fff; color:#111; border:1px solid #eee; border-radius:15px; overflow:hidden; box-shadow:0 15px 50px rgba(0,0,0,0.1);">
            <script type="application/ld+json">
            {{ "@context": "https://schema.org", "@type": "NewsArticle", "headline": "{item.title}", "image": ["{image_url}"], "datePublished": "{datetime.now().isoformat()}" }}
            </script>
            <img src="{image_url}" style="width:100%; border-bottom:5px solid #ff6600;">
            <div style="padding:45px;">
                <h1 style="font-size:36px; line-height:1.2; font-weight:900;">{item.title}</h1>
                <div style="font-size:18px; line-height:1.9; color:#444;">{article}</div>
                <div style="margin-top:50px; text-align:center; background:#000; padding:40px; border-radius:15px;">
                    <h2 style="color:#fff;">Unlock Full Data & Official Video</h2>
                    <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:18px 50px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block;">🚀 ACCESS DATA NOW</a>
                </div>
            </div>
        </div>
        """

        # --- Official API Posting ---
        creds = service_account.Credentials.from_service_account_info(service_info)
        scoped_creds = creds.with_scopes(['https://www.googleapis.com/auth/blogger'])
        service = build('blogger', 'v3', credentials=scoped_creds)
        
        post_data = {"kind": "blogger#post", "blog": {"id": BLOG_ID}, "title": item.title, "content": html_body}
        service.posts().insert(blogId=BLOG_ID, body=post_data, isDraft=False).execute()
        print(f"✅ SUCCESS! Published: {item.title}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_viral_machine()
