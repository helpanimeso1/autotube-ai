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

def get_user_by_referral(ref_code):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?referral_code=eq.{ref_code}"
    res = requests.get(url, headers=get_sb_headers())
    if res.status_code == 200 and len(res.json()) > 0:
        return res.json()[0]
    return None

def create_user(email, password):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers"
    # Create unique referral code
    clean_email = email.split('@')[0][:4].upper()
    random_str = ''.join(random.choices(string.digits, k=4))
    ref_code = f"AUTOX-{clean_email}-{random_str}"
    
    data = {
        "email": email, 
        "password": password, 
        "has_paid": False,
        "videos_left": 1,  # FREE TRIAL: 1 Free Video
        "referral_code": ref_code
    }
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

def update_videos_left(email, new_count):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?email=eq.{email}"
    data = {"videos_left": new_count}
    requests.patch(url, headers=get_sb_headers(), json=data)

# --- EMAIL OTP FUNCTION ---
def send_otp_email(recipient_email, otp_code, purpose="login"):
    sender_email = ADMIN_EMAIL
    sender_password = st.secrets.get("GMAIL_PASSWORD", "").replace(" ", "") 
    
    msg_body = f"Hello,\n\nYour AutoX verification code is: {otp_code}\n\nDo not share this code with anyone.\n\nThanks,\nAutoX System"
    if purpose == "signup":
         msg_body = f"Welcome to AutoX!\n\nYour account verification code is: {otp_code}\n\nEnter this to activate your account."
         
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
    except Exception as e:
        print("Email Error:", e)
        return False

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)


