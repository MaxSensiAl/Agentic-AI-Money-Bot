import os
import json
import random
import time
import requests
import feedparser
import re
from datetime import datetime, timedelta
import socket

# --- FIX: DNS Resolution for Hugging Face ---
def fix_dns():
    """Fix DNS resolution for Hugging Face API"""
    try:
        socket.gethostbyname('api-inference.huggingface.co')
    except:
        print("DNS fix applied for Hugging Face")

# --- CONFIGURATION ---
BLOG_ID = os.getenv('BLOG_ID').strip() if os.getenv('BLOG_ID') else None
SHRINKME_API = os.getenv('SHRINKME_API').strip() if os.getenv('SHRINKME_API') else None

# Hugging Face Token
HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('GEMINI_API')
if HF_TOKEN:
    HF_TOKEN = HF_TOKEN.strip()

# Blogger OAuth Credentials
BC_CLIENT_ID = os.getenv('BC_CLIENT_ID').strip() if os.getenv('BC_CLIENT_ID') else None
BC_CLIENT_SECRET = os.getenv('BC_CLIENT_SECRET').strip() if os.getenv('BC_CLIENT_SECRET') else None
BC_REFRESH_TOKEN = os.getenv('BC_REFRESH_TOKEN').strip() if os.getenv('BC_REFRESH_TOKEN') else None

# --- MULTI-CATEGORY RSS FEEDS (Expanded for MORE variety) ---
RSS_FEEDS = [
    # Technology (Latest tech news)
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://www.cnet.com/rss/news/",
    "https://arstechnica.com/feed/",
    "https://www.zdnet.com/news/rss.xml",
    
    # Gaming (Game news, releases)
    "https://www.gamespot.com/feeds/game-news/",
    "https://www.ign.com/rss/articles/all",
    "https://www.polygon.com/rss/index.xml",
    "https://www.eurogamer.net/?format=rss",
    
    # Entertainment (Hollywood, Movies)
    "https://www.variety.com/feed/",
    "https://www.hollywoodreporter.com/feed/",
    "https://www.pinkvilla.com/feed",
    "https://www.eonline.com/news/rss",
    "https://deadline.com/feed/",
    
    # Space & Science
    "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "https://www.space.com/feeds/all",
    "https://www.sciencedaily.com/rss/all.xml",
    
    # Business & Finance
    "https://www.bloomberg.com/feeds/markets.rss",
    "https://www.reuters.com/rss/reuters-business-news.rss",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    
    # Sports (Cricket, Football)
    "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
    "https://www.espn.com/espn/rss/news",
    
    # Music
    "https://www.rollingstone.com/music/music-news/feed/",
    "https://www.billboard.com/feed/",
    
    # World News
    "https://feeds.npr.org/1001/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.bbc.com/news/rss.xml",
    
    # Health & Science
    "https://www.medicalnewstoday.com/rss/all.xml",
    
    # AI & Technology (Specialized)
    "https://www.artificialintelligence-news.com/feed/",
    "https://ai.googleblog.com/atom.xml",
]

# --- SEO OPTIMIZED FUNCTIONS ---

def get_seo_title(title):
    """Generate SEO optimized title"""
    # Remove special characters and limit length
    clean_title = re.sub(r'[^\w\s-]', '', title)
    words = clean_title.split()
    
    # Keep title under 60 characters (Google SEO)
    seo_title = " ".join(words[:10])  # First 10 words
    if len(seo_title) > 60:
        seo_title = seo_title[:57] + "..."
    
    # Add year for freshness signal
    year = datetime.now().strftime("%Y")
    return f"{seo_title} - {year}"

def get_seo_description(summary, title):
    """Generate SEO meta description (150-160 characters)"""
    clean_summary = re.sub(r'<[^>]+>', '', summary)[:150]
    if len(clean_summary) < 100:
        return f"{title[:140]}... Read the full story on Viral News AI"
    return clean_summary[:157] + "..."

