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

# --- CONFIGURATION FOR SERVER ---
if os.path.exists("/usr/bin/convert"):
    os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"

LANGUAGE_VOICES = {
    "English (Deep Male)": ("English", "en-US-ChristopherNeural"),
    "English (Friendly Female)": ("English", "en-US-AriaNeural"),
    "Hindi (Male)": ("Hindi", "hi-IN-MadhurNeural"),
    "Hindi (Female)": ("Hindi", "hi-IN-SwaraNeural")
}

# 👑 UPDATED ADMIN & SENDER EMAIL
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
    data = {"email": email, "password": password, "has_paid": False}
    requests.post(url, headers=get_sb_headers(), json=data)
    return data

def update_user_password(email, new_password):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?email=eq.{email}"
    data = {"password": new_password}
    requests.patch(url, headers=get_sb_headers(), json=data)

def get_all_users():
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?select=*"
    res = requests.get(url, headers=get_sb_headers())
    return res.json()

def update_user_access(email, has_paid):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?email=eq.{email}"
    data = {"has_paid": has_paid}
    requests.patch(url, headers=get_sb_headers(), json=data)

# --- EMAIL OTP FUNCTION ---
def send_otp_email(recipient_email, otp_code):
    sender_email = ADMIN_EMAIL
    # Get password from secrets and remove spaces
    sender_password = st.secrets["GMAIL_PASSWORD"].replace(" ", "") 
    
    msg = MIMEText(f"Hello!\n\nYou requested an OTP to login to AutoX AI.\nYour secure 6-digit code is: {otp_code}\n\nIf you remember your password, you can ignore this.\n\nBest,\nAutoX AI Team")
    msg['Subject'] = 'AutoX AI - Forgot Password OTP 🔐'
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("Email Error:", e)
        return False


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


# --- HYBRID AUTHENTICATION SYSTEM (PASSWORD + OTP) ---
if 'logged_in_email' not in st.session_state:
    st.session_state.logged_in_email = None
    st.session_state.has_paid = False
    st.session_state.otp_sent = False
    st.session_state.expected_otp = None

if not st.session_state.logged_in_email:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("<br><br>", unsafe_allow_html=True)
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/X_icon_2.svg/2048px-X_icon_2.svg.png", width=60)
        st.title("Welcome to AutoX AI")
        st.markdown("Please log in or create an account to access the AI Creator Suite.")
        
        email_input = st.text_input("📧 Enter your Email Address:")
        
        if email_input:
            user = get_user(email_input.strip())
            
            # SCENARIO 1: NEW USER (CREATE ACCOUNT)
            if not user or not user.get('password'):
                st.info("✨ Looks like you are a new user. Create a password to sign up.")
                new_pwd = st.text_input("🔑 Create a Password:", type="password")
                if st.button("🚀 Sign Up & Login", use_container_width=True):
                    if len(new_pwd) < 4:
                        st.warning("Password must be at least 4 characters.")
                    else:
                        with st.spinner("Creating account..."):
                            if not user:
                                user = create_user(email_input.strip(), new_pwd)
                            else:
                                update_user_password(email_input.strip(), new_pwd)
                                user['has_paid'] = user.get('has_paid', False)
                            
                            st.session_state.logged_in_email = email_input.strip()
                            st.session_state.has_paid = user.get('has_paid', False)
                            st.rerun()
            
            # SCENARIO 2: EXISTING USER (LOGIN)
            else:
                st.success("✅ Account found.")
                pwd_input = st.text_input("🔑 Enter your Password:", type="password")
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("🔓 Login", use_container_width=True):
                        if pwd_input == user['password']:
                            st.session_state.logged_in_email = user['email']
                            st.session_state.has_paid = user['has_paid']
                            st.rerun()
                        else:
                            st.error("❌ Incorrect Password.")
                
                with c_btn2:
                    if st.button("🤔 Forgot Password?", use_container_width=True):
                        with st.spinner("Sending secure OTP to your email..."):
                            otp = str(random.randint(100000, 999999))
                            if send_otp_email(email_input.strip(), otp):
                                st.session_state.otp_sent = True
                                st.session_state.expected_otp = otp
                                st.rerun()
                            else:
                                st.error("Failed to send email. Check Server Config.")
                
                # FORGOT PASSWORD OTP VERIFICATION
                if st.session_state.get('otp_sent'):
                    st.divider()
                    st.info("✅ We sent a 6-digit recovery code to your email.")
                    otp_in = st.text_input("🔢 Enter 6-digit OTP Code:")
                    
                    if st.button("Verify OTP & Login (Bypass Password)"):
                        if otp_in.strip() == st.session_state.expected_otp:
                            st.session_state.logged_in_email = user['email']
                            st.session_state.has_paid = user['has_paid']
                            st.session_state.otp_sent = False
                            st.rerun()
                        else:
                            st.error("❌ Incorrect OTP Code.")

    st.stop()


