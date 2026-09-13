import streamlit as st
import subprocess
import os
import requests
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, TextClip
import moviepy.video.fx.all as vfx
import webvtt
import urllib.parse
import smtplib
from email.mime.text import MIMEText
import random
import time
import re
import string
from PIL import Image

# --- CONFIGURATION ---
if os.path.exists("/usr/bin/convert"):
    os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"

LANGUAGE_VOICES = {
    "English (Deep Male)": ("English", "en-US-ChristopherNeural"),
    "English (Friendly Female)": ("English", "en-US-AriaNeural"),
    "Hindi (Male)": ("Hindi", "hi-IN-MadhurNeural"),
    "Hindi (Female)": ("Hindi", "hi-IN-SwaraNeural"),
    "Spanish (Male)": ("Spanish", "es-ES-AlvaroNeural"),
    "Spanish (Female)": ("Spanish", "es-ES-ElviraNeural"),
    "French (Male)": ("French", "fr-FR-HenriNeural"),
    "French (Female)": ("French", "fr-FR-DeniseNeural"),
    "German (Male)": ("German", "de-DE-ConradNeural"),
    "Japanese (Female)": ("Japanese", "ja-JP-NanamiNeural"),
    "Arabic (Male)": ("Arabic", "ar-SA-HamedNeural")
}
ADMIN_EMAIL = "helpanimeso1@gmail.com"

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

def create_user(email, password):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers"
    clean_email = email.split('@')[0][:4].upper()
    random_str = ''.join(random.choices(string.digits, k=4))
    ref_code = f"AUTOX-{clean_email}-{random_str}"
    
    data = {
        "email": email, 
        "password": password, 
        "has_paid": False, 
        "videos_left": 1,
        "referral_code": ref_code,
        "yt_pro": False,
        "insta_pro": False,
        "referral_count": 0
    }
    requests.post(url, headers=get_sb_headers(), json=data)
    return data

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

def update_videos_left(email, new_count):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?email=eq.{email}"
    data = {"videos_left": new_count}
    requests.patch(url, headers=get_sb_headers(), json=data)

def get_user_by_referral(ref_code):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?referral_code=eq.{ref_code}"
    res = requests.get(url, headers=get_sb_headers())
    if res.status_code == 200 and len(res.json()) > 0:
        return res.json()[0]
    return None

def add_referral_bonus(my_email, friend_email, my_current_credits, friend_current_credits, friend_current_ref_count):
    # Give both +1 credit, and increase friend's referral count
    update_videos_left(my_email, my_current_credits + 1)
    
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?email=eq.{friend_email}"
    data = {
        "videos_left": friend_current_credits + 1,
        "referral_count": friend_current_ref_count + 1
    }
    requests.patch(url, headers=get_sb_headers(), json=data)