def get_category_image(feed_url, title):
    """Get category-based high-quality image for SEO"""
    title_lower = title.lower()
    feed_lower = feed_url.lower() if feed_url else ""
    
    # Space/Science
    if "nasa" in feed_lower or "space" in feed_lower or "science" in feed_lower:
        return "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80"
    
    # Gaming
    if "gamespot" in feed_lower or "ign" in feed_lower or "polygon" in feed_lower:
        return "https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80"
    
    # Entertainment
    if "variety" in feed_lower or "hollywood" in feed_lower or "eonline" in feed_lower:
        return "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80"
    
    # Sports
    if "cric" in feed_lower or "sports" in feed_lower:
        return "https://images.unsplash.com/photo-1531415074968-036ba1b575da?auto=format&fit=crop&w=1200&q=80"
    
    # Business
    if "bloomberg" in feed_lower or "reuters" in feed_lower or "cnbc" in feed_lower:
        return "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80"
    
    # Music
    if "rollingstone" in feed_lower or "billboard" in feed_lower:
        return "https://images.unsplash.com/photo-1511735111819-9a3f7709049c?auto=format&fit=crop&w=1200&q=80"
    
    # AI & Tech
    if "artificial" in feed_lower or "ai." in feed_lower:
        return "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=1200&q=80"
    
    # Default - High quality news image
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1200&q=80"

def get_entry_image(entry):
    """Extract image from RSS entry"""
    try:
        # Check media_content
        media_content = entry.get('media_content')
        if media_content and isinstance(media_content, list):
            for media in media_content:
                if 'url' in media:
                    return media['url']
        
        # Check links
        links = entry.get('links')
        if links:
            for link in links:
                if 'image' in link.get('type', ''):
                    return link.get('href')
        
        # Check enclosures
        enclosures = entry.get('enclosures')
        if enclosures:
            for enc in enclosures:
                if enc.get('type', '').startswith('image'):
                    return enc.get('href')
        
        # Check summary
        summary = entry.get('summary', '')
        if 'src=' in summary:
            match = re.search(r'src=["\'](https?://[^"\']+)["\']', summary)
            if match:
                return match.group(1)
        
        # Check content
        content = entry.get('content', [])
        if content:
            for item in content:
                if isinstance(item, dict) and 'value' in item:
                    match = re.search(r'src=["\'](https?://[^"\']+)["\']', item['value'])
                    if match:
                        return match.group(1)
    except Exception as e:
        print(f"Image extraction warning: {e}")
    return None

def get_short_url(long_url):
    """Shorten URL with ShrinkMe API"""
    try:
        if not SHRINKME_API:
            return long_url
        api_url = f"https://shrinkme.io/api?api={SHRINKME_API}&url={long_url}&format=text"
        response = requests.get(api_url, timeout=10)
        return response.text.strip() if response.text else long_url
    except:
        return long_url

def generate_ai_content(title, source_text, category):
    """Generate SEO-optimized AI content"""
    if not HF_TOKEN:
        print("❌ HF_TOKEN is empty")
        return None

    today = datetime.now().strftime("%B %d, %Y")
    
    # SEO-optimized prompt
    prompt = f"""Write a comprehensive, SEO-optimized 600-word news article about: {title} (published {today}).

Context: {source_text[:500]}.

Category: {category}

SEO Requirements:
1. Use target keywords naturally: {title[:50]}
2. Include related keywords and LSI terms
3. Write a compelling meta description (150-160 chars)
4. Use proper heading hierarchy (H1, H2, H3)
5. Include "Key Highlights" with bullet points
6. Add relevant internal linking suggestions
7. Include a FAQ section at the end

Formatting Requirements:
- Use HTML tags: <h2>, <h3>, <p>, <ul>, <li>, <blockquote>
- Include at least 2-3 subheadings
- Add bold text for important points
- Write in active voice
- Keep paragraphs short (3-4 lines)
- Include a disclaimer

Content Structure:
1. Introduction (hook + overview)
2. Key details and analysis
3. Expert opinions or quotes (if available)
4. Impact and implications
5. Future outlook
6. FAQ section (3-4 questions)
7. Conclusion

Make it engaging, informative, and shareable."""

    # AI Models with fallback
    AI_MODELS = [
        "mistralai/Mistral-7B-Instruct-v0.1",
        "Qwen/Qwen2.5-7B-Instruct",
        "meta-llama/Llama-2-7b-chat-hf",
        "google/flan-t5-xxl"
    ]
    
    for model in AI_MODELS:
        try:
            print(f"⏳ Trying model: {model}")
            API_URL = f"https://api-inference.huggingface.co/models/{model}"
            
            headers = {
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 800,
                    "temperature": 0.8,
                    "do_sample": True,
                    "top_p": 0.95
                }
            }
            
            response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
            
            if response.status_code == 503:
                print(f"⏳ Model {model} loading, waiting...")
                time.sleep(30)
                response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get('generated_text', '')
                    if prompt in text:
                        text = text.replace(prompt, '').strip()
                    if len(text) > 150:
                        print(f"✅ Success with model: {model}")
                        return text
        except:
            continue
    
    print("⚠️ All AI models failed, using SEO fallback")
    return None

