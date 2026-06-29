import os, requests, feedparser, random, json, sys, re, time
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==========================================
# 1. VIRAL BRAIN (Internet Trends)
# ==========================================
def get_viral_topic():
    queries = [
        "breaking news viral india", "bollywood leaked gossip", 
        "tech leaks india", "gaming viral news today", "cricket controversy"
    ]
    query = random.choice(queries)
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        feed = feedparser.parse(rss_url)
        if feed.entries: return feed.entries[0], query
    except: return None, None

# ==========================================
# 2. AI HUMANIZER (With Nuclear JSON Repair)
# ==========================================
def generate_powerful_content(headline, cat, g_key):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={g_key.strip()}"
    
    prompt = f"""
    Write a 1200-word HUMAN-LIKE news blog on: '{headline}'. 
    Category: {cat}.
    RULES: No robot words. Use H2, H3 tags. Include 5 FAQs. Viral Meta description.
    FORMAT: Return ONLY a JSON object. No Markdown. No backticks.
    {{ "meta": "Search desc", "article": "HTML content", "faq": [{{"q":"?","a":".."}}] }}
    """
    
    try:
        res = requests.post(url, json={"contents": [{"parts":[{"text": prompt}]}]}, timeout=90).json()
        raw_text = res['candidates'][0]['content']['parts'][0]['text']
        
        # --- NUCLEAR JSON REPAIR LOGIC ---
        # 1. फालतू मार्कडाउन (```json) हटाना
        clean_text = re.sub(r'```json|```', '', raw_text).strip()
        
        # 2. सिर्फ { } के बीच का हिस्सा निकालना
        json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        # 3. अगर फिर भी फेल हो (Fall-back)
        print("⚠️ Direct JSON failed, trying manual recovery...")
        return {
            "meta": headline[:150],
            "article": clean_text.replace("\n", "<br>"),
            "faq": []
        }
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return None

# ==========================================
# 3. CORE ENGINE
# ==========================================
def run_power_bot():
    print("🔋 Booting Up World's Most Powerful Engine...")
    try:
        service_info = json.loads(os.getenv("SERVICE_ACCOUNT_JSON"))
        BLOG_ID = os.getenv("BLOG_ID").strip()
        G_KEY = os.getenv("GEMINI_API").strip()
        S_KEY = os.getenv("SHRINKME_API").strip()

        # Blogger Auth
        scopes = ['https://www.googleapis.com/auth/blogger']
        creds = service_account.Credentials.from_service_account_info(service_info, scopes=scopes)
        service = build('blogger', 'v3', credentials=creds)

        # 1. ताज़ा खबर
        entry, niche = get_viral_topic()
        if not entry: return
        print(f"🔥 Trending: {entry.title}")

        # 2. AI आर्टिकल (Self-Healing)
        data = generate_powerful_content(entry.title, niche, G_KEY)
        if not data: 
            print("❌ System Failure: AI did not respond."); sys.exit(1)

        # 3. लिंक और इमेज
        try:
            money_link = requests.get(f"https://shrinkme.io/api?api={S_KEY}&url={entry.link}").json().get("shortenedUrl", entry.link)
        except: money_link = entry.link
        
        img_url = f"https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200"

        # 4. Final High-Conversion Design
        faq_html = "".join([f"<b>Q: {f.get('q','')}</b><p>A: {f.get('a','')}</p>" for f in data.get('faq', [])])
        
        final_html = f"""
        <div style='font-family:Segoe UI, sans-serif; line-height:1.9; color:#111; max-width:800px; margin:auto;'>
            <img src='{img_url}' style='width:100%; border-radius:20px; box-shadow:0 10px 40px rgba(0,0,0,0.2);'/>
            <p style='color:#666; font-size:13px; margin-top:10px;'>⚡ Live Update | {time.strftime("%d %b %Y")}</p>
            <div class='main-body' style='font-size:18px;'>{data.get('article','')}</div>
            <div style='background:#f4f4f4; padding:25px; border-radius:15px; margin-top:40px;'>
                <h3 style='color:#e67e22;'>People Also Ask (SEO)</h3>{faq_html}
            </div>
            <div style='background:#1a1a1a; padding:45px; border-radius:25px; text-align:center; color:#fff; margin-top:50px; border:3px solid #ff6600;'>
                <h2 style='color:#ff6600;'>📢 WATCH EXCLUSIVE LEAKED VIDEO</h2>
                <a href='{money_link}' rel='nofollow' style='background:#ff6600; color:#fff; padding:20px 50px; text-decoration:none; border-radius:100px; font-weight:bold; font-size:26px; display:inline-block;'>🚀 UNLOCK FULL DATA</a>
            </div>
        </div>
        """

        # 5. पब्लिश (Direct Live)
        print("📤 Publishing...")
        service.posts().insert(blogId=BLOG_ID, body={
            "title": "🔴 BREAKING: " + entry.title,
            "content": final_html,
            "labels": [niche.title(), "Trending", "Viral"],
            "searchDescription": data.get('meta', entry.title[:150])
        }, isDraft=False).execute()

        print("✅ SUCCESS! Article is Live.")

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}"); sys.exit(1)

if __name__ == "__main__":
    run_power_bot()
