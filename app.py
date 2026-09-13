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
        "email": email, "password": password, "has_paid": False, 
        "videos_left": 1, "referral_code": ref_code,
        "yt_pro": False, "insta_pro": False, "referral_count": 0
    }
    requests.post(url, headers=get_sb_headers(), json=data)
    return data

def update_user_password(email, new_password):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?email=eq.{email}"
    data = {"password": new_password}
    requests.patch(url, headers=get_sb_headers(), json=data)

def is_valid_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)

def update_videos_left(email, new_count):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?email=eq.{email}"
    requests.patch(url, headers=get_sb_headers(), json={"videos_left": new_count})

def get_user_by_referral(ref_code):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?referral_code=eq.{ref_code}"
    res = requests.get(url, headers=get_sb_headers())
    if res.status_code == 200 and len(res.json()) > 0: return res.json()[0]
    return None

def add_referral_bonus(my_email, friend_email, my_current_credits, friend_current_credits, friend_current_ref_count):
    update_videos_left(my_email, my_current_credits + 1)
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?email=eq.{friend_email}"
    requests.patch(url, headers=get_sb_headers(), json={"videos_left": friend_current_credits + 1, "referral_count": friend_current_ref_count + 1})

# --- EMAIL OTP FUNCTION (RESTORED) ---
def send_otp_email(recipient_email, otp_code, purpose="login"):
    sender_email = ADMIN_EMAIL
    sender_password = st.secrets.get("GMAIL_PASSWORD", "").replace(" ", "") 
    msg_body = f"Your AutoX verification code is: {otp_code}" if purpose == "login" else f"Welcome! Your verification code is: {otp_code}"
    msg = MIMEText(msg_body)
    msg['Subject'] = 'AutoX - Verification Code'
    msg['From'] = f"AutoX <{sender_email}>"
    msg['To'] = recipient_email
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except: return False


