import streamlit as st
import subprocess
import os
import requests
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, TextClip
import moviepy.video.fx.all as vfx
import webvtt
import urllib.parse

# --- CONFIGURATION FOR SERVER ---
if os.path.exists("/usr/bin/convert"):
    os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"

LANGUAGE_VOICES = {
    "English (Deep Male)": ("English", "en-US-ChristopherNeural"),
    "English (Friendly Female)": ("English", "en-US-AriaNeural"),
    "Hindi (Male)": ("Hindi", "hi-IN-MadhurNeural"),
    "Hindi (Female)": ("Hindi", "hi-IN-SwaraNeural"),
    "Spanish (Male)": ("Spanish", "es-ES-AlvaroNeural")
}

def time_to_seconds(t_str):
    h, m, s = t_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def add_subtitles(video_clip, vtt_file):
    if not os.path.exists(vtt_file):
        return video_clip
    subs = webvtt.read(vtt_file)
    subtitle_clips = []
    for sub in subs:
        start_time = time_to_seconds(sub.start)
        end_time = time_to_seconds(sub.end)
        txt_clip = TextClip(sub.text.upper(), fontsize=70, color='yellow', font='Arial-Bold',
                            stroke_color='black', stroke_width=4, method='caption', size=(video_clip.w - 100, None))
        txt_clip = txt_clip.set_position(('center', 'center')).set_start(start_time).set_end(end_time)
        subtitle_clips.append(txt_clip)
    return CompositeVideoClip([video_clip] + subtitle_clips)

# --- UI SETUP & CUSTOM CSS (PROFESSIONAL LOOK) ---
st.set_page_config(page_title="AutoX AI Suite", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        /* Hide Streamlit default marks */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Modern Button Styling */
        .stButton>button {
            background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
            color: white;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
            border: none;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            color: white;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            font-weight: bold;
            color: #4F46E5;
        }
        
        /* Text headers */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            color: #1F2937;
        }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CATEGORIZED NAVIGATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/X_icon_2.svg/2048px-X_icon_2.svg.png", width=50)
    st.title("AutoX AI")
    st.caption("The Ultimate Automation Empire")
    st.divider()
    
    st.write("### 🏢 Main")
    dashboard_btn = st.radio("Dashboard", ["AutoX Hub"], label_visibility="collapsed")
    
    st.write("### 🎥 Video & Media")
    media_mode = st.radio("Media", ["None", "🎬 AutoTube (Video)", "🖼️ AutoThumb (Image)"], label_visibility="collapsed")
    
    st.write("### ✍️ Content & Copy")
    content_mode = st.radio("Content", ["None", "✍️ AutoBlog (Articles)", "📱 AutoSocial (Posts)", "📖 AutoStory (Fiction)"], label_visibility="collapsed")
    
    st.write("### 💼 Business & Marketing")
    biz_mode = st.radio("Business", ["None", "📚 AutoCourse (EdTech)", "📧 AutoMail (Sales)", "💸 AutoAds (Ad Copy)"], label_visibility="collapsed")
    
    st.write("### 🚀 Growth & Reach")
    growth_mode = st.radio("Growth", ["None", "🔍 AutoSEO (YouTube)", "🌍 AutoTranslate (Global)"], label_visibility="collapsed")
    
    st.divider()
    st.caption("v3.0 Pro | Created by Prince Kumar Singh")

# Determine active app mode based on radio buttons
app_mode = "AutoX Hub"
for mode in [media_mode, content_mode, biz_mode, growth_mode]:
    if mode != "None":
        app_mode = mode

# --- SECURE API KEYS ---
try:
    user_gemini_key = st.secrets["GEMINI_API_KEY"]
    user_pexels_key = st.secrets["PEXELS_API_KEY"]
except:
    user_gemini_key = None
    user_pexels_key = None

def check_keys():
    if not user_gemini_key:
        st.error("⚠️ SYSTEM ERROR: CEO has not configured API keys in the Server Vault.")
        st.stop()
    genai.configure(api_key=user_gemini_key)
    return genai.GenerativeModel('gemini-3.6-flash')


# ==========================================
# PAGE: DASHBOARD
# ==========================================
if app_mode == "AutoX Hub":
    st.title("⚡ AutoX AI Command Center")
    st.markdown("Welcome to the most advanced AI automation suite on the market. Select any tool from the sidebar to multiply your productivity by 100x.")
    
    st.write("### 📊 Platform Analytics (Simulation)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tools Available", "10", "+5 New")
    m2.metric("API Status", "Online", "Operational")
    m3.metric("System Latency", "12ms", "-2ms")
    m4.metric("License", "Pro Lifetime", "Active")
    
    st.divider()
    st.write("### 🛠️ The 10-Tool Ecosystem")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**🎬 AutoTube:** Faceless 1-click videos")
        st.info("**🖼️ AutoThumb:** Hyper-realistic thumbnails")
        st.info("**✍️ AutoBlog:** SEO optimized articles")
        st.info("**📱 AutoSocial:** Viral posts for Twitter/IG")
    with c2:
        st.success("**📚 AutoCourse:** Instant course curriculums")
        st.success("**📧 AutoMail:** Cold email & newsletters")
        st.success("**💸 AutoAds:** Facebook & IG Ad Copy")
        st.success("**📖 AutoStory:** Kids stories & fiction")
    with c3:
        st.warning("**🔍 AutoSEO:** YT Titles, Tags, Descriptions")
        st.warning("**🌍 AutoTranslate:** Translate to 5 languages")
        st.warning("**🎙️ AutoPod (Coming Soon):** Podcast scripts")
        st.warning("**📊 AutoDeck (Coming Soon):** Pitch Decks")

