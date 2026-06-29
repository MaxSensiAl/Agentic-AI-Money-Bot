import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. AI जर्नलिस्ट (Human-Style 1000+ Words)
# ==========================================
def generate_human_seo_content(headline, cat, g_key):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key.strip()}"
    prompt = f"""
    Act as a World-Class Viral Blogger. Write a 1200-word EXPLOSIVE article on: '{headline}' ({cat}).
    - Tone: Spicy, Human-like, Emotional (Direct address: "You won't believe").
    - Structure: H1 for title, 6 H2/H3 subheadings, Bullet points, Bolding.
    - SEO: Include 5 FAQs and a 150-char meta description.
    FORMAT: Return ONLY a valid JSON:
    {{ "article": "HTML content", "meta": "description", "tags": "tag1, tag2", "faq": [{{"q":"?","a":".."}}] }}
    """
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=80).json()
        raw_text = res['candidates'][0]['content']['parts'][0]['text']
        clean_json = re.sub(r'```json|```', '', raw_text).strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"❌ AI Generation Failed: {e}")
        return None

# ==========================================
# 2. कमाई इंजन (Earnings & High CTR Design)
# ==========================================
def get_money_link(entry_link, s_key):
    try:
        res = requests.get(f"https://shrinkme.io/api?api={s_key.strip()}&url={entry_link}", timeout=15).json()
        return res.get("shortenedUrl", entry_link) if res.get("status") == "success" else entry_link
    except: return entry_link

# ==========================================
# 3. MAIN MASTER ENGINE (Official API + Owner Logic)
# ==========================================
def run_viral_machine():
    print("🚀 System Diagnosis Starting...")
    
    # Secrets Loading
    try:
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        G_KEY = os.getenv("GEMINI_API").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()
    except Exception as e:
        print(f"❌ Secret Error: {e}"); sys.exit(1)

    # Auth via Service Account
    try:
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ Auth Engine Failed: {e}"); sys.exit(1)

    # Trending Sources
    sources = [
        ("Bollywood", "https://www.pinkvilla.com/feed"),
        ("Gaming", "https://www.ign.com/rss/articles/feed"),
        ("YouTube Viral", "https://news.google.com/rss/search?q=trending+youtube+india&hl=en-IN&gl=IN&ceid=IN:en"),
        ("India News", "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en")
    ]
    random.shuffle(sources)
    cat, rss = sources[0]
    feed = feedparser.parse(rss)
    if not feed.entries: print("⏭️ Source empty"); return
    entry = feed.entries[0]

    print(f"🎯 News Target: {entry.title}")
    
    # AI Article & Money Link
    data = generate_human_seo_content(entry.title, cat, G_KEY)
    if not data: sys.exit(1)
    money_link = get_money_link(entry.link, S_KEY)

    # SEO Image & Schema
    img_match = re.search(r'<img [^>]*src="([^"]+)"', getattr(entry, 'description', ''))
    img_url = img_match.group(1) if img_match else f"https://source.unsplash.com/1200x675/?{cat},trending"
    
    faq_schema = "".join([f'{{"@type":"Question","name":"{f["q"]}","acceptedAnswer":{{"@type":"Answer","text":"{f["a"]}"}}}},' for f in data['faq']])

    # Premium HTML Template (High Earnings)
    final_html = f"""
    <div style='font-family:Segoe UI, sans-serif; line-height:1.8; color:#111;'>
        <img src='{img_url}' alt='{entry.title}' title='{entry.title}' style='width:100%; border-radius:20px; box-shadow:0 15px 35px rgba(0,0,0,0.2);'/>
        <div style='margin-top:20px;'>{data['article']}</div>
        
        <div style='background:#fff0f0; border:3px dashed #ff0000; padding:35px; border-radius:20px; text-align:center; margin-top:50px;'>
            <h2 style='color:#ff0000; margin-top:0;'>🛑 BIG REVEAL & SOURCE DATA</h2>
            <p style='font-size:18px;'>Access the original unedited leaked media and full official report below.</p>
            <a href='{money_link}' rel='nofollow' style='background:#ff0000; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:26px; display:inline-block; box-shadow:0 10px 25px rgba(255,0,0,0.4); animation: pulse 2s infinite;'>🚀 UNLOCK FULL DATA SOURCE</a>
            <p style='font-size:12px; color:#999; margin-top:15px;'>Verification ID: {random.randint(1000,9999)} | Secure Link</p>
        </div>
        
        <script type="application/ld+json">
        {{ "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{faq_schema[:-1]}] }}
        </script>
    </div>
    """

    # --- THE POSTING (The Fix) ---
    try:
        result = service.posts().insert(blogId=BLOG_ID, body={
            "kind": "blogger#post",
            "title": "🔴 BREAKING: " + entry.title,
            "content": final_html,
            "labels": [cat, "Trending", "Live"],
            "searchDescription": data['meta']
        }, isDraft=False).execute()
        
        if 'id' in result:
            print(f"✅ MISSION ACCOMPLISHED! Article is LIVE: {result.get('url')}")
        else:
            print(f"❌ Rejection: {result}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ BLOGGER API ERROR: {e}")
        print("💡 SOLUTION: Add the Service Account as OWNER in Google Search Console!")
        sys.exit(1)

if __name__ == "__main__":
    run_viral_machine()