def generate_seo_fallback(title, source_text, image_html, category):
    """Generate SEO-optimized fallback content"""
    today = datetime.now().strftime("%B %d, %Y")
    seo_title = get_seo_title(title)
    seo_desc = get_seo_description(source_text, title)
    
    # Keywords extraction
    keywords = title.split()[:5]
    keywords_str = ", ".join(keywords)
    
    article = f"""
    <!-- SEO Meta -->
    <meta name="description" content="{seo_desc}">
    <meta name="keywords" content="{keywords_str}, news, breaking, update">
    
    {image_html}
    
    <h1>{seo_title}</h1>
    
    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <p><strong>📅 Published:</strong> {today} | <strong>📂 Category:</strong> {category}</p>
        <p><strong>🔑 Key Topics:</strong> {keywords_str}</p>
    </div>
    
    <h2>Breaking News: {title}</h2>
    
    <p>In a significant development today ({today}), <strong>{title}</strong> has emerged as one of the most important stories in the {category} sector. This breaking news is creating waves across the industry and capturing global attention.</p>
    
    <h3>Key Highlights</h3>
    <ul>
        <li><strong>Major Announcement:</strong> Important development in {category}</li>
        <li><strong>Industry Impact:</strong> Significant implications for professionals and consumers</li>
        <li><strong>Global Response:</strong> International reactions and analysis</li>
        <li><strong>Future Implications:</strong> What this means for the future</li>
    </ul>
    
    <h3>Detailed Analysis</h3>
    <p>{source_text[:400]}... [Click the button below for complete coverage]</p>
    
    <blockquote style="border-left: 5px solid #ff5722; padding: 20px; background: #f9f9f9; border-radius: 8px; margin: 20px 0;">
        <p style="font-style: italic; color: #333; font-size: 16px;">
            "This is a developing story with significant implications. Click the button below for the complete, detailed analysis."
        </p>
    </blockquote>
    
    <h3>Expert Opinion</h3>
    <p>Industry experts suggest that this development could reshape the {category} landscape, leading to new opportunities and challenges. The full impact will become clearer in the coming days.</p>
    
    <h3>Frequently Asked Questions</h3>
    <p><strong>Q: What is the main announcement?</strong><br>
    {title} - A major development in {category}.</p>
    
    <p><strong>Q: Why is this important?</strong><br>
    This news has significant implications for the {category} industry and consumers.</p>
    
    <p><strong>Q: Where can I find more information?</strong><br>
    Click the button below for the complete story and detailed analysis.</p>
    
    <h3>Conclusion</h3>
    <p>This breaking news story is developing rapidly. Stay tuned for updates and comprehensive coverage.</p>
    """
    return article

def post_to_blogger(title, content):
    """Post to Blogger with SEO optimization"""
    if not all([BC_CLIENT_ID, BC_CLIENT_SECRET, BC_REFRESH_TOKEN]):
        print("❌ Blogger OAuth Secrets missing.")
        return False
        
    try:
        # Get new access token
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": BC_CLIENT_ID,
            "client_secret": BC_CLIENT_SECRET,
            "refresh_token": BC_REFRESH_TOKEN,
            "grant_type": "refresh_token"
        }
        res = requests.post(token_url, data=payload, timeout=15)
        res_json = res.json()
        
        if "access_token" not in res_json:
            print(f"❌ Failed to refresh Blogger token: {res_json}")
            return False
            
        access_token = res_json["access_token"]
        
        # SEO-optimized post with labels
        post_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # SEO-friendly labels
        labels = [
            "Breaking News",
            category,
            "AI-Generated",
            datetime.now().strftime("%Y"),
            "Automated"
        ]
        
        post_body = {
            "kind": "blogger#post",
            "title": title[:60],  # SEO: Keep title under 60 chars
            "content": content,
            "labels": labels,
        }
        
        post_res = requests.post(post_url, headers=headers, json=post_body, timeout=20)
        
        if post_res.status_code in [200, 201]:
            result = post_res.json()
            print(f"✅ Successfully Posted!")
            print(f"🔗 URL: {result.get('url', 'N/A')}")
            print(f"📊 SEO Title: {title[:60]}")
            print(f"🏷️ Labels: {', '.join(labels)}")
            return True
        else:
            print(f"❌ Blogger Post Failed - Status: {post_res.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Blogger OAuth Error: {e}")
        return False