# --- UI SETUP & CSS ---
st.set_page_config(page_title="AutoX App Portal", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700;900&display=swap');
        
        /* AutoX Premium Light Theme */
        .stApp {
            background-color: #FAFAFA !important;
            color: #111111 !important;
            font-family: 'Roboto', sans-serif;
        }
        
        /* Headings */
        h1, h2, h3, h4 { color: #111111 !important; font-weight: 900; letter-spacing: -0.5px; }
        
        /* AutoX Brand Gradient Text */
        .brand-text {
            background: linear-gradient(90deg, #FF0055 0%, #0033FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
        }
        
        /* Sidebar Light */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #EBEBEB;
            box-shadow: 2px 0px 15px rgba(0,0,0,0.02);
        }
        [data-testid="stSidebar"] * { color: #111111 !important; }
        
        /* Premium Buttons */
        .stButton>button {
            background: linear-gradient(90deg, #111111 0%, #333333 100%) !important;
            color: #FFFFFF !important;
            border: none;
            border-radius: 8px;
            font-weight: 700;
            padding: 12px 24px;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        
        /* Inputs */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            background-color: #FFFFFF !important;
            color: #111111 !important;
            border: 1px solid #E0E0E0 !important;
            border-radius: 8px;
            font-size: 16px;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
        }
        .stTextInput input:focus { border-color: #0033FF !important; }
        
        /* Layout Cards */
        .feature-card {
            background: #FFFFFF;
            border: 1px solid #EBEBEB;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
            margin-bottom: 16px;
        }
        ::placeholder { color: #999999 !important; }
        
        .referral-box {
            border: 2px dashed #0033FF;
            padding: 20px;
            border-radius: 10px;
            background: #f0f4ff;
            text-align: center;
            margin: 20px 0;
        }
    </style>
""", unsafe_allow_html=True)


# --- ADVANCED VIDEO EDITING HELPERS ---
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


# --- AUTOX PORTAL (LOGIN SCREEN) ---
if 'logged_in_email' not in st.session_state:
    st.session_state.logged_in_email = None
    st.session_state.has_paid = False
    st.session_state.otp_sent = False
    st.session_state.expected_otp = None
    st.session_state.auth_purpose = None

if not st.session_state.logged_in_email:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("<br><br><br>", unsafe_allow_html=True)
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
                    if email_input.strip() == ADMIN_EMAIL:
                        st.info("👑 **CEO RECOGNIZED.** Welcome Boss.")
                        new_pwd = st.text_input("Create Master Password", type="password")
                        if st.button("Initialize CEO Account", use_container_width=True):
                            if len(new_pwd) < 4:
                                st.warning("Password must be at least 4 chars.")
                            else:
                                with st.spinner("Setting up CEO account..."):
                                    if not user:
                                        user = create_user(email_input.strip(), new_pwd)
                                    else:
                                        update_user_password(email_input.strip(), new_pwd)
                                    st.session_state.logged_in_email = email_input.strip()
                                    st.session_state.has_paid = True
                                    st.rerun()
                    else:
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
                        if st.button("Login", use_container_width=True):
                            if pwd_input == user['password']:
                                st.session_state.logged_in_email = user['email']
                                if user['email'] == ADMIN_EMAIL:
                                    st.session_state.has_paid = True
                                else:
                                    st.session_state.has_paid = user['has_paid']
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
                                if user['email'] == ADMIN_EMAIL:
                                    st.session_state.has_paid = True
                                else:
                                    st.session_state.has_paid = user['has_paid']
                                st.session_state.otp_sent = False
                                st.rerun()
                            else:
                                st.error("Wrong code.")
    st.stop()


# --- GET LATEST USER DATA ON EVERY REFRESH ---
current_user_data = get_user(st.session_state.logged_in_email)
if current_user_data:
    st.session_state.has_paid = current_user_data.get('has_paid', False)


# --- SIDEBAR: NAVIGATION ---
with st.sidebar:
    st.markdown("<h2><span class='brand-text'>AutoX</span></h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #606060 !important; font-size: 14px;'>👤 {st.session_state.logged_in_email}</p>", unsafe_allow_html=True)
    
    if st.session_state.has_paid or st.session_state.logged_in_email == ADMIN_EMAIL:
        st.markdown("<span style='background:#FF0055; color:white; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:bold;'>PRO ACCOUNT</span>", unsafe_allow_html=True)
    else:
        v_left = current_user_data.get('videos_left', 0) if current_user_data else 0
        st.markdown(f"<span style='background:#E0E0E0; color:#333; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:bold;'>FREE PLAN ({v_left} Credits)</span>", unsafe_allow_html=True)
        
    st.write("<br>", unsafe_allow_html=True)
    if st.button("Sign out", use_container_width=True):
        st.session_state.logged_in_email = None
        st.rerun()
    st.divider()
    
    if st.session_state.logged_in_email == ADMIN_EMAIL:
        st.write("### 👑 Executive (CEO)")
        admin_mode = st.radio("Admin", ["None", "📊 Revenue & Users"], label_visibility="collapsed")
    else:
        admin_mode = "None"
        
    st.write("### 👤 Account")
    profile_mode = st.radio("Profile", ["None", "👤 My Profile & Billing", "🎁 Refer & Earn (Free Videos)"], label_visibility="collapsed")
        
    st.write("### 💎 AutoX Pro")
    agent_mode = st.radio("Agent", ["None", "🤖 AutoX Video Agent"], label_visibility="collapsed")
    
    st.write("### 🏠 Hub")
    dashboard_btn = st.radio("Dashboard", ["None", "App Dashboard"], label_visibility="collapsed")
    
    st.write("### 🎥 Modular Tools")
    media_mode = st.radio("Media", ["None", "🎬 Auto Shorts (Free)", "🖼️ Thumbnails"], label_visibility="collapsed")
    
    st.write("### ✍️ Text Tools")
    content_mode = st.radio("Content", ["None", "✍️ Blogs & Posts", "📱 Social Sync"], label_visibility="collapsed")
    
    st.divider()
    st.caption("AutoX AI Inc. 2026")


app_mode = "App Dashboard"
for mode in [admin_mode, profile_mode, agent_mode, dashboard_btn, media_mode, content_mode]:
    if mode != "None":
        app_mode = mode

# --- SECURE API KEYS ---
try:
    user_gemini_key = st.secrets["GEMINI_API_KEY"]
    user_pexels_key = st.secrets["PEXELS_API_KEY"]
except:
    st.error("System configuration error. Keys missing.")
    st.stop()

def check_keys():
    genai.configure(api_key=user_gemini_key)
    return genai.GenerativeModel('gemini-3.6-flash')


# ==========================================
# PAGE: ADMIN DASHBOARD
# ==========================================
if app_mode == "📊 Revenue & Users":
    st.title("📊 CEO Dashboard")
    st.markdown("Manage your AutoX platform.")
    st.divider()
    
    users = get_all_users()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Users", len(users))
    c2.metric("Pro Subscribers", len([u for u in users if u.get('has_paid')]))
    c3.metric("Estimated Revenue", f"${len([u for u in users if u.get('has_paid')]) * 99}")
    
    st.write("### ⚙️ Manual Access Override")
    st.caption("Use this to manually grant access until Stripe Webhooks are connected.")
    if not users:
        st.write("No users found.")
    else:
        user_emails = [u['email'] for u in users]
        selected_user = st.selectbox("Select User Email:", user_emails)
        current_status = next((u.get('has_paid') for u in users if u['email'] == selected_user), False)
        
        st.info(f"Current Status: **{'✅ PRO Active' if current_status else '❌ Standard Account'}**")
        
        new_status = st.radio("Change Status To:", [True, False], format_func=lambda x: "Grant PRO Access" if x else "Revoke PRO Access")
        if st.button("Save Changes"):
            with st.spinner("Updating database..."):
                update_user_access(selected_user, new_status)
                if selected_user == st.session_state.logged_in_email:
                    st.session_state.has_paid = new_status
                st.success("Access updated successfully!")
                time.sleep(1)
                st.rerun()

# ==========================================
# PAGE: USER PROFILE & BILLING
# ==========================================
elif app_mode == "👤 My Profile & Billing":
    st.title("👤 My Profile & Billing")
    st.markdown("Manage your account details and payment history.")
    st.divider()
    
    st.write(f"**Email Address:** {st.session_state.logged_in_email}")
    
    if st.session_state.logged_in_email == ADMIN_EMAIL:
        st.success("👑 **Account Level:** CEO / Admin (Unlimited Access)")
        st.write("### 🧾 Payment History")
        st.info("No billing history. Admin accounts do not require payments.")
        
    elif st.session_state.has_paid:
        st.success("✅ **Account Level:** AutoX PRO (Lifetime Access)")
        st.write("### 🧾 Payment History")
        st.markdown("""
        <div class='feature-card'>
            <h4>Invoice #INV-2026-AUT</h4>
            <p><strong>Item:</strong> AutoX Pro Lifetime License</p>
            <p><strong>Status:</strong> <span style='color:green;'>PAID ✅</span></p>
            <p><strong>Amount:</strong> $99.00</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        v_left = current_user_data.get('videos_left', 0) if current_user_data else 0
        st.warning(f"🔒 **Account Level:** Standard (Free) - {v_left} Video Credits Left")
        st.write("### 🧾 Payment History")
        st.info("No payment history found. Upgrade to PRO to unlock unlimited features.")
        payment_link = st.secrets.get("PAYMENT_LINK", "https://razorpay.com/")
        st.markdown(f"<a href='{payment_link}' target='_blank'><button style='padding:10px 20px; background:#FF0055; color:white; border:none; border-radius:5px;'>💳 Upgrade to PRO Now</button></a>", unsafe_allow_html=True)

# ==========================================
# PAGE: REFER & EARN (VIRAL GROWTH)
# ==========================================
elif app_mode == "🎁 Refer & Earn (Free Videos)":
    st.title("🎁 Refer & Earn")
    st.markdown("Invite your friends to AutoX and get **Free AI Videos** for every successful sign-up!")
    st.divider()
    
    my_ref_code = current_user_data.get('referral_code', 'NOT_GENERATED') if current_user_data else 'NOT_GENERATED'
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class='referral-box'>
            <h3>Your Unique Invite Code:</h3>
            <h1 style='color:#0033FF; font-family:monospace;'>{my_ref_code}</h1>
            <p>Share this code with your network. When they redeem it, you both get <b>+1 Free Video Credit!</b></p>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.write("### 🎟️ Redeem a Friend's Code")
        st.info("Did a friend invite you? Enter their code below to get a bonus free video.")
        friend_code = st.text_input("Enter Invite Code:", placeholder="e.g., AUTOX-JOHN-1234")
        
        if st.button("Redeem Bonus Video"):
            if friend_code.strip().upper() == my_ref_code:
                st.error("You cannot use your own referral code.")
            else:
                with st.spinner("Checking code..."):
                    friend_data = get_user_by_referral(friend_code.strip().upper())
                    if friend_data:
                        # Add +1 to me
                        my_new_count = current_user_data.get('videos_left', 0) + 1
                        update_videos_left(st.session_state.logged_in_email, my_new_count)
                        # Add +1 to friend
                        friend_new_count = friend_data.get('videos_left', 0) + 1
                        update_videos_left(friend_data['email'], friend_new_count)
                        
                        st.success("🎉 Code Redeemed! You and your friend both got +1 Free Video!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Invalid Code. Please check and try again.")


# ==========================================
# PAGE: AUTOX VIDEO AGENT (PRO) 
# ==========================================
elif app_mode == "🤖 AutoX Video Agent":
    st.title("🤖 AutoX Video Agent")
    
    # FREE TRIAL & PRO LOGIC
    v_left = current_user_data.get('videos_left', 0) if current_user_data else 0
    is_admin = (st.session_state.logged_in_email == ADMIN_EMAIL)
    has_pro = st.session_state.has_paid
    
    is_authorized = has_pro or is_admin or (v_left > 0)
    
    if not is_authorized:
        st.error("🔒 **AUTOX PRO REQUIRED (Credits Exhausted)**")
        st.markdown("You have used all your free video credits. Upgrade to PRO for unlimited video generation.")
        st.divider()
        
        st.write("### 💳 Upgrade to PRO")
        payment_link = st.secrets.get("PAYMENT_LINK", "https://razorpay.com/")
        st.markdown(f"<a href='{payment_link}' target='_blank'><button style='width:100%; padding:15px; background:linear-gradient(90deg, #FF0055 0%, #0033FF 100%); color:white; border:none; border-radius:8px; font-weight:bold; font-size:16px;'>💳 UPGRADE NOW - $99</button></a>", unsafe_allow_html=True)
    
    else:
        if has_pro or is_admin:
            st.success("✅ **PRO Active. Unlimited Generation.**")
        else:
            st.info(f"🎁 **Free Trial Active.** You have **{v_left}** free video credit(s) remaining.")
            
        model = check_keys()
        agent_topic = st.text_input("🎯 Video Idea or Topic:")
        
        c1, c2 = st.columns(2)
        with c1:
            agent_format = st.selectbox("🎥 Video Format (YouTube/Insta):", ["YouTube Shorts / Reels (9:16)", "YouTube Standard (16:9)"])
        with c2:
            agent_voice = st.selectbox("🗣️ Voice Actor:", list(LANGUAGE_VOICES.keys()))
            
        is_landscape = "16:9" in agent_format
        width, height = (1280, 720) if is_landscape else (720, 1280)
        orientation = "landscape" if is_landscape else "portrait"
        
        if st.button("Generate Final Video", use_container_width=True) and agent_topic:
            with st.status("🤖 AutoX is crafting your masterpiece...", expanded=True) as status:
                try:
                    lang, code = LANGUAGE_VOICES[agent_voice]
                    st.write("✍️ Writing script & SEO...")
                    prompt = f"Write a 60-second video script about: {agent_topic}. Format: {agent_format}. Language: {lang}. Format EXACTLY like this:\nKEYWORDS: kw1, kw2, kw3\nSCRIPT:\n[script]\nSEO_TITLE:\n[title]\nSEO_TAGS:\n[tags]"
                    res = model.generate_content(prompt).text
                    
                    script = res.split("SCRIPT:")[1].split("SEO_TITLE:")[0].strip()
                    kws = res.split("SCRIPT:")[0].replace("KEYWORDS:", "").strip().split(",")[:3]
                    seo_data = res.split("SEO_TITLE:")[1].strip()
                    
                    st.write("🎙️ Synthesizing Voice...")
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
                    
                    # DEDUCT FREE CREDIT AFTER SUCCESSFUL GENERATION
                    if not (has_pro or is_admin):
                        new_count = v_left - 1
                        update_videos_left(st.session_state.logged_in_email, new_count)
                        st.warning(f"📉 You used 1 Free Credit. You have {new_count} credits left.")
                    
                    st.divider()
                    st.subheader("🎉 Your Video is Ready")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.video(final_path)
                        with open(final_path, "rb") as file:
                            st.download_button("💾 Download Video", file, "Final_Video.mp4", "video/mp4")
                            
                        # THE DIRECT UPLOAD ILLUSION BUTTON
                        if st.button("🚀 Publish to Instagram/YouTube"):
                            st.info("ℹ️ **Beta Feature:** We are currently awaiting final API approval from Google & Meta. Please download your video and upload it manually for now.")
                    with c2:
                        st.image("agent_thumb.jpg")
                        with open("agent_thumb.jpg", "rb") as file:
                            st.download_button("💾 Download Thumbnail", file, "Thumbnail.jpg", "image/jpeg")
                    with c3:
                        st.info(seo_data)
                        st.download_button("💾 Download SEO", seo_data, "SEO_Data.txt")
                        
                except Exception as e:
                    status.update(label="❌ Render Failed", state="error")
                    st.error(e)

# ==========================================
# PAGE: DASHBOARD 
# ==========================================
elif app_mode == "App Dashboard":
    st.title("⚡ AutoX Hub")
    st.markdown("Welcome to the AutoX ecosystem. Select a module to begin.")
    
    st.write("### 🛠️ Active Modules")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='feature-card'><h4>🤖 AutoX Video Agent (Pro)</h4><p style='color:#606060; font-size:14px;'>Generates full 16:9 YouTube videos or 9:16 Shorts/Reels with advanced transitions and subtitles instantly.</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='feature-card'><h4>🎬 Auto Shorts</h4><p style='color:#606060; font-size:14px;'>Basic text-to-video conversion.</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='feature-card'><h4>🖼️ Thumbnails</h4><p style='color:#606060; font-size:14px;'>Generate hyper-realistic 8k thumbnails.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='feature-card'><h4>✍️ Blogs & Posts</h4><p style='color:#606060; font-size:14px;'>SEO-optimized long-form articles.</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='feature-card'><h4>📱 Social Sync</h4><p style='color:#606060; font-size:14px;'>Automated Twitter/Instagram copy.</p></div>", unsafe_allow_html=True)
