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
    
    msg_body = f"Hello!\n\nYour highly secure OTP code for AutoX AI is: {otp_code}\n\nDo not share this with anyone.\n\nBest,\nAutoX AI System"
    if purpose == "signup":
         msg_body = f"Welcome to AutoX AI!\n\nYour account verification code is: {otp_code}\n\nEnter this to activate your account."
         
    msg = MIMEText(msg_body)
    msg['Subject'] = 'AutoX AI - Verification Code ⚡'
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

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

# --- UI SETUP & FUTURISTIC CSS ---
st.set_page_config(page_title="AutoX AI Empire", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;500;800&display=swap');
        
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        
        /* App Background */
        .stApp {
            background-color: #050814;
            background-image: radial-gradient(circle at 15% 50%, rgba(20, 11, 46, 1), #050814 25%),
                              radial-gradient(circle at 85% 30%, rgba(13, 27, 42, 1), #050814 25%);
            color: #e2e8f0;
            font-family: 'Inter', sans-serif;
        }
        
        /* Gradient Text (Headings) */
        h1, h2, h3 {
            font-family: 'Orbitron', sans-serif;
            background: -webkit-linear-gradient(45deg, #00f2fe, #4facfe, #00f2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }
        
        /* Sidebar Glassmorphism */
        [data-testid="stSidebar"] {
            background: rgba(10, 15, 30, 0.7) !important;
            backdrop-filter: blur(15px);
            border-right: 1px solid rgba(0, 242, 254, 0.1);
        }
        
        /* Futuristic Neon Buttons */
        .stButton>button {
            background: rgba(0, 0, 0, 0.4);
            color: #00f2fe !important;
            border: 1px solid #00f2fe;
            box-shadow: 0 0 10px rgba(0, 242, 254, 0.1), inset 0 0 5px rgba(0, 242, 254, 0.1);
            border-radius: 4px;
            font-family: 'Orbitron', sans-serif;
            letter-spacing: 1px;
            transition: 0.3s;
            padding: 12px 24px;
        }
        .stButton>button:hover {
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.6), inset 0 0 10px rgba(0, 242, 254, 0.4);
            background: rgba(0, 242, 254, 0.1);
            color: #ffffff !important;
            border-color: #ffffff;
            transform: translateY(-2px);
        }
        
        /* Futuristic Inputs */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            background: rgba(255, 255, 255, 0.03) !important;
            color: #00f2fe !important;
            border: 1px solid #1e293b;
            border-radius: 4px;
            font-family: 'Inter', sans-serif;
        }
        .stTextInput input:focus {
            border-color: #00f2fe;
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.3);
        }
        
        /* Info/Success/Error Boxes */
        .stAlert {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            backdrop-filter: blur(5px);
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
        st.title("⚡ AutoX AI Core")
        st.markdown("### SYSTEM_LOGIN_REQUIRED")
        st.caption("Secure encrypted tunnel to the Ultimate AI Creator Suite.")
        st.divider()
        
        email_input = st.text_input("📡 TERMINAL ID (Enter Email):", placeholder="user@domain.com")
        
        if email_input:
            if not is_valid_email(email_input):
                st.error("❌ INVALID_EMAIL_FORMAT")
            else:
                user = get_user(email_input.strip())
                
                # SCENARIO 1: NEW USER (REQUIRE OTP TO CREATE ACCOUNT)
                if not user or not user.get('password'):
                    st.info("✨ INITIALIZING NEW SECTOR: Account not found.")
                    st.markdown("We must verify your email to create an account. This prevents unauthorized access.")
                    
                    if not st.session_state.otp_sent:
                        if st.button("🚀 INITIATE VERIFICATION (Send OTP)", use_container_width=True):
                            with st.spinner("Transmitting encrypted code..."):
                                otp = str(random.randint(100000, 999999))
                                if send_otp_email(email_input.strip(), otp, "signup"):
                                    st.session_state.otp_sent = True
                                    st.session_state.expected_otp = otp
                                    st.session_state.auth_purpose = "signup"
                                    st.rerun()
                                else:
                                    st.error("TRANSMISSION_FAILED: Check Server Config.")
                    
                    # Verify New Account OTP
                    if st.session_state.get('otp_sent') and st.session_state.auth_purpose == "signup":
                        st.success("✅ CODE SENT to terminal.")
                        otp_in = st.text_input("🔢 ENTER 6-DIGIT CODE:")
                        new_pwd = st.text_input("🔑 CREATE MASTER PASSWORD:", type="password")
                        
                        if st.button("CREATE ACCOUNT & LOGIN", use_container_width=True):
                            if otp_in.strip() != st.session_state.expected_otp:
                                st.error("❌ INVALID_CODE")
                            elif len(new_pwd) < 4:
                                st.warning("Password must be at least 4 chars.")
                            else:
                                with st.spinner("Encrypting account..."):
                                    if not user:
                                        user = create_user(email_input.strip(), new_pwd)
                                    else:
                                        update_user_password(email_input.strip(), new_pwd)
                                        user['has_paid'] = user.get('has_paid', False)
                                    
                                    st.session_state.logged_in_email = email_input.strip()
                                    st.session_state.has_paid = user.get('has_paid', False)
                                    st.session_state.otp_sent = False
                                    st.rerun()
                
                # SCENARIO 2: EXISTING USER (LOGIN)
                else:
                    st.success("✅ IDENTITY FOUND.")
                    pwd_input = st.text_input("🔑 ENTER PASSWORD:", type="password")
                    
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        if st.button("🔓 AUTHORIZE", use_container_width=True):
                            if pwd_input == user['password']:
                                st.session_state.logged_in_email = user['email']
                                st.session_state.has_paid = user['has_paid']
                                st.rerun()
                            else:
                                st.error("❌ ACCESS_DENIED: Incorrect Password.")
                    
                    with c_btn2:
                        if st.button("🤔 FORGOT PASSWORD?", use_container_width=True):
                            with st.spinner("Transmitting recovery code..."):
                                otp = str(random.randint(100000, 999999))
                                if send_otp_email(email_input.strip(), otp, "login"):
                                    st.session_state.otp_sent = True
                                    st.session_state.expected_otp = otp
                                    st.session_state.auth_purpose = "login"
                                    st.rerun()
                                else:
                                    st.error("TRANSMISSION_FAILED")
                    
                    # FORGOT PASSWORD OTP VERIFICATION
                    if st.session_state.get('otp_sent') and st.session_state.auth_purpose == "login":
                        st.divider()
                        st.info("✅ We sent a 6-digit recovery code to your email.")
                        otp_in = st.text_input("🔢 ENTER RECOVERY CODE:")
                        
                        if st.button("VERIFY CODE & OVERRIDE", use_container_width=True):
                            if otp_in.strip() == st.session_state.expected_otp:
                                st.session_state.logged_in_email = user['email']
                                st.session_state.has_paid = user['has_paid']
                                st.session_state.otp_sent = False
                                st.rerun()
                            else:
                                st.error("❌ INVALID_CODE")

    st.stop()


# --- SIDEBAR: NAVIGATION ---
with st.sidebar:
    st.title("⚡ AutoX AI")
    st.markdown(f"👤 **{st.session_state.logged_in_email}**")
    if st.button("🚪 SYSTEM_LOGOUT"):
        st.session_state.logged_in_email = None
        st.rerun()
    st.divider()
    
    if st.session_state.logged_in_email == ADMIN_EMAIL:
        st.write("### 👑 GOD MODE (CEO)")
        admin_mode = st.radio("Admin", ["None", "👑 Admin Dashboard"], label_visibility="collapsed")
    else:
        admin_mode = "None"
        
    st.write("### 💎 PREMIUM SECTOR")
    agent_mode = st.radio("Agent", ["None", "🤖 YouTube AI Agent (Pro) 🔒"], label_visibility="collapsed")
    
    st.write("### 🏢 COMMAND HUB")
    dashboard_btn = st.radio("Dashboard", ["None", "AutoX Dashboard"], label_visibility="collapsed")
    
    st.write("### 🎥 MEDIA PROTOCOLS")
    media_mode = st.radio("Media", ["None", "🎬 AutoTube", "🖼️ AutoThumb"], label_visibility="collapsed")
    
    st.write("### ✍️ CONTENT ENGINES")
    content_mode = st.radio("Content", ["None", "✍️ AutoBlog", "📱 AutoSocial"], label_visibility="collapsed")
    
    st.divider()
    st.caption("BUILT FOR THE FUTURE | CEO: Prince Kumar Singh")


app_mode = "AutoX Dashboard"
for mode in [admin_mode, agent_mode, dashboard_btn, media_mode, content_mode]:
    if mode != "None":
        app_mode = mode

# --- SECURE API KEYS ---
try:
    user_gemini_key = st.secrets["GEMINI_API_KEY"]
    user_pexels_key = st.secrets["PEXELS_API_KEY"]
except:
    st.error("⚠️ CRITICAL_ERROR: Keys missing in Server Vault.")
    st.stop()

def check_keys():
    genai.configure(api_key=user_gemini_key)
    return genai.GenerativeModel('gemini-3.6-flash')


# ==========================================
# PAGE: ADMIN DASHBOARD (GOD MODE)
# ==========================================
if app_mode == "👑 Admin Dashboard":
    st.title("👑 CEO CONTROL TERMINAL")
    st.markdown("Welcome back, Boss. Network is secure.")
    st.divider()
    
    users = get_all_users()
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL TERMINALS (Users)", len(users))
    c2.metric("ELITE PROTOCOLS (Paid)", len([u for u in users if u.get('has_paid')]))
    c3.metric("NETWORK REVENUE", f"${len([u for u in users if u.get('has_paid')]) * 99}")
    
    st.write("### ⚙️ ACCESS MANAGEMENT OVERRIDE")
    if not users:
        st.write("No users found.")
    else:
        user_emails = [u['email'] for u in users]
        selected_user = st.selectbox("Select Target Terminal (Email):", user_emails)
        current_status = next((u.get('has_paid') for u in users if u['email'] == selected_user), False)
        
        st.info(f"Current Status: **{'✅ PAID (Access Granted)' if current_status else '❌ UNPAID (Access Denied)'}**")
        
        new_status = st.radio("Override Status To:", [True, False], format_func=lambda x: "Paid (Unlock Agent)" if x else "Unpaid (Lock Agent)")
        if st.button("💾 EXECUTE OVERRIDE"):
            with st.spinner("Executing database override..."):
                update_user_access(selected_user, new_status)
                if selected_user == st.session_state.logged_in_email:
                    st.session_state.has_paid = new_status
                st.success("Target access overridden successfully!")
                time.sleep(1)
                st.rerun()

# ==========================================
# PAGE: YOUTUBE AI AGENT (PRO) 🔒
# ==========================================
elif app_mode == "🤖 YouTube AI Agent (Pro) 🔒":
    st.title("🤖 AUTONOMOUS AGENT PROTOCOL")
    
    is_authorized = st.session_state.has_paid or st.session_state.logged_in_email == ADMIN_EMAIL
    
    if not is_authorized:
        st.error("🔒 **CLEARANCE LEVEL INSUFFICIENT**")
        st.markdown("The Autonomous Agent requires ELITE access. It handles scripting, voice synthesis, video rendering, and SEO injection.")
        st.divider()
        st.write("### 💳 ACQUIRE ELITE CLEARANCE")
        st.info("Your terminal lacks Premium License. Purchase one to unlock the Agent Protocol.")
        st.markdown("[👉 Acquire Lifetime License for $99 (Gumroad)](#)")
    
    else:
        st.success("✅ **CLEARANCE VERIFIED. AGENT STANDING BY.**")
        model = check_keys()
        agent_topic = st.text_input("🎯 TARGET TOPIC FOR INJECTION:")
        agent_voice = st.selectbox("🗣️ SYNTHESIS VOICE:", list(LANGUAGE_VOICES.keys()))
        
        if st.button("🚀 INITIATE AGENT", use_container_width=True) and agent_topic:
            with st.status("🤖 AGENT ONLINE...", expanded=True) as status:
                try:
                    lang, code = LANGUAGE_VOICES[agent_voice]
                    st.write("✍️ Generating neural script & SEO...")
                    prompt = f"Write a 60-second YouTube Shorts script about: {agent_topic}. Language: {lang}. Format EXACTLY like this:\nKEYWORDS: kw1, kw2, kw3\nSCRIPT:\n[script]\nSEO_TITLE:\n[title]\nSEO_TAGS:\n[tags]"
                    res = model.generate_content(prompt).text
                    
                    script = res.split("SCRIPT:")[1].split("SEO_TITLE:")[0].strip()
                    kws = res.split("SCRIPT:")[0].replace("KEYWORDS:", "").strip().split(",")[:3]
                    seo_data = res.split("SEO_TITLE:")[1].strip()
                    
                    st.write("🎙️ Synthesizing voiceprint...")
                    audio_path, vtt_path = "agent_voice.mp3", "agent_voice.vtt"
                    subprocess.run(["python3", "-m", "edge_tts", "--text", script, "--voice", code, "--write-media", audio_path, "--write-subtitles", vtt_path], check=True)
                    
                    st.write("🎥 Extracting visual assets...")
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

                    st.write("🎞️ Rendering final output...")
                    final_path = "agent_final.mp4"
                    audioclip = AudioFileClip(audio_path)
                    vis = concatenate_videoclips(videos, method="compose") if len(videos) > 1 else videos[0]
                    vis = vis.fx(vfx.loop, duration=audioclip.duration) if vis.duration < audioclip.duration else vis.subclip(0, audioclip.duration)
                    final_vid = vis.set_audio(audioclip)
                    try: final_vid = add_subtitles(final_vid, vtt_path)
                    except: pass
                    final_vid.write_videofile(final_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
                    
                    st.write("🖼️ Generating neural thumbnail...")
                    p = model.generate_content(f"Create an 8k hyper-realistic image prompt for a YouTube thumbnail about: '{agent_topic}'. NO TEXT. Max 30 words.").text.strip()
                    thumb_img = requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width=1280&height=720&nologo=true").content
                    with open("agent_thumb.jpg", "wb") as f:
                        f.write(thumb_img)
                    
                    status.update(label="✅ AGENT EXECUTION COMPLETE!", state="complete", expanded=True)
                    
                    st.divider()
                    st.subheader("🎉 ASSETS READY FOR DEPLOYMENT")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.video(final_path)
                        with open(final_path, "rb") as file:
                            st.download_button("💾 DOWNLOAD MEDIA", file, "Final_Video.mp4", "video/mp4")
                    with c2:
                        st.image("agent_thumb.jpg")
                        with open("agent_thumb.jpg", "rb") as file:
                            st.download_button("💾 DOWNLOAD THUMBNAIL", file, "Thumbnail.jpg", "image/jpeg")
                    with c3:
                        st.info(seo_data)
                        st.download_button("💾 DOWNLOAD SEO DATA", seo_data, "SEO_Data.txt")
                        
                except Exception as e:
                    status.update(label="❌ SYSTEM FAILURE", state="error")
                    st.error(e)

# ==========================================
# PAGE: DASHBOARD 
# ==========================================
elif app_mode == "AutoX Dashboard":
    st.title("⚡ AUTOX AI COMMAND HUB")
    st.markdown("Welcome to the most advanced AI automation ecosystem on the grid.")
    st.write("### 🛠️ ACTIVE PROTOCOLS")
    c1, c2 = st.columns(2)
    with c1:
        st.error("**🤖 YouTube Agent:** All-in-one autonomous bot")
        st.info("**🎬 AutoTube:** Faceless 1-click videos")
    with c2:
        st.success("**✍️ AutoBlog:** SEO optimized articles")
        st.success("**📱 AutoSocial:** Viral posts for Twitter/IG")
