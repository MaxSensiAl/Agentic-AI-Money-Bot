import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. AI जर्नलिस्ट (OpenRouter Llama 3.1 - No Blocks)
# ==========================================
def generate_llama_article(headline, cat, or_key):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {or_key.strip()}",
        "Content-Type": "application/json"
    }
    
    # AI को 'इंसानी' बनाने का सबसे तगड़ा निर्देश
    prompt = f"""
    Act as India's #1 Viral News Blogger. Write a 1200-word EXPLOSIVE news article on: '{headline}'.
    Category: {cat}.
    
    STRICT BLOGGER RULES:
    1. STYLE: Fast-paced, emotional, and direct. Use "I am shocked," "The truth is finally out."
    2. WORD COUNT: MINIMUM 1000-1200 words of deep information.
    3. NO BOT WORDS: Strictly DO NOT use 'delve', 'moreover', 'comprehensive', 'era', 'shaping'.
    4. STRUCTURE: Use one H1, four H2, and six H3 subheadings. Use short paragraphs.
    5. SEO: Include 5 'People Also Ask' FAQs with long answers.
    6. META: Write a 150-char viral search description.
    
    FORMAT: Return ONLY a JSON object (strictly no markdown code blocks):
    {{
      "meta": "viral description",
      "article": "Full HTML content with subheadings",
      "faq": [ {{"q":"?","a":".."}} ],
      "tags": "trending, news, viral"
    }}
    """
    
    data = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        res = requests.post(url, headers=headers, json=data, timeout=120).json()
        raw_text = res['choices'][0]['message']['content'].strip()
        # JSON Repair Logic
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return None
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return None

# ==========================================
# 2. न्यूज़ हंटर (Trends Finder)
# ==========================================
def get_viral_news():
    sources = [
        ("Bollywood", "https://www.pinkvilla.com/feed"),
        ("YouTube Viral", "https://news.google.com/rss/search?q=trending+youtube+india&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Gaming", "https://www.ign.com/rss/articles/feed"),
        ("Tech & Gadgets", "https://techcrunch.com/feed/"),
        ("Breaking News", "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en")
    ]
    random.shuffle(sources)
    for cat, rss in sources:
        try:
            feed = feedparser.parse(rss)
            if feed.entries: return feed.entries, cat
        except: continue
    return None, None

# ==========================================
# 3. कमाई इंजन (ShrinkMe API)
# ==========================================
def get_money_link(url, s_key):
    try:
        api = f"https://shrinkme.io/api?api={s_key.strip()}&url={url}"
        res = requests.get(api, timeout=10).json()
        return res.get("shortenedUrl", url)
    except: return url

# ==========================================
# 4. मुख्य इंजन (The Unstoppable Machine)
# ==========================================
def run_power_bot():
    print("🔋 BOOTING UNSTOPPABLE LLAMA-3.1 ENGINE...")
    try:
        # Load Secrets
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        OR_KEY = os.getenv("OPENROUTER_API_KEY").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        # Blogger Auth
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        entries, category = get_viral_news()
        if not entries: return

        posted = False
        for entry in entries[:20]: # 20 खबरों को चेक करेगा
            print(f"🎯 Analyzing: {entry.title}")
            
            # AI आर्टिकल (Llama 3.1 never blocks!)
            data = generate_llama_article(entry.title, category, OR_KEY)
            if not data: continue

            # Earning Link
            money_link = get_money_link(entry.link, S_KEY)
            img_url = f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"

            # FAQ Schema Design
            faq_html = "".join([f"<b>Q: {f['q']}</b><p>A: {f['a']}</p>" for f in data.get('faq', [])])
            schema_faq = "".join([f'{{"@type":"Question","name":"{f["q"]}","acceptedAnswer":{{"@type":"Answer","text":"{f["a"]}"}}}},' for f in data.get('faq', [])])

            # Premium Design (High Conversion)
            full_html = f"""
            <div style='font-family:Arial, sans-serif; line-height:1.9; color:#111; max-width:800px; margin:auto;'>
                <img src='{img_url}' alt='{entry.title}' style='width:100%; border-radius:20px; box-shadow:0 15px 40px rgba(0,0,0,0.2);'/>
                <h1 style='color:#000; font-size:35px;'>{entry.title}</h1>
                <div class='main-article' style='font-size:18px;'>{data['article']}</div>
                
                <div style='background:#f4f4f4; padding:25px; border-radius:15px; margin-top:40px;'>
                    <h3>Essential Insights & FAQ</h3>{faq_html}
                </div>

                <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:50px; border:3px solid #ff6600;'>
                    <h2 style='color:#ff6600; margin-top:0;'>📢 WATCH EXCLUSIVE FOOTAGE</h2>
                    <p style='font-size:18px;'>Verified documents and unedited leaked video for this story are available below. Access the private server now.</p>
                    <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:18px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:24px; display:inline-block; box-shadow:0 5px 25px rgba(255,102,0,0.5);'>🚀 UNLOCK FULL DATA</a>
                    <p style='font-size:11px; margin-top:15px; color:#666;'>Verification: {random.randint(1000,9999)} | Secure Link</p>
                </div>
                <script type="application/ld+json">
                {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{schema_faq[:-1]}] }}
                </script>
            </div>
            """

            # Post LIVE
            try:
                service.posts().insert(blogId=BLOG_ID, body={
                    "title": "🔴 BREAKING: " + entry.title,
                    "content": full_html,
                    "labels": [category, "Trending", "Viral"],
                    "searchDescription": data['meta']
                }, isDraft=False).execute()
                
                print(f"✅ MISSION SUCCESS! Post is LIVE: {entry.title}")
                posted = True; break
            except Exception as e:
                print(f"❌ Blogger Fail: {e}"); continue

        if not posted:
            print("❌ All attempts failed. Check API Keys."); sys.exit(1)

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_power_bot()