# --- SIDEBAR: NAVIGATION ---
with st.sidebar:
    st.title("⚡ AutoX AI")
    st.markdown(f"👤 **{st.session_state.logged_in_email}**")
    if st.button("🚪 Logout"):
        st.session_state.logged_in_email = None
        st.rerun()
    st.divider()
    
    if st.session_state.logged_in_email == ADMIN_EMAIL:
        st.write("### 👑 GOD MODE")
        admin_mode = st.radio("Admin", ["None", "👑 Admin Dashboard"], label_visibility="collapsed")
    else:
        admin_mode = "None"
        
    st.write("### 💎 Premium")
    agent_mode = st.radio("Agent", ["None", "🤖 YouTube AI Agent (Pro) 🔒"], label_visibility="collapsed")
    
    st.write("### 🏢 Main Hub")
    dashboard_btn = st.radio("Dashboard", ["None", "AutoX Dashboard"], label_visibility="collapsed")
    
    st.write("### 🎥 Media Tools")
    media_mode = st.radio("Media", ["None", "🎬 AutoTube", "🖼️ AutoThumb"], label_visibility="collapsed")
    
    st.write("### ✍️ Content & Copy")
    content_mode = st.radio("Content", ["None", "✍️ AutoBlog", "📱 AutoSocial"], label_visibility="collapsed")
    
    st.divider()
    st.caption("CEO: Prince Kumar Singh")