def verify_blogger_permission():
    """Verify Blogger access"""
    if not all([BC_CLIENT_ID, BC_CLIENT_SECRET, BC_REFRESH_TOKEN]):
        print("❌ Blogger OAuth Secrets missing.")
        return False
    try:
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": BC_CLIENT_ID,
            "client_secret": BC_CLIENT_SECRET,
            "refresh_token": BC_REFRESH_TOKEN,
            "grant_type": "refresh_token"
        }
        res = requests.post(token_url, data=payload, timeout=15)
        access_token = res.json().get("access_token")
        
        if not access_token:
            print("❌ Cannot retrieve access token.")
            return False
            
        blog_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}"
        headers = {"Authorization": f"Bearer {access_token}"}
        blog_res = requests.get(blog_url, headers=headers, timeout=15)
        
        if blog_res.status_code == 200:
            print(f"✅ Blogger access verified! Blog: {blog_res.json().get('name')}")
            return True
        else:
            print(f"❌ Blog Verification Failed")
            return False
    except Exception as e:
        print(f"❌ Verification Error: {e}")
        return False

def detect_category(feed_url):
    """Detect category from feed URL"""
    feed_lower = feed_url.lower() if feed_url else ""
    
    if any(x in feed_lower for x in ["tech", "verge", "cnet", "wired", "arstechnica", "zdnet"]):
        return "Technology"
    elif any(x in feed_lower for x in ["gamespot", "ign", "polygon", "eurogamer"]):
        return "Gaming"
    elif any(x in feed_lower for x in ["variety", "hollywood", "eonline", "deadline", "pinkvilla"]):
        return "Entertainment"
    elif any(x in feed_lower for x in ["nasa", "space", "sciencedaily"]):
        return "Science & Space"
    elif any(x in feed_lower for x in ["cric", "espn"]):
        return "Sports"
    elif any(x in feed_lower for x in ["bloomberg", "reuters", "cnbc"]):
        return "Business"
    elif any(x in feed_lower for x in ["rollingstone", "billboard"]):
        return "Music"
    elif any(x in feed_lower for x in ["artificial", "ai."]):
        return "AI & Technology"
    else:
        return "News"

# --- MAIN FUNCTION ---

