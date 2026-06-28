import os, requests, feedparser, random, json, time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime

# --- CONFIGURATION (GitHub Secrets) ---
def run_viral_machine():
    try:
        service_json = os.getenv("SERVICE_ACCOUNT_JSON")
        if not service_json: raise ValueError("SERVICE_ACCOUNT_JSON is missing!")
        
        service_info = json.loads(service_json)
        BLOG_ID = os.getenv("BLOG_ID", "").strip()
        G_KEY = os.getenv("GEMINI_API")
        S_KEY = os.getenv("SHRINKME_API")

        print(f"🚀 Agentic AI v23.0 Waking Up... Time: {datetime.now()}")

        # 1. 20+ प्रीमियम ताज़ा न्यूज़ और यूट्यूब सोर्सेस
        sources = {
            "YouTube Trending India": "https://news.google.com/rss/search?q=trending+on+youtube+india&hl=en-IN&gl=IN&ceid=IN:en",
            "Gaming & PS5 News": "https://www.ign.com/rss/articles/feed",
            "Hollywood Leaks": "https://variety.com/feed/",
            "Bollywood Buzz": "https://www.pinkvilla.com/feed",
            "Tech Revolution": "https://techcrunch.com/feed/",
            "Gadget Reviews": "https://www.theverge.com/rss/index.xml",
            "Netflix & Web Series": "https://www.collider.com/feed/",
            "Smartphone Leaks": "https://www.gsmarena.com/rss-news-reviews.php3",
            "Space & NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
            "Cricket & Sports": "https://www.espn.com/espn/rss/news",
            "Anime & Manga": "https://www.animenewsnetwork.com/all/rss.xml",
            "Business Global": "https://www.forbes.com/real-time/feed/",
            "Crypto Trends": "https://cointelegraph.com/rss",
            "Marvel & DC": "https://screenrant.com/feed/"
        }

        # खबर ढूँढने का मज़बूत लॉजिक (Retry if empty)
        news_items = []
        selected_cat = ""
        source_list = list(sources.items())
        random.shuffle(source_list)

        for cat, rss_url in source_list:
            feed = feedparser.parse(rss_url)
            if feed.entries:
                news_items = feed.entries
                selected_cat = cat
                break
        
        if not news_items: return
        item = random.choice(news_items[:10])
        title, orig_url = item.title, item.link

        # 2. AI Article Generation (Fixed 'candidates' error)
        print(f"🤖 AI is writing deep article for: {title}")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"
        prompt = f"Act as a professional Viral Journalist. Write a DEEP, HUMAN-LIKE 800-word SEO article about: '{title}' in category {selected_cat}. Use HTML (h2, h3, b, ul, li). Include 'Hidden Facts' and 'Social Buzz' with emojis. Return ONLY HTML."
        
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=40).json()
        
        # 'candidates' एरर से बचने के लिए चेक
        if 'candidates' in res:
            article_body = res['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"⚠️ Gemini Error, using fallback. Details: {res}")
            article_body = f"<h2>Update: {title}</h2><p>Latest trending reports in {selected_cat} are emerging. Our team is analyzing the deep data behind this viral news.</p>"

        # 3. Photo & Money Link
        rand_id = random.randint(111, 999)
        image_url = f"https://loremflickr.com/800/450/viral,news,tech?lock={rand_id}"
        
        try:
            r = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={orig_url}").json()
            money_link = r.get("shortenedUrl", orig_url)
        except:
            money_link = orig_url

        # 4. प्रीमियम 'AGENTIC' डिज़ाइन
        html_content = f"""
        <div style="font-family:sans-serif; max-width:800px; margin:auto; background:#fff; color:#111; border-radius:20px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.15); border:1px solid #eee;">
            <script type="application/ld+json">
            {{ "@context": "https://schema.org", "@type": "NewsArticle", "headline": "{title}", "image": ["{image_url}"], "datePublished": "{datetime.now().isoformat()}" }}
            </script>
            <img src="{image_url}" style="width:100%; height:auto; border-bottom:5px solid #ff6600;" alt="News">
            <div style="padding:45px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:20px;">
                    <span style="background:#ff6600; color:#000; padding:6px 15px; border-radius:5px; font-weight:bold; font-size:12px;">★ {selected_cat.upper()} ★</span>
                    <span style="color:#aaa; font-size:12px;">Ref: AI-BOT-{rand_id}</span>
                </div>
                <h1 style="font-size:36px; line-height:1.2; font-weight:900; color:#000; margin-bottom:30px;">{title}</h1>
                <div style="font-size:18px; line-height:1.9; color:#333; text-align:justify;">{article_body}</div>
                <div style="margin-top:50px; text-align:center; background:#000; padding:50px; border-radius:20px;">
                    <h2 style="color:#fff; font-size:24px; margin-bottom:25px;">Unlock Official Files & Detailed Report</h2>
                    <a href="{money_link}" style="background:linear-gradient(45deg, #ff6600, #ff9900); color:#000; padding:20px 55px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:22px; display:inline-block; box-shadow:0 10px 30px rgba(255,102,0,0.4);">🔓 UNLOCK CONTENT NOW</a>
                    <p style="font-size:10px; color:#666; margin-top:15px;">Encrypted Data Tunneling v23.0 | Human-Verified Transfer</p>
                </div>
            </div>
        </div>
        """

        # 5. Official Blogger API Post
        creds = service_account.Credentials.from_service_account_info(service_info)
        service = build('blogger', 'v3', credentials=creds)
        post_data = {"kind": "blogger#post", "blog": {"id": BLOG_ID}, "title": title, "content": html_content}
        service.posts().insert(blogId=BLOG_ID, body=post_data).execute()
        print(f"✅ SUCCESS! Published: {title}")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    run_viral_machine()
