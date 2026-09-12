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

# --- CONFIGURATION FOR SERVER ---
if os.path.exists("/usr/bin/convert"):
    os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"

LANGUAGE_VOICES = {
    "English (Deep Male)": ("English", "en-US-ChristopherNeural"),
    "English (Friendly Female)": ("English", "en-US-AriaNeural"),
    "Hindi (Male)": ("Hindi", "hi-IN-MadhurNeural"),
    "Hindi (Female)": ("Hindi", "hi-IN-SwaraNeural")
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
def send_otp_email(recipient_email, otp_code, purpose="login"):
    sender_email = ADMIN_EMAIL
    sender_password = st.secrets["GMAIL_PASSWORD"].replace(" ", "") 
    
    msg_body = f"Hello Creator,\n\nYour YouTube AI Studio verification code is: {otp_code}\n\nDo not share this code with anyone.\n\nThanks,\nThe AutoX YouTube Team"
    if purpose == "signup":
         msg_body = f"Welcome to YouTube AI Studio by AutoX!\n\nYour account verification code is: {otp_code}\n\nEnter this to activate your Creator account."
         
    msg = MIMEText(msg_body)
    msg['Subject'] = 'YouTube AI Studio - Verification Code'
    msg['From'] = f"YouTube AI Studio <{sender_email}>"
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

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

# --- YOUTUBE OFFICIAL UI SETUP & CSS ---
st.set_page_config(page_title="YouTube AI Studio", page_icon="▶️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
        
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        
        /* YouTube Dark Mode Background */
        .stApp {
            background-color: #0F0F0F;
            color: #F1F1F1;
            font-family: 'Roboto', sans-serif;
        }
        
        /* Headings */
        h1, h2, h3 {
            font-family: 'Roboto', sans-serif;
            color: #FFFFFF;
            font-weight: 700;
        }
        
        /* YouTube Dark Sidebar */
        [data-testid="stSidebar"] {
            background-color: #212121 !important;
            border-right: 1px solid #303030;
        }
        
        /* YouTube Red Pill Buttons */
        .stButton>button {
            background-color: #FF0000;
            color: #FFFFFF !important;
            border: none;
            border-radius: 24px; /* YouTube Pill shape */
            font-family: 'Roboto', sans-serif;
            font-weight: 500;
            letter-spacing: 0.5px;
            transition: 0.2s;
            padding: 10px 24px;
        }
        .stButton>button:hover {
            background-color: #CC0000;
            color: #FFFFFF !important;
        }
        
        /* YouTube Inputs */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            background-color: #121212 !important;
            color: #F1F1F1 !important;
            border: 1px solid #303030;
            border-radius: 8px;
            font-family: 'Roboto', sans-serif;
        }
        .stTextInput input:focus {
            border-color: #3EA6FF; /* YouTube Blue Focus */
            box-shadow: none;
        }
        
        /* Info/Success/Error Boxes */
        .stAlert {
            background-color: #212121 !important;
            border: 1px solid #303030;
            border-radius: 8px;
            color: #F1F1F1;
        }
    </style>
""", unsafe_allow_html=True)


# --- ULTRA-SECURE HYBRID AUTHENTICATION SYSTEM ---
if 'logged_in_email' not in st.session_state:
    st.session_state.logged_in_email = None
    st.session_state.has_paid = False
    st.session_state.otp_sent = False
    st.session_state.expected_otp = None
    st.session_state.auth_purpose = None

if not st.session_state.logged_in_email:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("<br><br>", unsafe_allow_html=True)
        # Using a YouTube-like Play Icon for branding
        st.markdown("<h1 style='text-align: center; color: #FF0000; font-size: 50px;'>▶️</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>YouTube AI Studio</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #AAAAAA;'>Sign in with your Creator Email to continue</p>", unsafe_allow_html=True)
        st.divider()
        
        email_input = st.text_input("Email or phone", placeholder="Enter your email")
        
        if email_input:
            if not is_valid_email(email_input):
                st.error("Enter a valid email address")
            else:
                user = get_user(email_input.strip())
                
                # SCENARIO 1: NEW USER
                if not user or not user.get('password'):
                    st.info("Create a new Creator Account to continue.")
                    
                    if not st.session_state.otp_sent:
                        if st.button("Send Verification Code", use_container_width=True):
                            with st.spinner("Sending code..."):
                                otp = str(random.randint(100000, 999999))
                                if send_otp_email(email_input.strip(), otp, "signup"):
                                    st.session_state.otp_sent = True
                                    st.session_state.expected_otp = otp
                                    st.session_state.auth_purpose = "signup"
                                    st.rerun()
                                else:
                                    st.error("Failed to send email. Check Server Config.")
                    
                    if st.session_state.get('otp_sent') and st.session_state.auth_purpose == "signup":
                        st.success("Verification code sent to your email.")
                        otp_in = st.text_input("Enter code")
                        new_pwd = st.text_input("Create password", type="password")
                        
                        if st.button("Next", use_container_width=True):
                            if otp_in.strip() != st.session_state.expected_otp:
                                st.error("Wrong code. Try again.")
                            elif len(new_pwd) < 4:
                                st.warning("Password must be at least 4 chars.")
                            else:
                                with st.spinner("Creating account..."):
                                    if not user:
                                        user = create_user(email_input.strip(), new_pwd)
                                    else:
                                        update_user_password(email_input.strip(), new_pwd)
                                        user['has_paid'] = user.get('has_paid', False)
                                    
                                    st.session_state.logged_in_email = email_input.strip()
                                    st.session_state.has_paid = user.get('has_paid', False)
                                    st.session_state.otp_sent = False
                                    st.rerun()
                
                # SCENARIO 2: EXISTING USER
                else:
                    pwd_input = st.text_input("Enter your password", type="password")
                    
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        if st.button("Next", use_container_width=True):
                            if pwd_input == user['password']:
                                st.session_state.logged_in_email = user['email']
                                st.session_state.has_paid = user['has_paid']
                                st.rerun()
                            else:
                                st.error("Wrong password. Try again.")
                    
                    with c_btn2:
                        if st.button("Forgot password?", use_container_width=True):
                            with st.spinner("Sending code..."):
                                otp = str(random.randint(100000, 999999))
                                if send_otp_email(email_input.strip(), otp, "login"):
                                    st.session_state.otp_sent = True
                                    st.session_state.expected_otp = otp
                                    st.session_state.auth_purpose = "login"
                                    st.rerun()
                                else:
                                    st.error("Failed to send email.")
                    
                    if st.session_state.get('otp_sent') and st.session_state.auth_purpose == "login":
                        st.divider()
                        st.info("A verification code was sent to your email.")
                        otp_in = st.text_input("Enter code")
                        
                        if st.button("Verify", use_container_width=True):
                            if otp_in.strip() == st.session_state.expected_otp:
                                st.session_state.logged_in_email = user['email']
                                st.session_state.has_paid = user['has_paid']
                                st.session_state.otp_sent = False
                                st.rerun()
                            else:
                                st.error("Wrong code. Try again.")

    st.stop()


# --- SIDEBAR: NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='color: white;'>▶️ YouTube AI Studio</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #AAAAAA;'>{st.session_state.logged_in_email}</p>", unsafe_allow_html=True)
    if st.button("Sign out"):
        st.session_state.logged_in_email = None
        st.rerun()
    st.divider()
    
    if st.session_state.logged_in_email == ADMIN_EMAIL:
        st.write("### ⚙️ YouTube Analytics (Admin)")
        admin_mode = st.radio("Admin", ["None", "📊 Channel Analytics"], label_visibility="collapsed")
    else:
        admin_mode = "None"
        
    st.write("### 💎 YouTube Premium")
    agent_mode = st.radio("Agent", ["None", "🤖 YouTube Auto-Creator (Pro)"], label_visibility="collapsed")
    
    st.write("### 🏠 Studio Home")
    dashboard_btn = st.radio("Dashboard", ["None", "Creator Dashboard"], label_visibility="collapsed")
    
    st.write("### 🎥 Content Creation")
    media_mode = st.radio("Media", ["None", "🎬 Auto Shorts", "🖼️ Thumbnail Generator"], label_visibility="collapsed")
    
    st.write("### ✍️ Community & Posts")
    content_mode = st.radio("Content", ["None", "✍️ Community Articles", "📱 Social Media Sync"], label_visibility="collapsed")
    
    st.divider()
    st.caption("Powered by AutoX AI")


app_mode = "Creator Dashboard"
for mode in [admin_mode, agent_mode, dashboard_btn, media_mode, content_mode]:
    if mode != "None":
        app_mode = mode

# --- SECURE API KEYS ---
try:
    user_gemini_key = st.secrets["GEMINI_API_KEY"]
    user_pexels_key = st.secrets["PEXELS_API_KEY"]
except:
    st.error("System configuration error. Please contact support.")
    st.stop()

def check_keys():
    genai.configure(api_key=user_gemini_key)
    return genai.GenerativeModel('gemini-3.6-flash')


# ==========================================
# PAGE: ADMIN DASHBOARD
# ==========================================
if app_mode == "📊 Channel Analytics":
    st.title("📊 YouTube Studio Analytics")
    st.markdown("Manage your creator network and grant YouTube Premium Access.")
    st.divider()
    
    users = get_all_users()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Subscribers (Users)", len(users))
    c2.metric("YouTube Premium (Paid)", len([u for u in users if u.get('has_paid')]))
    c3.metric("Estimated Revenue", f"${len([u for u in users if u.get('has_paid')]) * 99}")
    
    st.write("### ⚙️ Manage Creator Access")
    if not users:
        st.write("No users found.")
    else:
        user_emails = [u['email'] for u in users]
        selected_user = st.selectbox("Select Creator Email:", user_emails)
        current_status = next((u.get('has_paid') for u in users if u['email'] == selected_user), False)
        
        st.info(f"Current Status: **{'✅ Premium Active' if current_status else '❌ Standard Account'}**")
        
        new_status = st.radio("Change Status To:", [True, False], format_func=lambda x: "Enable Premium (Unlock)" if x else "Disable Premium (Lock)")
        if st.button("Save Changes"):
            with st.spinner("Updating Google servers..."):
                update_user_access(selected_user, new_status)
                if selected_user == st.session_state.logged_in_email:
                    st.session_state.has_paid = new_status
                st.success("Creator access updated successfully!")
                time.sleep(1)
                st.rerun()

# ==========================================
# PAGE: YOUTUBE AI AGENT (PRO) 
# ==========================================
elif app_mode == "🤖 YouTube Auto-Creator (Pro)":
    st.title("🤖 YouTube Auto-Creator")
    
    is_authorized = st.session_state.has_paid or st.session_state.logged_in_email == ADMIN_EMAIL
    
    if not is_authorized:
        st.error("🔒 **YOUTUBE PREMIUM REQUIRED**")
        st.markdown("The Auto-Creator is an exclusive feature for YouTube Premium members. It generates full videos, thumbnails, and SEO automatically.")
        st.divider()
        st.write("### 💳 Upgrade to Premium")
        st.info("Your account does not have an active Premium subscription.")
        st.markdown("[👉 Upgrade Now for $99 (Gumroad)](#)")
    
    else:
        st.success("✅ **YouTube Premium Active. Welcome Creator.**")
        model = check_keys()
        agent_topic = st.text_input("🎯 Video Idea or Title:")
        agent_voice = st.selectbox("🗣️ Select Voice Actor:", list(LANGUAGE_VOICES.keys()))
        
        if st.button("Create Video", use_container_width=True) and agent_topic:
            with st.status("🤖 AI is creating your YouTube video...", expanded=True) as status:
                try:
                    lang, code = LANGUAGE_VOICES[agent_voice]
                    st.write("✍️ Writing script & SEO...")
                    prompt = f"Write a 60-second YouTube Shorts script about: {agent_topic}. Language: {lang}. Format EXACTLY like this:\nKEYWORDS: kw1, kw2, kw3\nSCRIPT:\n[script]\nSEO_TITLE:\n[title]\nSEO_TAGS:\n[tags]"
                    res = model.generate_content(prompt).text
                    
                    script = res.split("SCRIPT:")[1].split("SEO_TITLE:")[0].strip()
                    kws = res.split("SCRIPT:")[0].replace("KEYWORDS:", "").strip().split(",")[:3]
                    seo_data = res.split("SEO_TITLE:")[1].strip()
                    
                    st.write("🎙️ Recording voiceover...")
                    audio_path, vtt_path = "agent_voice.mp3", "agent_voice.vtt"
                    subprocess.run(["python3", "-m", "edge_tts", "--text", script, "--voice", code, "--write-media", audio_path, "--write-subtitles", vtt_path], check=True)
                    
                    st.write("🎥 Fetching stock footage...")
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

                    st.write("🎞️ Editing video & subtitles...")
                    final_path = "agent_final.mp4"
                    audioclip = AudioFileClip(audio_path)
                    vis = concatenate_videoclips(videos, method="compose") if len(videos) > 1 else videos[0]
                    vis = vis.fx(vfx.loop, duration=audioclip.duration) if vis.duration < audioclip.duration else vis.subclip(0, audioclip.duration)
                    final_vid = vis.set_audio(audioclip)
                    try: final_vid = add_subtitles(final_vid, vtt_path)
                    except: pass
                    final_vid.write_videofile(final_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
                    
                    st.write("🖼️ Generating custom thumbnail...")
                    p = model.generate_content(f"Create an 8k hyper-realistic image prompt for a YouTube thumbnail about: '{agent_topic}'. NO TEXT. Max 30 words.").text.strip()
                    thumb_img = requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width=1280&height=720&nologo=true").content
                    with open("agent_thumb.jpg", "wb") as f:
                        f.write(thumb_img)
                    
                    status.update(label="✅ Video is ready to publish!", state="complete", expanded=True)
                    
                    st.divider()
                    st.subheader("🎉 Your Upload Package")
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
                    status.update(label="❌ Error creating video", state="error")
                    st.error(e)

# ==========================================
# PAGE: DASHBOARD 
# ==========================================
elif app_mode == "Creator Dashboard":
    st.title("▶️ Creator Dashboard")
    st.markdown("Welcome to YouTube AI Studio. Manage your content generation below.")
    st.write("### 🛠️ Official Tools")
    c1, c2 = st.columns(2)
    with c1:
        st.error("**🤖 YouTube Auto-Creator:** All-in-one autonomous bot")
        st.info("**🎬 Auto Shorts:** Faceless 1-click videos")
    with c2:
        st.success("**✍️ Community Articles:** SEO optimized blogs")
        st.success("**📱 Social Sync:** Viral posts for Twitter/IG")