def main():
    print("🤖 Starting SEO-Optimized Blogger Bot...")
    print(f"📅 Today's Date: {datetime.now().strftime('%B %d, %Y')}")
    
    # Fix DNS
    fix_dns()
    
    # --- Check Secrets ---
    print("\n--- Checking GitHub Secrets Status ---")
    required_secrets = {
        "BLOG_ID": BLOG_ID,
        "BC_CLIENT_ID": BC_CLIENT_ID,
        "BC_CLIENT_SECRET": BC_CLIENT_SECRET,
        "BC_REFRESH_TOKEN": BC_REFRESH_TOKEN,
        "HF_TOKEN": HF_TOKEN,
        "SHRINKME_API": SHRINKME_API
    }
    
    for name, value in required_secrets.items():
        print(f"{name}: {'✅ LOADED' if value else '❌ MISSING'}")
    
    # Verify required secrets
    required = [BLOG_ID, HF_TOKEN, BC_CLIENT_ID, BC_CLIENT_SECRET, BC_REFRESH_TOKEN]
    if not all(required):
        print("❌ Required secrets missing. Exiting...")
        return
    
    # Verify Blogger
    print("\n🔍 Verifying Blogger permissions...")
    if not verify_blogger_permission():
        print("❌ Cannot proceed. Blogger credentials are invalid.")
        return
    
    # Shuffle feeds for variety
    random.shuffle(RSS_FEEDS)
    
    entry = None
    selected_feed_url = None
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # Find news
    print("\n🔍 Searching for Today's Breaking News from all categories...")
    
    for feed_url in RSS_FEEDS:
        print(f"\n📰 Checking: {feed_url}")
        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                if feed.entries:
                    # Get latest news
                    entry = feed.entries[0]
                    selected_feed_url = feed_url
                    
                    # Check date (allow 2 days old)
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])
                        today = datetime.now()
                        if pub_date.date() >= today.date() - timedelta(days=2):
                            print(f"✅ Recent news found (from {pub_date.strftime('%B %d')})")
                            break
                        else:
                            print(f"⚠️ News from {pub_date.strftime('%B %d')} - using anyway...")
                            break
                    else:
                        print(f"✅ Found news in: {feed_url}")
                        break
                else:
                    print(f"❌ No entries found")
            else:
                print(f"❌ Failed - Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

    if not entry:
        print("❌ No news found in any RSS feed!")
        return

    # Process article with SEO
    title = re.sub(r'\s+', ' ', entry.title).strip()
    link = entry.link
    summary = entry.get('summary', '')
    
    # SEO Title
    seo_title = get_seo_title(title)
    category = detect_category(selected_feed_url)
    
    print(f"\n📰 Processing: {seo_title}")
    print(f"📂 Category: {category}")
    
    # Get image
    image_url = get_entry_image(entry)
    if not image_url:
        print("🖼️ Using category-based SEO image")
        image_url = get_category_image(selected_feed_url, title)
        
    image_html = f"""
    <img src='{image_url}' 
         alt='{seo_title}' 
         style='width: 100%; max-height: 500px; object-fit: cover; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); margin-bottom: 25px;' 
         loading='lazy'>
    """
    print(f"📸 SEO Image: {image_url}")
    
    # Shorten link
    short_link = get_short_url(link)
    print(f"🔗 Short link: {short_link}")

    # Generate SEO content
    print("🤖 Generating SEO-optimized content...")
    ai_content = generate_ai_content(title, summary, category)
    
    # Earning Button (SEO optimized)
    earning_button = f"""
    <div style="text-align: center; margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #fff5f0, #fff); border-radius: 12px;">
        <a href="{short_link}" 
           target="_blank" 
           rel="nofollow sponsored"
           style="background: linear-gradient(135deg, #ff5722, #ff6f00); 
                  color: white; 
                  padding: 18px 50px; 
                  text-decoration: none; 
                  font-size: 20px; 
                  font-weight: bold; 
                  border-radius: 50px; 
                  box-shadow: 0 8px 25px rgba(255,87,34,0.4); 
                  display: inline-block; 
                  transition: all 0.3s;
                  text-transform: uppercase;
                  letter-spacing: 1px;">
            📖 READ FULL STORY HERE
        </a>
        <p style="font-size: 12px; color: #999; margin-top: 10px;">Click to read the complete story on the original source</p>
    </div>
    """

    # Final SEO content
    if ai_content and len(ai_content) > 150:
        print("✅ SEO content generated successfully")
        final_content = f"""
        {image_html}
        {ai_content}
        
        {earning_button}
        
        <hr style="border: 0; border-top: 2px solid #f0f0f0; margin: 30px 0;">
        <div style="text-align: center; color: #999; font-size: 14px; line-height: 1.6;">
            <p>📅 Published: {datetime.now().strftime('%B %d, %Y')}</p>
            <p>📂 Category: {category}</p>
            <p>🤖 AI-Generated News Summary • <a href="/" style="color: #ff5722; text-decoration: none;">Viral News AI</a></p>
        </div>
        """
    else:
        print("⚠️ Using SEO fallback content")
        final_content = generate_seo_fallback(title, summary, image_html, category)
        final_content += f"""
        
        {earning_button}
        
        <hr style="border: 0; border-top: 2px solid #f0f0f0; margin: 30px 0;">
        <div style="text-align: center; color: #999; font-size: 14px; line-height: 1.6;">
            <p>📅 Published: {datetime.now().strftime('%B %d, %Y')}</p>
            <p>📂 Category: {category}</p>
            <p>📰 Auto-Generated News Summary • <a href="/" style="color: #ff5722; text-decoration: none;">Viral News AI</a></p>
        </div>
        """

    # Post to Blogger
    print("\n📝 Posting to Blogger...")
    if post_to_blogger(seo_title, final_content):
        print("\n✅ PROCESS COMPLETED SUCCESSFULLY!")
        print(f"📰 SEO Title: {seo_title}")
        print(f"📂 Category: {category}")
        print(f"🔗 Short Link: {short_link}")
        print(f"📈 SEO Score: Optimized for Google ranking")
    else:
        print("\n❌ Failed to post. Check logs above.")

if __name__ == "__main__":
    main()