app_mode = "AutoX Dashboard"
for mode in [admin_mode, agent_mode, dashboard_btn, media_mode, content_mode]:
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
    st.title("👑 CEO Admin Panel")
    st.markdown("Welcome back, Boss! Here you can manage all users and grant/revoke access.")
    st.divider()
    
    users = get_all_users()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Users", len(users))
    c2.metric("Paid Customers", len([u for u in users if u.get('has_paid')]))
    c3.metric("Revenue", f"${len([u for u in users if u.get('has_paid')]) * 99}")
    
    st.write("### ⚙️ Manage User Access")
    if not users:
        st.write("No users found.")
    else:
        user_emails = [u['email'] for u in users]
        selected_user = st.selectbox("Select Customer Email:", user_emails)
        current_status = next((u.get('has_paid') for u in users if u['email'] == selected_user), False)
        
        st.info(f"Current Status: **{'✅ PAID (Access Granted)' if current_status else '❌ UNPAID (Access Denied)'}**")
        
        new_status = st.radio("Change Status To:", [True, False], format_func=lambda x: "Paid (Unlock Agent)" if x else "Unpaid (Lock Agent)")
        if st.button("💾 Update Customer Access"):
            with st.spinner("Updating Database..."):
                update_user_access(selected_user, new_status)
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
    
    is_authorized = st.session_state.has_paid or st.session_state.logged_in_email == ADMIN_EMAIL
    
    if not is_authorized:
        st.error("🔒 **PREMIUM FEATURE LOCKED**")
        st.markdown("The Autonomous Agent does the work of a Scriptwriter, Voiceover Artist, Video Editor, and SEO Expert all at the same time.")
        st.divider()
        st.write("### 💳 Upgrade Your Account")
        st.info("Your email does not have a Premium License. Please purchase one to unlock this feature.")
        st.markdown("[👉 Buy Lifetime License for $99 (Gumroad)](#)")
    
    else:
        st.success("✅ **Premium Access Verified. Welcome to the Pro Agent.**")
        model = check_keys()
        agent_topic = st.text_input("🎯 What is the YouTube Video about?")
        agent_voice = st.selectbox("🗣️ Language & Voice:", list(LANGUAGE_VOICES.keys()))
        
        if st.button("🚀 DEPLOY AI AGENT", use_container_width=True) and agent_topic:
            with st.status("🤖 Agent is working...", expanded=True) as status:
                try:
                    # VIDEO GENERATION LOGIC REMAINS IDENTICAL
                    lang, code = LANGUAGE_VOICES[agent_voice]
                    st.write("✍️ Writing viral script & SEO...")
                    prompt = f"Write a 60-second YouTube Shorts script about: {agent_topic}. Language: {lang}. Format EXACTLY like this:\nKEYWORDS: kw1, kw2, kw3\nSCRIPT:\n[script]\nSEO_TITLE:\n[title]\nSEO_TAGS:\n[tags]"
                    res = model.generate_content(prompt).text
                    
                    script = res.split("SCRIPT:")[1].split("SEO_TITLE:")[0].strip()
                    kws = res.split("SCRIPT:")[0].replace("KEYWORDS:", "").strip().split(",")[:3]
                    seo_data = res.split("SEO_TITLE:")[1].strip()
                    
                    st.write("🎙️ Recording voiceover...")
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

                    st.write("🎞️ Editing video...")
                    final_path = "agent_final.mp4"
                    audioclip = AudioFileClip(audio_path)
                    vis = concatenate_videoclips(videos, method="compose") if len(videos) > 1 else videos[0]
                    vis = vis.fx(vfx.loop, duration=audioclip.duration) if vis.duration < audioclip.duration else vis.subclip(0, audioclip.duration)
                    final_vid = vis.set_audio(audioclip)
                    try: final_vid = add_subtitles(final_vid, vtt_path)
                    except: pass
                    final_vid.write_videofile(final_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
                    
                    st.write("🖼️ Generating Thumbnail...")
                    p = model.generate_content(f"Create an 8k hyper-realistic image prompt for a YouTube thumbnail about: '{agent_topic}'. NO TEXT. Max 30 words.").text.strip()
                    thumb_img = requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width=1280&height=720&nologo=true").content
                    with open("agent_thumb.jpg", "wb") as f:
                        f.write(thumb_img)
                    
                    status.update(label="✅ Agent finished!", state="complete", expanded=True)
                    
                    st.divider()
                    st.subheader("🎉 Your Done-For-You Package")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.video(final_path)
                        with open(final_path, "rb") as file:
                            st.download_button("💾 Download Video", file, "Final_Video.mp4", "video/mp4")
                    with c2:
                        st.image("agent_thumb.jpg")
                        with open("agent_thumb.jpg", "rb") as file:
                            st.download_button("💾 Download Thumbnail", file, "Thumbnail.jpg", "image/jpeg")
                    with c3:
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
    st.write("### 🛠️ The Ultimate Ecosystem")
    c1, c2 = st.columns(2)
    with c1:
        st.error("**🤖 YouTube Agent:** All-in-one autonomous bot")
        st.info("**🎬 AutoTube:** Faceless 1-click videos")
    with c2:
        st.success("**✍️ AutoBlog:** SEO optimized articles")
        st.success("**📱 AutoSocial:** Viral posts for Twitter/IG")
