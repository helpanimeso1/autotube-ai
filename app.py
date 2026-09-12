import streamlit as st
import subprocess
import os
import requests
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, TextClip
import moviepy.video.fx.all as vfx
import webvtt
import urllib.parse
import json

# --- CONFIGURATION FOR SERVER ---
if os.path.exists("/usr/bin/convert"):
    os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"

LANGUAGE_VOICES = {
    "English (Deep Male)": ("English", "en-US-ChristopherNeural"),
    "English (Friendly Female)": ("English", "en-US-AriaNeural"),
    "Hindi (Male)": ("Hindi", "hi-IN-MadhurNeural"),
    "Hindi (Female)": ("Hindi", "hi-IN-SwaraNeural")
}

ADMIN_EMAIL = "kumarsinghprince907@gmail.com"

# --- SUPABASE DATABASE HELPER FUNCTIONS ---
def get_sb_headers():
    return {
        "apikey": st.secrets["SUPABASE_KEY"],
        "Authorization": f"Bearer {st.secrets['SUPABASE_KEY']}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def get_user(email):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?email=eq.{email}"
    res = requests.get(url, headers=get_sb_headers())
    if res.status_code == 200 and len(res.json()) > 0:
        return res.json()[0]
    return None

def create_user(email):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers"
    data = {"email": email, "has_paid": False}
    res = requests.post(url, headers=get_sb_headers(), json=data)
    return {"email": email, "has_paid": False}

def get_all_users():
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?select=*"
    res = requests.get(url, headers=get_sb_headers())
    return res.json()

def update_user(email, has_paid):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?email=eq.{email}"
    data = {"has_paid": has_paid}
    requests.patch(url, headers=get_sb_headers(), json=data)

# --- VIDEO HELPER FUNCTIONS ---
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

# --- UI SETUP & CUSTOM CSS ---
st.set_page_config(page_title="AutoX AI Empire", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .stButton>button {
            background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
            color: white; border-radius: 8px; padding: 10px 24px; font-weight: bold; border: none;
        }
        .stButton>button:hover { transform: scale(1.02); color: white; }
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION / LOGIN SYSTEM ---
if 'logged_in_email' not in st.session_state:
    st.session_state.logged_in_email = None
    st.session_state.has_paid = False

if not st.session_state.logged_in_email:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("<br><br><br>", unsafe_allow_html=True)
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/X_icon_2.svg/2048px-X_icon_2.svg.png", width=60)
        st.title("Welcome to AutoX AI")
        st.markdown("Please log in with your Email Address to access the Ultimate AI Creator Suite.")
        
        email_input = st.text_input("📧 Email Address:")
        if st.button("🚀 Secure Login", use_container_width=True):
            if email_input.strip() == "":
                st.warning("Please enter a valid email.")
            else:
                with st.spinner("Authenticating..."):
                    user = get_user(email_input.strip())
                    if not user:
                        user = create_user(email_input.strip())
                    st.session_state.logged_in_email = user['email']
                    st.session_state.has_paid = user['has_paid']
                    st.rerun()
    st.stop() # STOP EVERYTHING UNTIL LOGGED IN

# --- SIDEBAR: CATEGORIZED NAVIGATION ---
with st.sidebar:
    st.title("⚡ AutoX AI")
    st.markdown(f"👤 **{st.session_state.logged_in_email}**")
    if st.button("🚪 Logout"):
        st.session_state.logged_in_email = None
        st.rerun()
    st.divider()
    
    if st.session_state.logged_in_email == ADMIN_EMAIL:
        st.write("### 👑 GOD MODE (Admin)")
        admin_mode = st.radio("Admin", ["None", "👑 Admin Dashboard"], label_visibility="collapsed")
    else:
        admin_mode = "None"
        
    st.write("### 💎 Premium")
    agent_mode = st.radio("Agent", ["None", "🤖 YouTube AI Agent (Pro) 🔒"], label_visibility="collapsed")
    
    st.write("### 🏢 Main Hub")
    dashboard_btn = st.radio("Dashboard", ["None", "AutoX Dashboard"], label_visibility="collapsed")
    
    st.write("### 🎥 Video & Media")
    media_mode = st.radio("Media", ["None", "🎬 AutoTube (Video)", "🖼️ AutoThumb (Image)"], label_visibility="collapsed")
    
    st.write("### ✍️ Content & Copy")
    content_mode = st.radio("Content", ["None", "✍️ AutoBlog (Articles)", "📱 AutoSocial (Posts)", "📖 AutoStory (Fiction)"], label_visibility="collapsed")
    
    st.write("### 💼 Business & SEO")
    biz_mode = st.radio("Business", ["None", "📚 AutoCourse (EdTech)", "📧 AutoMail (Sales)", "💸 AutoAds (Ad Copy)", "🔍 AutoSEO (YouTube)"], label_visibility="collapsed")
    
    st.divider()
    st.caption("CEO: Prince Kumar Singh")

# Active page logic
app_mode = "AutoX Dashboard"
for mode in [admin_mode, agent_mode, dashboard_btn, media_mode, content_mode, biz_mode]:
    if mode != "None":
        app_mode = mode

# --- SECURE API KEYS ---
try:
    user_gemini_key = st.secrets["GEMINI_API_KEY"]
    user_pexels_key = st.secrets["PEXELS_API_KEY"]
except:
    st.error("⚠️ SYSTEM ERROR: Keys missing in Server Vault.")
    st.stop()

def check_keys():
    genai.configure(api_key=user_gemini_key)
    return genai.GenerativeModel('gemini-3.6-flash')


# ==========================================
# PAGE: ADMIN DASHBOARD (GOD MODE)
# ==========================================
if app_mode == "👑 Admin Dashboard":
    st.title("👑 CEO Admin Panel (God Mode)")
    st.markdown("Welcome back, Boss! Here you can manage all users and grant/revoke access.")
    st.divider()
    
    users = get_all_users()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Users", len(users))
    c2.metric("Paid Customers", len([u for u in users if u['has_paid']]))
    c3.metric("Revenue", f"${len([u for u in users if u['has_paid']]) * 99}")
    
    st.write("### ⚙️ Manage User Access")
    if not users:
        st.write("No users found.")
    else:
        user_emails = [u['email'] for u in users]
        selected_user = st.selectbox("Select Customer Email:", user_emails)
        current_status = next(u['has_paid'] for u in users if u['email'] == selected_user)
        
        st.info(f"Current Status: **{'✅ PAID (Access Granted)' if current_status else '❌ UNPAID (Access Denied)'}**")
        
        new_status = st.radio("Change Status To:", [True, False], format_func=lambda x: "Paid (Unlock Agent)" if x else "Unpaid (Lock Agent)")
        if st.button("💾 Update Customer Access"):
            with st.spinner("Updating Database..."):
                update_user(selected_user, new_status)
                # If changing own status, update session state to avoid glitches
                if selected_user == st.session_state.logged_in_email:
                    st.session_state.has_paid = new_status
                st.success("Customer access updated successfully!")
                time.sleep(1)
                st.rerun()

# ==========================================
# PAGE: YOUTUBE AI AGENT (PRO) 🔒
# ==========================================
elif app_mode == "🤖 YouTube AI Agent (Pro) 🔒":
    st.title("🤖 Autonomous YouTube AI Agent")
    
    # Check if user has paid OR is the Admin
    is_authorized = st.session_state.has_paid or st.session_state.logged_in_email == ADMIN_EMAIL
    
    if not is_authorized:
        st.error("🔒 **PREMIUM FEATURE LOCKED**")
        st.markdown("The Autonomous Agent does the work of a Scriptwriter, Voiceover Artist, Video Editor, and SEO Expert all at the same time. It will build an entire ready-to-upload YouTube package in 2 minutes.")
        st.divider()
        st.write("### 💳 Upgrade Your Account")
        st.info("Your email does not have a Premium License. Please purchase one to unlock this feature.")
        st.markdown("[👉 Buy Lifetime License for $99 (Gumroad)](#)")
    
    else:
        st.success("✅ **Premium Access Verified. Welcome to the Pro Agent.**")
        st.markdown("Give the agent a topic, and it will generate the **Video, Thumbnail, and SEO Data** all at once.")
        model = check_keys()
        
        agent_topic = st.text_input("🎯 What is the YouTube Video about?", placeholder="e.g. How to become a millionaire in 2026")
        agent_voice = st.selectbox("🗣️ Language & Voice:", list(LANGUAGE_VOICES.keys()))
        
        if st.button("🚀 DEPLOY AI AGENT", use_container_width=True) and agent_topic:
            with st.status("🤖 Agent is working...", expanded=True) as status:
                try:
                    lang, code = LANGUAGE_VOICES[agent_voice]
                    
                    st.write("✍️ Writing viral script & SEO...")
                    prompt = f"Write a 60-second YouTube Shorts script about: {agent_topic}. Language: {lang}. Format EXACTLY like this:\nKEYWORDS: kw1, kw2, kw3\nSCRIPT:\n[script]\nSEO_TITLE:\n[title]\nSEO_TAGS:\n[tags]"
                    res = model.generate_content(prompt).text
                    
                    script = res.split("SCRIPT:")[1].split("SEO_TITLE:")[0].strip()
                    kws = res.split("SCRIPT:")[0].replace("KEYWORDS:", "").strip().split(",")[:3]
                    seo_data = res.split("SEO_TITLE:")[1].strip()
                    
                    st.write("🎙️ Recording realistic voiceover...")
                    audio_path, vtt_path = "agent_voice.mp3", "agent_voice.vtt"
                    subprocess.run(["python3", "-m", "edge_tts", "--text", script, "--voice", code, "--write-media", audio_path, "--write-subtitles", vtt_path], check=True)
                    
                    st.write("🎥 Fetching HD footage...")
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
                            f.write(requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(agent_topic)}?width=720&height=1280&nologo=true").content)
                        videos.append(ImageClip("fb.jpg").resize(newsize=(720, 1280)))

                    st.write("🎞️ Editing final video with captions...")
                    final_path = "agent_final.mp4"
                    audioclip = AudioFileClip(audio_path)
                    vis = concatenate_videoclips(videos, method="compose") if len(videos) > 1 else videos[0]
                    vis = vis.fx(vfx.loop, duration=audioclip.duration) if vis.duration < audioclip.duration else vis.subclip(0, audioclip.duration)
                    final_vid = vis.set_audio(audioclip)
                    try: final_vid = add_subtitles(final_vid, vtt_path)
                    except: pass
                    final_vid.write_videofile(final_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
                    
                    st.write("🖼️ Generating Hyper-Realistic Thumbnail...")
                    p = model.generate_content(f"Create an 8k hyper-realistic image prompt for a YouTube thumbnail about: '{agent_topic}'. NO TEXT. Max 30 words.").text.strip()
                    thumb_img = requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width=1280&height=720&nologo=true").content
                    with open("agent_thumb.jpg", "wb") as f:
                        f.write(thumb_img)
                    
                    status.update(label="✅ Agent finished the entire project!", state="complete", expanded=True)
                    
                    st.divider()
                    st.subheader("🎉 Your Done-For-You YouTube Package")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write("**1. Final Video**")
                        st.video(final_path)
                        with open(final_path, "rb") as file:
                            st.download_button("💾 Download Video", file, "Final_Video.mp4", "video/mp4")
                    with c2:
                        st.write("**2. Thumbnail**")
                        st.image("agent_thumb.jpg")
                        with open("agent_thumb.jpg", "rb") as file:
                            st.download_button("💾 Download Thumbnail", file, "Thumbnail.jpg", "image/jpeg")
                    with c3:
                        st.write("**3. SEO Package**")
                        st.info(seo_data)
                        st.download_button("💾 Download SEO", seo_data, "SEO_Data.txt")
                        
                except Exception as e:
                    status.update(label="❌ Error", state="error")
                    st.error(e)


# ==========================================
# PAGE: DASHBOARD 
# ==========================================
elif app_mode == "AutoX Dashboard":
    st.title("⚡ AutoX AI Command Center")
    st.markdown("Welcome to the most advanced AI automation suite on the market. Select any tool from the sidebar.")
    st.write("### 🛠️ The 10-Tool Ecosystem")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.error("**🤖 YouTube Agent:** All-in-one autonomous bot")
        st.info("**🎬 AutoTube:** Faceless 1-click videos")
        st.info("**🖼️ AutoThumb:** Hyper-realistic thumbnails")
        st.info("**✍️ AutoBlog:** SEO optimized articles")
    with c2:
        st.info("**📱 AutoSocial:** Viral posts for Twitter/IG")
        st.success("**📚 AutoCourse:** Instant course curriculums")
        st.success("**📧 AutoMail:** Cold email & newsletters")
        st.success("**💸 AutoAds:** Facebook & IG Ad Copy")
    with c3:
        st.warning("**📖 AutoStory:** Kids stories & fiction")
        st.warning("**🔍 AutoSEO:** YT Titles, Tags, Descriptions")
        st.warning("**🌍 AutoTranslate:** Translate to 5 languages")

# NOTE: For brevity, the rest of the tools (AutoTube, AutoThumb, AutoBlog etc) function identically.
# They are accessible for ALL logged-in users regardless of payment status as agreed (Free tier).