# --- UI SETUP & MODERN CSS ---
st.set_page_config(page_title="AutoX - AI Engine", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        /* Ultra Modern Colorful SaaS Theme */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&display=swap');
        .stApp {
            background-color: #0d0e15 !important;
            color: #ffffff !important;
            font-family: 'Outfit', sans-serif;
        }
        h1, h2, h3 { color: #ffffff !important; font-weight: 900; }
        
        .gradient-text {
            background: linear-gradient(90deg, #ff007f, #7928ca, #00d4ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
        }
        
        .yt-text { color: #FF0000; font-weight: 900; }
        .insta-text { 
            background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
        }
        
        /* Modern Cards */
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            transition: transform 0.3s ease;
        }
        .glass-card:hover { transform: translateY(-5px); border-color: #7928ca; }
        
        /* Premium Buttons */
        .stButton>button {
            background: linear-gradient(90deg, #7928ca 0%, #ff007f 100%) !important;
            color: #FFFFFF !important;
            border: none;
            border-radius: 30px;
            font-weight: 700;
            padding: 15px 30px;
        }
        
        /* Inputs */
        .stTextInput input { background: #1a1c29 !important; color: white !important; border: 1px solid #333 !important; border-radius: 10px; }
        
        /* Footer */
        .footer { text-align: center; margin-top: 50px; padding: 30px; border-top: 1px solid #333; color: #888; }
        .footer a { color: #00d4ff; text-decoration: none; margin: 0 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)


# --- STATE MANAGEMENT ---
if 'logged_in_email' not in st.session_state:
    st.session_state.logged_in_email = None

# --- REFRESH USER DATA ---
current_user = None
if st.session_state.logged_in_email:
    current_user = get_user(st.session_state.logged_in_email)


# --- SECURE API KEYS ---
try:
    user_gemini_key = st.secrets["GEMINI_API_KEY"]
    user_pexels_key = st.secrets["PEXELS_API_KEY"]
except:
    pass

def check_keys():
    genai.configure(api_key=user_gemini_key)
    return genai.GenerativeModel('gemini-3.6-flash')


# --- CORE VIDEO GENERATION ENGINE ---
def add_subtitles(video_clip, vtt_file, width, height):
    if not os.path.exists(vtt_file):
        return video_clip
    subs = webvtt.read(vtt_file)
    subtitle_clips = []
    for sub in subs:
        h, m, s = sub.start.split(':')
        start_time = int(h) * 3600 + int(m) * 60 + float(s)
        h, m, s = sub.end.split(':')
        end_time = int(h) * 3600 + int(m) * 60 + float(s)
        
        txt_clip = TextClip(sub.text.upper(), fontsize=int(width/15), color='white', font='Arial-Bold',
                            stroke_color='black', stroke_width=3, method='caption', size=(width - 100, None))
        txt_clip = txt_clip.set_position(('center', 'center')).set_start(start_time).set_end(end_time)
        subtitle_clips.append(txt_clip)
    return CompositeVideoClip([video_clip] + subtitle_clips)

def run_video_agent(agent_topic, is_landscape, agent_voice):
    model = check_keys()
    width, height = (1280, 720) if is_landscape else (720, 1280)
    orientation = "landscape" if is_landscape else "portrait"
    agent_format = "YouTube Standard (16:9)" if is_landscape else "Instagram Reels (9:16)"
    
    with st.status("🤖 AutoX AI is crafting your masterpiece...", expanded=True) as status:
        try:
            lang, code = LANGUAGE_VOICES[agent_voice]
            st.write("✍️ Writing script & SEO...")
            prompt = f"Write a 60-second viral video script about: {agent_topic}. Format: {agent_format}. Language: {lang}. Format EXACTLY like this:\nKEYWORDS: kw1, kw2, kw3\nSCRIPT:\n[script]\nSEO_TITLE:\n[title]\nSEO_TAGS:\n[tags]"
            res = model.generate_content(prompt).text
            
            script = res.split("SCRIPT:")[1].split("SEO_TITLE:")[0].strip()
            kws = res.split("SCRIPT:")[0].replace("KEYWORDS:", "").strip().split(",")[:3]
            seo_data = res.split("SEO_TITLE:")[1].strip()
            
            st.write("🎙️ Synthesizing Voice Actor...")
            audio_path, vtt_path = "agent_voice.mp3", "agent_voice.vtt"
            subprocess.run(["python3", "-m", "edge_tts", "--text", script, "--voice", code, "--write-media", audio_path, "--write-subtitles", vtt_path], check=True)
            
            st.write("🎥 Fetching Cinematic Footage...")
            videos = []
            headers = {"Authorization": user_pexels_key}
            for kw in kws:
                r = requests.get(f"https://api.pexels.com/videos/search?query={kw.strip()}&per_page=1&orientation={orientation}&size=medium", headers=headers).json()
                vdata = r.get('videos', [])
                if vdata and vdata[0].get('video_files'):
                    with open(f"v_{kw}.mp4", 'wb') as f:
                        f.write(requests.get(vdata[0]['video_files'][0]['link']).content)
                    
                    clip = VideoFileClip(f"v_{kw}.mp4").resize(newsize=(width, height))
                    if len(videos) > 0:
                        clip = clip.crossfadein(0.5)
                    videos.append(clip)
            
            if not videos:
                with open("fb.jpg", 'wb') as f:
                    f.write(requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(agent_topic)}?width={width}&height={height}&nologo=true").content)
                videos.append(ImageClip("fb.jpg").resize(newsize=(width, height)).set_duration(5))

            st.write("🎞️ Rendering Advanced Timeline (Transitions & Subtitles)...")
            final_path = "agent_final.mp4"
            audioclip = AudioFileClip(audio_path)
            
            if len(videos) > 1:
                vis = concatenate_videoclips(videos, padding=-0.5, method="compose")
            else:
                vis = videos[0]
                
            vis = vis.fx(vfx.loop, duration=audioclip.duration) if vis.duration < audioclip.duration else vis.subclip(0, audioclip.duration)
            final_vid = vis.set_audio(audioclip)
            
            try: 
                final_vid = add_subtitles(final_vid, vtt_path, width, height)
            except: 
                pass
            
            final_vid.write_videofile(final_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
            
            st.write("🖼️ Generating 8K Thumbnail...")
            p = model.generate_content(f"Create an 8k hyper-realistic image prompt for a video thumbnail about: '{agent_topic}'. NO TEXT. Max 30 words.").text.strip()
            thumb_img = requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width=1280&height=720&nologo=true").content
            with open("agent_thumb.jpg", "wb") as f:
                f.write(thumb_img)
            
            status.update(label="✅ Render Complete!", state="complete", expanded=True)
            
            st.divider()
            st.subheader("🎉 Your Video is Ready")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.video(final_path)
                with open(final_path, "rb") as file:
                    st.download_button("💾 Download Video", file, "Final_Video.mp4", "video/mp4")
                if st.button("🚀 Publish (Beta)"):
                    st.info("ℹ️ **Beta Feature:** We are currently awaiting API approval from Google & Meta. Please upload manually for now.")
            with c2:
                st.image("agent_thumb.jpg")
                with open("agent_thumb.jpg", "rb") as file:
                    st.download_button("💾 Download Thumbnail", file, "Thumbnail.jpg", "image/jpeg")
            with c3:
                st.info(seo_data)
                st.download_button("💾 Download SEO", seo_data, "SEO_Data.txt")
                
        except Exception as e:
            status.update(label="❌ Render Failed", state="error")
            st.error(f"Error Details: {str(e)}")


# ==========================================
# PAGE 1: PROFESSIONAL LANDING PAGE (NOT LOGGED IN)
# ==========================================
if not st.session_state.logged_in_email:
    c_logo, c_login = st.columns([4, 1])
    with c_logo:
        st.markdown("<h3>⚡ <span class='gradient-text'>AutoX</span></h3>", unsafe_allow_html=True)
    with c_login:
        with st.popover("Login / Sign Up", use_container_width=True):
            st.write("#### Secure Access")
            email_input = st.text_input("Email")
            pwd_input = st.text_input("Password", type="password")
            if st.button("Enter Platform", use_container_width=True):
                if is_valid_email(email_input) and len(pwd_input) >= 4:
                    user_data = get_user(email_input.strip())
                    if not user_data:
                        create_user(email_input.strip(), pwd_input)
                        st.session_state.logged_in_email = email_input.strip()
                        st.rerun()
                    else:
                        if pwd_input == user_data['password']:
                            st.session_state.logged_in_email = email_input.strip()
                            st.rerun()
                        else:
                            st.error("Wrong password!")
                else:
                    st.error("Invalid email or short password")

    st.write("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        st.markdown("<h1 style='text-align: center; font-size: 60px;'>The Ultimate <span class='gradient-text'>AI Workforce</span> for Creators</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 20px; color: #aaa;'>Automate your YouTube and Instagram channels entirely with AI. Zero editing skills required.</p>", unsafe_allow_html=True)
        try:
            logo_path = "/Users/princekumarsingh/.gemini/antigravity/brain/14257aba-a9b6-466d-94bd-670877ef98ec/autox_logo_1789214937891.jpg"
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                st.image(img, use_container_width=True)
        except:
            pass

    st.write("<br><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>How It Works</h2><br>", unsafe_allow_html=True)
    colA, colB = st.columns(2)
    with colA:
        st.markdown("<div class='glass-card'><h3 class='yt-text'>YouTube AutoX (PRO)</h3><p>Generates long-form 16:9 cinematic videos with AI voiceovers, subtitles, and smooth transitions.</p></div>", unsafe_allow_html=True)
        try:
            st.image(Image.open("/Users/princekumarsingh/.gemini/antigravity/brain/14257aba-a9b6-466d-94bd-670877ef98ec/yt_demo_mockup_1789319335368.jpg"), use_container_width=True)
        except: pass
    with colB:
        st.markdown("<div class='glass-card'><h3 class='insta-text'>Instagram AutoX (PRO)</h3><p>Creates viral 9:16 Reels with trendy captions, fast pacing, and engaging hooks designed for the algorithm.</p></div>", unsafe_allow_html=True)
        try:
            st.image(Image.open("/Users/princekumarsingh/.gemini/antigravity/brain/14257aba-a9b6-466d-94bd-670877ef98ec/insta_demo_mockup_1789319351037.jpg"), use_container_width=True)
        except: pass

    st.markdown("""
        <div class='footer'>
            <p>AutoX AI Inc. © 2026 | All Data Secured</p>
            <a href='https://youtube.com/@autox' target='_blank'>Official YouTube</a> | 
            <a href='https://instagram.com/autox' target='_blank'>Official Instagram</a> |
            <a href='#'>Privacy Policy</a>
        </div>
    """, unsafe_allow_html=True)
    st.stop()


# ==========================================
# PAGE 2: LOGGED IN DASHBOARD
# ==========================================

# Access controls
yt_pro_active = current_user.get('yt_pro', False) if current_user else False
insta_pro_active = current_user.get('insta_pro', False) if current_user else False
v_left = current_user.get('videos_left', 0) if current_user else 0
is_admin = (st.session_state.logged_in_email == ADMIN_EMAIL)
if is_admin:
    yt_pro_active, insta_pro_active = True, True

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("<h2>⚡ <span class='gradient-text'>AutoX</span></h2>", unsafe_allow_html=True)
st.sidebar.divider()
app_mode = st.sidebar.radio("Navigation", ["🏠 Main Hub", "🎥 YouTube AutoX", "📱 Instagram AutoX"], label_visibility="collapsed")
st.sidebar.divider()

with st.sidebar.expander("⚙️ Account & Settings (•••)"):
    settings_mode = st.radio("Options", ["👤 My Profile", "💳 Payment History", "🎁 Refer & Earn", "🚪 Logout"], label_visibility="collapsed")
    if settings_mode == "🚪 Logout":
        st.session_state.logged_in_email = None
        st.rerun()
    elif settings_mode != "👤 My Profile": 
        app_mode = settings_mode
        
if settings_mode == "👤 My Profile":
    app_mode = "👤 My Profile"

st.sidebar.markdown("""
<div style='margin-top: 50px; text-align: center;'>
    <a href='https://youtube.com/@autox' target='_blank' style='color:#00d4ff; text-decoration:none;'>📺 YouTube</a><br>
    <a href='https://instagram.com/autox' target='_blank' style='color:#00d4ff; text-decoration:none;'>📸 Instagram</a>
</div>
""", unsafe_allow_html=True)


# ----------------------------------------
# 🏠 MAIN HUB
# ----------------------------------------
if app_mode == "🏠 Main Hub":
    st.title("Welcome to your AI Workspace")
    st.markdown("Select an engine from the sidebar to start generating.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='glass-card'><h3 class='yt-text'>YouTube AutoX</h3><p>Status: {'<span style="color:green;">✅ PRO ACTIVE</span>' if yt_pro_active else '<span style="color:red;">❌ INACTIVE</span>'}</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='glass-card'><h3 class='insta-text'>Instagram AutoX</h3><p>Status: {'<span style="color:green;">✅ PRO ACTIVE</span>' if insta_pro_active else '<span style="color:red;">❌ INACTIVE</span>'}</p></div>", unsafe_allow_html=True)

# ----------------------------------------
# 👤 PROFILE & PAYMENT HISTORY
# ----------------------------------------
elif app_mode == "👤 My Profile":
    st.title("👤 My Profile")
    st.markdown(f"**Email:** {st.session_state.logged_in_email}")
    st.markdown(f"**YouTube PRO:** {'✅ Active' if yt_pro_active else '❌ Standard'}")
    st.markdown(f"**Insta PRO:** {'✅ Active' if insta_pro_active else '❌ Standard'}")
    st.markdown(f"**Free Credits Left:** {v_left}")

elif app_mode == "💳 Payment History":
    st.title("💳 Payment History")
    if not (yt_pro_active or insta_pro_active):
        st.info("No active payments found.")
    else:
        if yt_pro_active:
            st.markdown("<div class='glass-card' style='border-left: 5px solid #FF0000;'><h4>🧾 YouTube PRO Subscription</h4><p>Status: <span style='color:green;'>PAID ✅</span> | Amount: $99.00</p></div>", unsafe_allow_html=True)
        if insta_pro_active:
            st.markdown("<div class='glass-card' style='border-left: 5px solid #E1306C;'><h4>🧾 Instagram PRO Subscription</h4><p>Status: <span style='color:green;'>PAID ✅</span> | Amount: $99.00</p></div>", unsafe_allow_html=True)

# ----------------------------------------
# 🎁 REFER & EARN
# ----------------------------------------
elif app_mode == "🎁 Refer & Earn":
    st.title("🎁 Refer & Earn History")
    my_ref = current_user.get('referral_code') if current_user else None
    my_ref = my_ref or 'NOT_GENERATED'
    ref_count = current_user.get('referral_count', 0) if current_user else 0
    
    st.markdown(f"<div class='glass-card' style='text-align:center;'><h3>Your Code: <span style='color:#00d4ff;'>{my_ref}</span></h3><p>Friends Referred: <b>{ref_count}</b></p></div>", unsafe_allow_html=True)
    share_text = urllib.parse.quote(f"Use my AutoX code for free AI Videos: {my_ref}. https://autox-ai.com")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<a href='https://api.whatsapp.com/send?text={share_text}' target='_blank'><button style='background:#25D366; width:100%; border:none; border-radius:10px; color:white; padding:10px;'>💬 WhatsApp</button></a>", unsafe_allow_html=True)
    with c2: st.markdown(f"<a href='https://twitter.com/intent/tweet?text={share_text}' target='_blank'><button style='background:#1DA1F2; width:100%; border:none; border-radius:10px; color:white; padding:10px;'>🐦 Twitter</button></a>", unsafe_allow_html=True)
    
    st.write("### 🎟️ Redeem Code")
    friend_code = st.text_input("Enter Invite Code:")
    if st.button("Redeem Bonus"):
        if friend_code.strip().upper() == my_ref:
            st.error("You cannot use your own code.")
        else:
            friend_data = get_user_by_referral(friend_code.strip().upper())
            if friend_data:
                add_referral_bonus(st.session_state.logged_in_email, friend_data['email'], v_left, friend_data.get('videos_left',0), friend_data.get('referral_count',0))
                st.success("🎉 Code Redeemed! +1 Free Video!")
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ Invalid Code.")

# ----------------------------------------
# 🎥 YOUTUBE PRO ENGINE
# ----------------------------------------
elif app_mode == "🎥 YouTube AutoX":
    st.markdown("<h2><span class='yt-text'>YouTube AutoX</span> Engine</h2>", unsafe_allow_html=True)
    
    is_authorized = yt_pro_active or is_admin or v_left > 0
    
    if not is_authorized:
        st.error("🔒 YouTube PRO Subscription Required")
        st.markdown("<div class='glass-card'><h4>Unlock the Ultimate YouTube Automator</h4><ul><li>16:9 Long Form Generation</li><li>Cinematic Transitions</li><li>Unlimited Rendering</li></ul></div>", unsafe_allow_html=True)
        gumroad_yt = "https://gumroad.com/l/youtube_pro_autox" 
        st.markdown(f"<a href='{gumroad_yt}' target='_blank'><button style='width:100%; background:#FF0000; color:white; padding:15px; border-radius:10px; border:none; font-weight:bold;'>💳 BUY YOUTUBE PRO ($99)</button></a>", unsafe_allow_html=True)
    else:
        if yt_pro_active or is_admin: st.success("✅ YouTube PRO Active (Unlimited)")
        else: st.info(f"🎁 Free Trial Active: {v_left} credits left")
        
        agent_topic = st.text_input("🎯 YouTube Video Idea:")
        c1, c2 = st.columns(2)
        with c1:
            yt_format = st.selectbox("🎥 Video Format:", ["YouTube Standard (16:9)", "YouTube Shorts (9:16)"], key="yt_format")
        with c2:
            agent_voice = st.selectbox("🗣️ Voice & Language:", list(LANGUAGE_VOICES.keys()), key="yt_voice")
        
        if st.button("Generate YouTube Video", use_container_width=True) and agent_topic:
            is_land = "16:9" in yt_format
            run_video_agent(agent_topic, is_landscape=is_land, agent_voice=agent_voice)
            if not (yt_pro_active or is_admin):
                update_videos_left(st.session_state.logged_in_email, v_left - 1)

# ----------------------------------------
# 📱 INSTAGRAM PRO ENGINE
# ----------------------------------------
elif app_mode == "📱 Instagram AutoX":
    st.markdown("<h2><span class='insta-text'>Instagram AutoX</span> Engine</h2>", unsafe_allow_html=True)
    
    is_authorized = insta_pro_active or is_admin or v_left > 0
    
    if not is_authorized:
        st.error("🔒 Instagram PRO Subscription Required")
        st.markdown("<div class='glass-card'><h4>Unlock the Viral Reels Automator</h4><ul><li>9:16 Portrait Generation</li><li>Fast Pacing & Trendy Fonts</li><li>Unlimited Rendering</li></ul></div>", unsafe_allow_html=True)
        gumroad_insta = "https://gumroad.com/l/insta_pro_autox" 
        st.markdown(f"<a href='{gumroad_insta}' target='_blank'><button style='width:100%; background:linear-gradient(45deg, #f09433, #dc2743); color:white; padding:15px; border-radius:10px; border:none; font-weight:bold;'>💳 BUY INSTA PRO ($99)</button></a>", unsafe_allow_html=True)
    else:
        if insta_pro_active or is_admin: st.success("✅ Instagram PRO Active (Unlimited)")
        else: st.info(f"🎁 Free Trial Active: {v_left} credits left")
        
        agent_topic = st.text_input("🎯 Instagram Reel Idea (9:16):")
        agent_voice = st.selectbox("🗣️ Voice & Language:", list(LANGUAGE_VOICES.keys()), key="in_voice")
        
        if st.button("Generate Viral Reel", use_container_width=True) and agent_topic:
            run_video_agent(agent_topic, is_landscape=False, agent_voice=agent_voice)
            if not (insta_pro_active or is_admin):
                update_videos_left(st.session_state.logged_in_email, v_left - 1)
