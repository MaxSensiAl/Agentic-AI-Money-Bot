import os
import requests
import google.generativeai as genai

# GitHub Secrets से डेटा उठाना
SHRINKME_KEY = os.getenv("SHRINKME_API")
GEMINI_KEY = os.getenv("GEMINI_API")
BLOGGER_KEY = os.getenv("BLOGGER_API")
BLOG_ID = os.getenv("BLOG_ID")

def get_viral_content():
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-pro')
        prompt = "Find a real trending movie or tech news from the last 24 hours. Provide: 1) Title, 2) Image URL, 3) 3-line viral summary. Format it clearly."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None

def create_cyber_html(title, desc, img, link):
    return f"""
    <div style="background:#050505; color:white; padding:20px; border:2px solid #00f2ff; border-radius:15px; text-align:center; font-family:sans-serif;">
        <h1 style="color:#00f2ff; font-family:Orbitron, sans-serif;">{title}</h1>
        <img src="{img}" style="width:100%; border-radius:10px; border:1px solid #7000ff; box-shadow:0 0 15px #00f2ff;">
        <p style="color:#ccc; margin-top:15px;">{desc}</p>
        <div style="margin-top:30px;">
            <a href="{link}" style="background:linear-gradient(45deg, #7000ff, #00f2ff); color:white; padding:15px 40px; text-decoration:none; border-radius:50px; font-weight:bold; box-shadow:0 0 20px #7000ff;">INITIALIZE DOWNLOAD</a>
        </div>
        <p style="font-size:10px; color:#555; margin-top:20px;">ENCRYPTED DATA BY AGENTIC AI</p>
    </div>
    """

def post_to_blogger(title, html_content):
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
    payload = {
        "kind": "blogger#post",
        "title": title,
        "content": html_content
    }
    params = {'key': BLOGGER_KEY}
    r = requests.post(url, params=params, json=payload)
    if r.status_code == 200:
        return r.json()['url']
    else:
        print(f"Blogger Error: {r.text}")
        return None

if __name__ == "__main__":
    content = get_viral_content()
    if content:
        # यहाँ हम ब्लॉग का लिंक ही ShrinkMe से छोटा कर रहे हैं ताकि आपको पैसे मिलें
        # आप यहाँ किसी मूवी का असली डाउनलोड लिंक भी डाल सकते हैं
        original_link = "https://viralnewsai24.blogspot.com" 
        
        shrink_url = f"https://shrinkme.io/api?api={SHRINKME_KEY}&url={original_link}"
        money_link = requests.get(shrink_url).json().get("shortenedUrl", original_link)
        
        final_html = create_cyber_html("AI Trending Update", content, "https://via.placeholder.com/800x400", money_link)
        result = post_to_blogger("New Viral Update Found by AI", final_html)
        
        if result:
            print(f"🚀 Success! Money Link Created: {money_link}")