# --- UI SETUP & LIGHT CSS (RESTORED) ---
st.set_page_config(page_title="AutoX App Portal", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700;900&display=swap');
        .stApp { background-color: #FAFAFA !important; color: #111111 !important; font-family: 'Roboto', sans-serif; }
        h1, h2, h3, h4 { color: #111111 !important; font-weight: 900; letter-spacing: -0.5px; }
        .brand-text { background: linear-gradient(90deg, #FF0055 0%, #0033FF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900; }
        .yt-text { color: #FF0000; font-weight: 900; }
        .insta-text { background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900; }
        
        [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #EBEBEB; box-shadow: 2px 0px 15px rgba(0,0,0,0.02); }
        [data-testid="stSidebar"] * { color: #111111 !important; }
        
        /* Fixed Buttons */
        .stButton>button { background: linear-gradient(90deg, #111111 0%, #333333 100%) !important; color: #FFFFFF !important; border: none; border-radius: 8px; font-weight: 700; padding: 12px 24px; }
        
        .stTextInput input, .stSelectbox div[data-baseweb="select"] { background-color: #FFFFFF !important; color: #111111 !important; border: 1px solid #E0E0E0 !important; border-radius: 8px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02); }
        .stTextInput input:focus { border-color: #0033FF !important; }
        
        .feature-card { background: #FFFFFF; border: 1px solid #EBEBEB; border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 16px; }
        .footer { text-align: center; margin-top: 50px; padding: 30px; border-top: 1px solid #E0E0E0; color: #666; font-size: 14px; }
        .footer a { color: #0033FF; text-decoration: none; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- STATE MANAGEMENT ---
if 'logged_in_email' not in st.session_state:
    st.session_state.logged_in_email = None
    st.session_state.otp_sent = False
    st.session_state.expected_otp = None
    st.session_state.auth_purpose = None


# ==========================================
# PAGE 1: LOGIN SCREEN (SIMPLE & CLEAN)
# ==========================================
if not st.session_state.logged_in_email:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("<br><br><br>", unsafe_allow_html=True)
        # Show Logo on Login Page
        try:
            st.image(Image.open("/Users/princekumarsingh/.gemini/antigravity/brain/14257aba-a9b6-466d-94bd-670877ef98ec/autox_logo_1789214937891.jpg"), use_container_width=True)
        except:
            st.markdown("<h2 style='text-align: center;'><span class='brand-text'>AutoX</span> Portal</h2>", unsafe_allow_html=True)
            
        st.markdown("<p style='text-align: center; color: #606060 !important;'>Sign in to access your AI Workforce.</p>", unsafe_allow_html=True)
        st.divider()
        
        email_input = st.text_input("Work Email", placeholder="Enter your email")
        
        if email_input:
            if not is_valid_email(email_input):
                st.error("Enter a valid email address")
            else:
                user = get_user(email_input.strip())
                
                # SCENARIO 1: NEW USER
                if not user or not user.get('password'):
                    st.info("Create a new AutoX Account.")
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
                                    st.error("Failed to send email.")
                    
                    if st.session_state.get('otp_sent') and st.session_state.auth_purpose == "signup":
                        st.success("Verification code sent.")
                        otp_in = st.text_input("Enter code")
                        new_pwd = st.text_input("Create password", type="password")
                        if st.button("Complete Signup", use_container_width=True):
                            if otp_in.strip() != st.session_state.expected_otp:
                                st.error("Wrong code.")
                            elif len(new_pwd) < 4:
                                st.warning("Password must be at least 4 chars.")
                            else:
                                if not user: create_user(email_input.strip(), new_pwd)
                                else: update_user_password(email_input.strip(), new_pwd)
                                st.session_state.logged_in_email = email_input.strip()
                                st.session_state.otp_sent = False
                                st.rerun()
                
                # SCENARIO 2: EXISTING USER (FORGOT PASSWORD RESTORED)
                else:
                    pwd_input = st.text_input("Enter your password", type="password")
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        if st.button("Login", use_container_width=True):
                            if pwd_input == user['password']:
                                st.session_state.logged_in_email = user['email']
                                st.rerun()
                            else:
                                st.error("Wrong password.")
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
                        st.info("Verification code sent.")
                        otp_in = st.text_input("Enter code")
                        if st.button("Verify & Login", use_container_width=True):
                            if otp_in.strip() == st.session_state.expected_otp:
                                st.session_state.logged_in_email = user['email']
                                st.session_state.otp_sent = False
                                st.rerun()
                            else:
                                st.error("Wrong code.")
    
    st.markdown("""
        <div class='footer'>
            <p>AutoX AI Inc. © 2026 | Created by Prince</p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()


# ==========================================
# POST-LOGIN: REFRESH DATA & SIDEBAR
# ==========================================
current_user = get_user(st.session_state.logged_in_email)
if not current_user: st.stop()

yt_pro_active = current_user.get('yt_pro', False)
insta_pro_active = current_user.get('insta_pro', False)
v_left = current_user.get('videos_left', 0)
is_admin = (st.session_state.logged_in_email == ADMIN_EMAIL)
if is_admin: yt_pro_active, insta_pro_active = True, True

st.sidebar.markdown("<h2>⚡ <span class='brand-text'>AutoX</span></h2>", unsafe_allow_html=True)
st.sidebar.divider()
app_mode = st.sidebar.radio("Navigation", ["🏠 Main Hub (Home)", "🎥 YouTube AutoX", "📱 Instagram AutoX"], label_visibility="collapsed")
st.sidebar.divider()

with st.sidebar.expander("⚙️ Account & Settings (•••)"):
    settings_mode = st.radio("Options", ["👤 My Profile", "💳 Payment History", "🎁 Refer & Earn", "🚪 Logout"], label_visibility="collapsed")
    if settings_mode == "🚪 Logout":
        st.session_state.logged_in_email = None
        st.rerun()
    elif settings_mode != "👤 My Profile": 
        app_mode = settings_mode
        
if settings_mode == "👤 My Profile": app_mode = "👤 My Profile"


# --- CORE GENERATION ENGINE ---
def run_video_agent(agent_topic, is_landscape, agent_voice):
    try: user_gemini_key = st.secrets["GEMINI_API_KEY"]; user_pexels_key = st.secrets["PEXELS_API_KEY"]
    except: st.error("API Keys missing in secrets."); return
    genai.configure(api_key=user_gemini_key); model = genai.GenerativeModel('gemini-3.6-flash')
    
    width, height = (1280, 720) if is_landscape else (720, 1280)
    agent_format = "YouTube Standard (16:9)" if is_landscape else "Instagram Reels (9:16)"
    
    with st.status("🤖 AutoX AI is crafting your masterpiece...", expanded=True) as status:
        try:
            lang, code = LANGUAGE_VOICES[agent_voice]
            st.write("✍️ Writing script & SEO...")
            res = model.generate_content(f"Write a 60-second viral video script about: {agent_topic}. Format: {agent_format}. Language: {lang}. Format EXACTLY like this:\nKEYWORDS: kw1, kw2\nSCRIPT:\n[script]\nSEO_TITLE:\n[title]\nSEO_TAGS:\n[tags]").text
            
            script = res.split("SCRIPT:")[1].split("SEO_TITLE:")[0].strip()
            kws = res.split("SCRIPT:")[0].replace("KEYWORDS:", "").strip().split(",")[:2]
            
            st.write("🎙️ Synthesizing Voice...")
            subprocess.run(["python3", "-m", "edge_tts", "--text", script, "--voice", code, "--write-media", "a.mp3", "--write-subtitles", "a.vtt"], check=True)
            
            st.write("🎥 Fetching Footage...")
            videos = []
            for kw in kws:
                r = requests.get(f"https://api.pexels.com/videos/search?query={kw.strip()}&per_page=1&orientation={'landscape' if is_landscape else 'portrait'}&size=medium", headers={"Authorization": user_pexels_key}).json()
                vdata = r.get('videos', [])
                if vdata and vdata[0].get('video_files'):
                    with open(f"v_{kw}.mp4", 'wb') as f: f.write(requests.get(vdata[0]['video_files'][0]['link']).content)
                    videos.append(VideoFileClip(f"v_{kw}.mp4").resize(newsize=(width, height)).crossfadein(0.5))
            
            if not videos: videos.append(ImageClip("fb.jpg").resize(newsize=(width, height)).set_duration(5))

            st.write("🎞️ Rendering Final Video...")
            vis = concatenate_videoclips(videos, padding=-0.5, method="compose") if len(videos)>1 else videos[0]
            aclip = AudioFileClip("a.mp3")
            vis = vis.fx(vfx.loop, duration=aclip.duration) if vis.duration < aclip.duration else vis.subclip(0, aclip.duration)
            final_vid = vis.set_audio(aclip)
            
            if os.path.exists("a.vtt"):
                subs = webvtt.read("a.vtt")
                txts = [TextClip(s.text, fontsize=int(width/15), color='white', stroke_color='black', stroke_width=3, method='caption', size=(width-100, None)).set_position('center').set_start(int(s.start.split(':')[0])*3600 + int(s.start.split(':')[1])*60 + float(s.start.split(':')[2])).set_end(int(s.end.split(':')[0])*3600 + int(s.end.split(':')[1])*60 + float(s.end.split(':')[2])) for s in subs]
                final_vid = CompositeVideoClip([final_vid] + txts)
            
            final_vid.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac", logger=None)
            status.update(label="✅ Render Complete!", state="complete", expanded=True)
            st.video("final.mp4")
            with open("final.mp4", "rb") as file: st.download_button("💾 Download Video", file, "Video.mp4", "video/mp4")
        except Exception as e:
            status.update(label="❌ Render Failed", state="error")
            st.error(f"Error Details: {str(e)}")


# ==========================================
# PAGE ROUTING (POST-LOGIN)
# ==========================================

# ----------------------------------------
# 🏠 MAIN HUB (NOW SHOWS FULL EXPLANATION)
# ----------------------------------------
if app_mode == "🏠 Main Hub (Home)":
    st.markdown("<h1 style='text-align: center; font-size: 50px;'>Welcome to <span class='brand-text'>AutoX</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 20px; color: #606060;'>The Ultimate AI Workforce for Creators. See how it works below.</p>", unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)
    
    colA, colB = st.columns(2)
    with colA:
        st.markdown("<div class='feature-card'><h3 class='yt-text'>YouTube AutoX (PRO)</h3><p>Generates long-form 16:9 cinematic videos with AI voiceovers, subtitles, and smooth transitions.</p></div>", unsafe_allow_html=True)
        try: st.image(Image.open("/Users/princekumarsingh/.gemini/antigravity/brain/14257aba-a9b6-466d-94bd-670877ef98ec/yt_demo_mockup_1789319335368.jpg"), use_container_width=True, caption="YouTube AutoX Dashboard")
        except: pass
    with colB:
        st.markdown("<div class='feature-card'><h3 class='insta-text'>Instagram AutoX (PRO)</h3><p>Creates viral 9:16 Reels with trendy captions, fast pacing, and engaging hooks designed for the algorithm.</p></div>", unsafe_allow_html=True)
        try: st.image(Image.open("/Users/princekumarsingh/.gemini/antigravity/brain/14257aba-a9b6-466d-94bd-670877ef98ec/insta_demo_mockup_1789319351037.jpg"), use_container_width=True, caption="Instagram AutoX Viral Reels")
        except: pass
    
    st.info("👈 Use the Sidebar Menu on the left to navigate to the YouTube or Instagram Generation Engines.")

# ----------------------------------------
# 👤 PROFILE & HISTORY
# ----------------------------------------
elif app_mode == "👤 My Profile":
    st.title("👤 My Profile")
    st.markdown(f"**Email:** {st.session_state.logged_in_email}")
    st.markdown(f"**YouTube PRO:** {'✅ Active' if yt_pro_active else '❌ Standard'}")
    st.markdown(f"**Insta PRO:** {'✅ Active' if insta_pro_active else '❌ Standard'}")
    st.markdown(f"**Free Credits Left:** {v_left}")

elif app_mode == "💳 Payment History":
    st.title("💳 Payment History")
    if not (yt_pro_active or insta_pro_active): st.info("No active payments found.")
    if yt_pro_active: st.markdown("<div class='feature-card' style='border-left: 5px solid #FF0000;'><h4>🧾 YouTube PRO Subscription</h4><p>Status: <span style='color:green;'>PAID ✅</span> | Amount: $99.00</p></div>", unsafe_allow_html=True)
    if insta_pro_active: st.markdown("<div class='feature-card' style='border-left: 5px solid #E1306C;'><h4>🧾 Instagram PRO Subscription</h4><p>Status: <span style='color:green;'>PAID ✅</span> | Amount: $99.00</p></div>", unsafe_allow_html=True)

elif app_mode == "🎁 Refer & Earn":
    st.title("🎁 Refer & Earn History")
    my_ref = current_user.get('referral_code') or 'NOT_GENERATED'
    ref_count = current_user.get('referral_count', 0)
    st.markdown(f"<div class='feature-card' style='text-align:center;'><h3>Your Code: <span style='color:#0033FF;'>{my_ref}</span></h3><p>Friends Referred: <b>{ref_count}</b></p></div>", unsafe_allow_html=True)
    share_text = urllib.parse.quote(f"Use my AutoX code for free AI Videos: {my_ref}. https://autox-ai.com")
    c1, c2 = st.columns(2)
    with c1: st.markdown(f"<a href='https://api.whatsapp.com/send?text={share_text}' target='_blank'><button style='background:#25D366; width:100%; border:none; border-radius:10px; color:white; padding:10px;'>💬 WhatsApp</button></a>", unsafe_allow_html=True)
    with c2: st.markdown(f"<a href='https://twitter.com/intent/tweet?text={share_text}' target='_blank'><button style='background:#1DA1F2; width:100%; border:none; border-radius:10px; color:white; padding:10px;'>🐦 Twitter</button></a>", unsafe_allow_html=True)
    
    st.write("### 🎟️ Redeem Code")
    friend_code = st.text_input("Enter Invite Code:")
    if st.button("Redeem Bonus"):
        if friend_code.strip().upper() == my_ref: st.error("You cannot use your own code.")
        else:
            friend_data = get_user_by_referral(friend_code.strip().upper())
            if friend_data:
                add_referral_bonus(st.session_state.logged_in_email, friend_data['email'], v_left, friend_data.get('videos_left',0), friend_data.get('referral_count',0))
                st.success("🎉 Code Redeemed! +1 Free Video!")
                time.sleep(2); st.rerun()
            else: st.error("❌ Invalid Code.")


# ----------------------------------------
# 🎥 YOUTUBE PRO ENGINE
# ----------------------------------------
elif app_mode == "🎥 YouTube AutoX":
    st.markdown("<h2><span class='yt-text'>YouTube AutoX</span> Engine</h2>", unsafe_allow_html=True)
    if not (yt_pro_active or is_admin or v_left > 0):
        st.error("🔒 YouTube PRO Subscription Required")
        st.markdown("<div class='feature-card'><h4>Unlock the Ultimate YouTube Automator</h4><ul><li>16:9 Long Form Generation</li><li>Cinematic Transitions</li><li>Unlimited Rendering</li></ul></div>", unsafe_allow_html=True)
        st.markdown(f"<a href='https://gumroad.com/l/youtube_pro_autox' target='_blank'><button style='width:100%; background:#FF0000; color:white; padding:15px; border-radius:10px; border:none; font-weight:bold;'>💳 BUY YOUTUBE PRO ($99)</button></a>", unsafe_allow_html=True)
    else:
        if yt_pro_active or is_admin: st.success("✅ YouTube PRO Active (Unlimited)")
        else: st.info(f"🎁 Free Trial Active: {v_left} credits left")
        
        agent_topic = st.text_input("🎯 YouTube Video Idea:")
        c1, c2 = st.columns(2)
        with c1: yt_format = st.selectbox("🎥 Video Format:", ["YouTube Standard (16:9)", "YouTube Shorts (9:16)"], key="yt_format")
        with c2: agent_voice = st.selectbox("🗣️ Voice & Language:", list(LANGUAGE_VOICES.keys()), key="yt_voice")
        
        if st.button("Generate YouTube Video", use_container_width=True) and agent_topic:
            is_land = "16:9" in yt_format
            run_video_agent(agent_topic, is_land, agent_voice)
            if not (yt_pro_active or is_admin): update_videos_left(st.session_state.logged_in_email, v_left - 1)

# ----------------------------------------
# 📱 INSTAGRAM PRO ENGINE
# ----------------------------------------
elif app_mode == "📱 Instagram AutoX":
    st.markdown("<h2><span class='insta-text'>Instagram AutoX</span> Engine</h2>", unsafe_allow_html=True)
    if not (insta_pro_active or is_admin or v_left > 0):
        st.error("🔒 Instagram PRO Subscription Required")
        st.markdown("<div class='feature-card'><h4>Unlock the Viral Reels Automator</h4><ul><li>9:16 Portrait Generation</li><li>Fast Pacing & Trendy Fonts</li><li>Unlimited Rendering</li></ul></div>", unsafe_allow_html=True)
        st.markdown(f"<a href='https://gumroad.com/l/insta_pro_autox' target='_blank'><button style='width:100%; background:linear-gradient(45deg, #f09433, #dc2743); color:white; padding:15px; border-radius:10px; border:none; font-weight:bold;'>💳 BUY INSTA PRO ($99)</button></a>", unsafe_allow_html=True)
    else:
        if insta_pro_active or is_admin: st.success("✅ Instagram PRO Active (Unlimited)")
        else: st.info(f"🎁 Free Trial Active: {v_left} credits left")
        
        agent_topic = st.text_input("🎯 Instagram Reel Idea (9:16):")
        agent_voice = st.selectbox("🗣️ Voice & Language:", list(LANGUAGE_VOICES.keys()), key="in_voice")
        if st.button("Generate Viral Reel", use_container_width=True) and agent_topic:
            run_video_agent(agent_topic, False, agent_voice)
            if not (insta_pro_active or is_admin): update_videos_left(st.session_state.logged_in_email, v_left - 1)

# --- FOOTER ---
st.write("<br><br><br>", unsafe_allow_html=True)
st.markdown("""
    <div class='footer'>
        <p>AutoX AI Inc. © 2026 | Created by Prince</p>
        <a href='https://www.instagram.com/rajputbusyguy?stkn=MTkyaG1zeWZzcWlpMw==' target='_blank'>Official Instagram</a>
    </div>
""", unsafe_allow_html=True)