# ==========================================
# PAGE: AUTOTUBE (VIDEO)
# ==========================================
elif app_mode == "🎬 AutoTube (Video)":
    st.title("🎬 AutoTube AI - Viral Faceless Generator")
    model = check_keys()
    
    c1, c2 = st.columns([1,2])
    with c1:
        st.write("### Settings")
        topic = st.text_input("🎯 Video Topic:")
        voice = st.selectbox("🌍 Voice Model:", list(LANGUAGE_VOICES.keys()))
        captions = st.checkbox("📝 Burn Subtitles", value=True)
        generate_btn = st.button("🚀 Generate Video", use_container_width=True)
        
    with c2:
        st.write("### Output Engine")
        if generate_btn and topic:
            with st.spinner("Processing AI Pipeline..."):
                try:
                    lang, code = LANGUAGE_VOICES[voice]
                    prompt = f"Write a fast-paced 60-second YouTube Shorts script about: {topic}. Language: {lang}. Format EXACTLY like this:\nKEYWORDS: keyword1, keyword2, keyword3\nSCRIPT:\n[script]"
                    res = model.generate_content(prompt).text
                    try:
                        kws = res.split("SCRIPT:")[0].replace("KEYWORDS:", "").strip().split(",")[:3]
                        script = res.split("SCRIPT:")[1].strip()
                    except:
                        script, kws = res, [topic.split()[0]]
                    
                    st.download_button("💾 Download Script", script, "script.txt")
                    
                    audio_path, vtt_path = "auto_voice.mp3", "auto_voice.vtt"
                    subprocess.run(["python3", "-m", "edge_tts", "--text", script, "--voice", code, "--write-media", audio_path, "--write-subtitles", vtt_path], check=True)
                    st.audio(audio_path)
                    
                    videos = []
                    headers = {"Authorization": user_pexels_key}
                    for kw in kws:
                        r = requests.get(f"https://api.pexels.com/videos/search?query={kw.strip()}&per_page=1&orientation=portrait&size=medium", headers=headers).json()
                        vdata = r.get('videos', [])
                        if vdata and vdata[0].get('video_files'):
                            with open(f"v_{kw}.mp4", 'wb') as f:
                                f.write(requests.get(vdata[0]['video_files'][0]['link']).content)
                            videos.append(VideoFileClip(f"v_{kw}.mp4").resize(newsize=(720, 1280)))
                    
                    if not videos:
                        with open("fb.jpg", 'wb') as f:
                            f.write(requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(topic)}?width=720&height=1280&nologo=true").content)
                        videos.append(ImageClip("fb.jpg").resize(newsize=(720, 1280)))

                    final_path = "final.mp4"
                    audioclip = AudioFileClip(audio_path)
                    vis = concatenate_videoclips(videos, method="compose") if len(videos) > 1 else videos[0]
                    vis = vis.fx(vfx.loop, duration=audioclip.duration) if vis.duration < audioclip.duration else vis.subclip(0, audioclip.duration)
                    final_vid = vis.set_audio(audioclip)
                    
                    if captions:
                        try: final_vid = add_subtitles(final_vid, vtt_path)
                        except: pass
                        
                    final_vid.write_videofile(final_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
                    st.video(final_path)
                    with open(final_path, "rb") as file:
                        st.download_button("💾 Download Master Video", data=file, file_name="AutoTube.mp4", mime="video/mp4", use_container_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")

# ==========================================
# PAGE: AUTOTHUMB
# ==========================================
elif app_mode == "🖼️ AutoThumb (Image)":
    st.title("🖼️ AutoThumb AI - Hyper-Realistic Studio")
    model = check_keys()
    topic = st.text_input("🎯 Video Topic:")
    style = st.selectbox("🎨 Style:", ["Hyper-Realistic Photography", "Cinematic Dark", "MrBeast Bright"])
    
    if st.button("🚀 Render HD Thumbnail") and topic:
        with st.spinner("Rendering 8k AI Matrix..."):
            try:
                p = model.generate_content(f"Create a highly detailed image prompt for a YouTube thumbnail about: '{topic}'. Style: {style}. Hyper-realistic, 8k, DSLR. NO TEXT OR WORDS. Max 40 words.").text.strip()
                img = requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width=1280&height=720&nologo=true").content
                st.image(img, caption=f"Prompt: {p}")
                st.download_button("💾 Download Thumbnail", img, "thumb.jpg", "image/jpeg")
            except Exception as e: st.error(e)

# ==========================================
# PAGE: AUTOBLOG
# ==========================================
elif app_mode == "✍️ AutoBlog (Articles)":
    st.title("✍️ AutoBlog AI - SEO Engine")
    model = check_keys()
    topic = st.text_input("📝 Blog Topic:")
    if st.button("🚀 Write 1000-Word Article") and topic:
        with st.spinner("Writing..."):
            res = model.generate_content(f"Write a 1000-word highly engaging SEO blog about '{topic}'. Include H1, H2, bullet points. Markdown format.").text
            st.markdown(res)
            st.download_button("💾 Download Blog", res, "blog.txt")

# ==========================================
# PAGE: AUTOSOCIAL
# ==========================================
elif app_mode == "📱 AutoSocial (Posts)":
    st.title("📱 AutoSocial AI - Viral Posts")
    model = check_check_keys = check_keys()
    topic = st.text_input("💡 Post Topic:")
    plat = st.selectbox("🎯 Platform:", ["Twitter Thread", "LinkedIn", "Instagram Reel Caption"])
    if st.button("🚀 Generate Post") and topic:
        with st.spinner("Writing..."):
            res = model.generate_content(f"Write a viral {plat} about '{topic}'. Add emojis and hashtags.").text
            st.info(res)
            st.download_button("💾 Download Post", res, "post.txt")

# ==========================================
# PAGE: AUTOSTORY
# ==========================================
elif app_mode == "📖 AutoStory (Fiction)":
    st.title("📖 AutoStory AI - Fiction & Kids")
    model = check_keys()
    topic = st.text_input("🐉 Story Idea:")
    if st.button("🚀 Write Story") and topic:
        with st.spinner("Writing..."):
            res = model.generate_content(f"Write a captivating short story about '{topic}'. Include rich descriptions and a great ending.").text
            st.write(res)
            st.download_button("💾 Download Story", res, "story.txt")

# ==========================================
# PAGE: AUTOCOURSE
# ==========================================
elif app_mode == "📚 AutoCourse (EdTech)":
    st.title("📚 AutoCourse AI - Curriculum Builder")
    model = check_keys()
    topic = st.text_input("🎓 Course Subject:")
    if st.button("🚀 Generate Course Curriculum") and topic:
        with st.spinner("Structuring modules..."):
            res = model.generate_content(f"Act as a master course creator. Build a premium 5-module course curriculum about '{topic}'. Include lesson titles and brief descriptions for each.").text
            st.write(res)
            st.download_button("💾 Download Curriculum", res, "course.txt")

# ==========================================
# PAGE: AUTOMAIL
# ==========================================
elif app_mode == "📧 AutoMail (Sales)":
    st.title("📧 AutoMail AI - Cold Outreach")
    model = check_keys()
    topic = st.text_input("✉️ Product/Offer:")
    if st.button("🚀 Write Sales Sequence") and topic:
        with st.spinner("Writing emails..."):
            res = model.generate_content(f"Write a high-converting 3-part cold email sequence to sell '{topic}'. Include subject lines.").text
            st.write(res)
            st.download_button("💾 Download Emails", res, "emails.txt")

# ==========================================
# PAGE: AUTOADS
# ==========================================
elif app_mode == "💸 AutoAds (Ad Copy)":
    st.title("💸 AutoAds AI - Facebook/IG Ads")
    model = check_keys()
    topic = st.text_input("🎯 Product to advertise:")
    if st.button("🚀 Generate Ad Copy") and topic:
        with st.spinner("Writing ads..."):
            res = model.generate_content(f"Write 3 variations of viral Facebook/Instagram Ad copy for '{topic}'. Include Hook, Body, and Call to Action. Use emojis.").text
            st.write(res)
            st.download_button("💾 Download Ads", res, "ads.txt")

# ==========================================
# PAGE: AUTOSEO
# ==========================================
elif app_mode == "🔍 AutoSEO (YouTube)":
    st.title("🔍 AutoSEO AI - Rank #1")
    model = check_keys()
    topic = st.text_input("🔍 YouTube Video Topic:")
    if st.button("🚀 Generate SEO Strategy") and topic:
        with st.spinner("Analyzing..."):
            res = model.generate_content(f"Act as a YouTube SEO Expert. For '{topic}', give: 1. Top 5 clickbait titles. 2. SEO Description. 3. 30 comma-separated Tags.").text
            st.write(res)
            st.download_button("💾 Download SEO", res, "seo.txt")

# ==========================================
# PAGE: AUTOTRANSLATE
# ==========================================
elif app_mode == "🌍 AutoTranslate (Global)":
    st.title("🌍 AutoTranslate AI")
    model = check_keys()
    text = st.text_area("📝 Text to translate:")
    if st.button("🚀 Translate to 5 Languages") and text:
        with st.spinner("Translating..."):
            res = model.generate_content(f"Translate the following text into Spanish, French, German, Hindi, and Japanese. Format clearly.\n\nText: {text}").text
            st.write(res)
            st.download_button("💾 Download Translations", res, "translations.txt")
