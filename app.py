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
    "English (US)": ("English", "en-US-ChristopherNeural"),
    "English (UK)": ("English", "en-GB-RyanNeural"),
    "Hindi (India)": ("Hindi", "hi-IN-MadhurNeural"),
    "Spanish (Spain)": ("Spanish", "es-ES-AlvaroNeural"),
    "French (France)": ("French", "fr-FR-HenriNeural"),
    "German (Germany)": ("German", "de-DE-ConradNeural"),
    "Japanese (Japan)": ("Japanese", "ja-JP-KeitaNeural")
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
    if res.status_code == 200 and len(res.json()) > 0: return res.json()[0]
    return None

def create_user(email, password):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers"
    ref_code = f"AUTOX-{email.split('@')[0][:4].upper()}-{''.join(random.choices(string.digits, k=4))}"
    data = {"email": email, "password": password, "has_paid": False, "videos_left": 1, "referral_code": ref_code, "yt_pro": False, "insta_pro": False, "referral_count": 0}
    requests.post(url, headers=get_sb_headers(), json=data)
    return data

def update_user_password(email, new_password):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?email=eq.{email}"
    requests.patch(url, headers=get_sb_headers(), json={"password": new_password})

def is_valid_email(email): return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email)

def update_videos_left(email, new_count):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?email=eq.{email}"
    requests.patch(url, headers=get_sb_headers(), json={"videos_left": new_count})

def send_otp_email(recipient_email, otp_code, purpose="login"):
    sender_email = ADMIN_EMAIL
    sender_password = st.secrets.get("GMAIL_PASSWORD", "").replace(" ", "") 
    msg = MIMEText(f"Your AutoX verification code is: {otp_code}")
    msg['Subject'] = 'AutoX - Security Code'
    msg['From'] = f"AutoX <{sender_email}>"
    msg['To'] = recipient_email
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except: return False


# --- JAI PORTAL CLONE CSS (PREMIUM DARK) ---
st.set_page_config(page_title="AutoX Agent - Video Production", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
        
        /* Hide Streamlit UI to protect privacy and remove GitHub link */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Exact JaiPortal Deep Dark Theme */
        .stApp { 
            background: radial-gradient(ellipse 80% 50% at 50% -20%, rgba(139, 92, 246, 0.12) 0%, transparent 50%),
                        radial-gradient(ellipse 60% 40% at 90% 100%, rgba(236, 72, 153, 0.06) 0%, transparent 50%),
                        linear-gradient(180deg, #0a0a14 0%, #0d0d1a 50%, #0a0a14 100%) !important;
            color: #ffffff !important; 
            font-family: 'Inter', sans-serif; 
        }
        
        h1, h2, h3, h4 { color: #ffffff !important; font-weight: 700; letter-spacing: -0.02em; }
        
        .hero-title { 
            font-size: 3.5rem !important; 
            font-weight: 900 !important; 
            background: linear-gradient(to right, #ffffff, #a1a1aa); 
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent; 
            line-height: 1.1; 
            margin-bottom: 20px;
        }
        .hero-subtitle { font-size: 1.25rem; color: #a1a1aa; max-width: 700px; margin: 0 auto; line-height: 1.6; }
        
        /* Glassmorphism Cards */
        .jai-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 24px;
            transition: all 0.2s ease-in-out;
            height: 100%;
        }
        .jai-card:hover { 
            background: rgba(255, 255, 255, 0.08); 
            border-color: rgba(139, 92, 246, 0.5);
            box-shadow: 0 12px 40px rgba(139, 92, 246, 0.2); 
            transform: translateY(-2px); 
        }
        .jai-card h3 { font-size: 1.25rem !important; margin-bottom: 10px; color: #ffffff; }
        .jai-card p { color: #a1a1aa; font-size: 0.95rem; line-height: 1.5; }
        
        /* Top Navigation */
        .nav-bar { display: flex; justify-content: space-between; align-items: center; padding: 20px 40px; border-bottom: 1px solid rgba(255,255,255,0.1); background: rgba(10, 10, 20, 0.8); backdrop-filter: blur(10px); }
        .nav-logo { font-size: 1.5rem; font-weight: 900; color: #fff; text-decoration: none; }
        
        /* Inputs & Buttons */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] { 
            background-color: rgba(255, 255, 255, 0.05) !important; color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 8px; 
        }
        .stButton>button { 
            background: rgba(255, 255, 255, 0.1) !important; color: #ffffff !important; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 8px; font-weight: 600; padding: 10px 24px; transition: 0.2s;
        }
        .stButton>button:hover { background: rgba(255, 255, 255, 0.15) !important; }
        
        /* Gradient Button exact match */
        .btn-primary>button { 
            background: linear-gradient(to right, #f97316, #ef4444, #ec4899) !important; 
            color: #ffffff !important; 
            border: none;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
        }
        .btn-primary>button:hover { 
            background: linear-gradient(to right, #fb923c, #f87171, #f472b6) !important; 
            box-shadow: 0 4px 15px rgba(249, 115, 22, 0.4);
        }
        
        .badge { display: inline-block; padding: 4px 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 15px;}
        
        /* Footer */
        .custom-footer { border-top: 1px solid rgba(255, 255, 255, 0.1); padding: 40px 0; margin-top: 80px; text-align: center; color: #71717a; font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)


# --- STATE MANAGEMENT ---
if 'logged_in_email' not in st.session_state:
    st.session_state.logged_in_email = None
    st.session_state.show_login = False
    st.session_state.otp_sent = False
    st.session_state.expected_otp = None


# ==========================================
# PAGE 1: JAI PORTAL CLONE (LANDING PAGE)
# ==========================================
if not st.session_state.logged_in_email:
    
    # Custom Navigation Bar
    col_nav1, col_nav2, col_nav3 = st.columns([1, 4, 1])
    with col_nav1:
        st.markdown("<div style='padding-top:10px; font-size:24px; font-weight:900;'>⚡ AutoX</div>", unsafe_allow_html=True)
    with col_nav3:
        if st.button("Login / Sign Up"):
            st.session_state.show_login = not st.session_state.show_login
            st.rerun()

    # --- LOGIN MODAL (IF TOGGLED) ---
    if st.session_state.show_login:
        st.write("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1.5, 1])
        with c2:
            st.markdown("<div class='jai-card'>", unsafe_allow_html=True)
            st.markdown("<h3>Welcome to AutoX</h3><p>Sign in to your AI workspace.</p>", unsafe_allow_html=True)
            email_input = st.text_input("Email Address")
            
            if email_input:
                user = get_user(email_input.strip())
                if not user:
                    st.info("New account will be created.")
                    if not st.session_state.otp_sent:
                        if st.button("Send Verification Code"):
                            otp = str(random.randint(100000, 999999))
                            send_otp_email(email_input.strip(), otp, "signup")
                            st.session_state.otp_sent = True
                            st.session_state.expected_otp = otp
                            st.rerun()
                    else:
                        st.success("Code sent!")
                        otp_in = st.text_input("Enter Code")
                        pwd_in = st.text_input("Create Password", type="password")
                        if st.button("Create Account"):
                            if otp_in == st.session_state.expected_otp and len(pwd_in) >= 4:
                                create_user(email_input.strip(), pwd_in)
                                st.session_state.logged_in_email = email_input.strip()
                                st.session_state.show_login = False
                                st.rerun()
                            else: st.error("Invalid Code or Password.")
                else:
                    pwd_in = st.text_input("Password", type="password")
                    if st.button("Log In"):
                        if pwd_in == user['password']:
                            st.session_state.logged_in_email = email_input.strip()
                            st.session_state.show_login = False
                            st.rerun()
                        else: st.error("Incorrect Password.")
            st.markdown("</div>", unsafe_allow_html=True)
            st.stop()


    # --- HERO SECTION ---
    st.write("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'><span class='badge'>AI Video Agent</span></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='hero-title' style='text-align: center;'>AI YouTube Agent<br>Video Production</h1>", unsafe_allow_html=True)
    st.markdown("<p class='hero-subtitle' style='text-align: center;'>Automate your YouTube channel with AI. Video creation, thumbnail generation, and script writing on autopilot.</p>", unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)
    c_btn1, c_btn2, c_btn3 = st.columns([1.5, 1, 1.5])
    with c_btn2:
        st.markdown("<div class='btn-primary'>", unsafe_allow_html=True)
        if st.button("Start Automating YouTube", use_container_width=True):
            st.session_state.show_login = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#71717a; font-size:12px; margin-top:10px;'>No Credit Card Required • Free Trial Included</p>", unsafe_allow_html=True)

    st.write("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="display: flex; justify-content: center; margin-bottom: 60px;">
            <div style="position: relative; width: 100%; max-width: 800px; padding-bottom: 45%; border-radius: 16px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(139, 92, 246, 0.25); border: 1px solid rgba(255,255,255,0.1); background: #000;">
                <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" src="https://www.youtube.com/embed/LXb3EKWsInQ?autoplay=1&mute=1&loop=1&playlist=LXb3EKWsInQ&controls=0&rel=0" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- FEATURES GRID (EXACT JAI COPY) ---
    st.markdown("<h3 style='text-align:center; margin-bottom: 40px;'>Professional YouTube content created automatically</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='jai-card'>
            <h3>🧠 AI Tutorial Creator</h3>
            <p>Step-by-step tutorials with AI voiceover and cinematic footage.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class='jai-card' style='margin-top:20px;'>
            <h3>📦 Product Review Generator</h3>
            <p>Professional product reviews with AI narration and feature highlights.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='jai-card'>
            <h3>🎮 Gaming Commentary AI</h3>
            <p>Automated gaming style videos with fast-paced edits.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class='jai-card' style='margin-top:20px;'>
            <h3>🏆 Top 10 Compilation</h3>
            <p>Ranking videos with AI storytelling and dynamic transitions.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='jai-card'>
            <h3>📱 Insta Viral Reels</h3>
            <p>9:16 portrait short-form content optimized for maximum engagement.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class='jai-card' style='margin-top:20px;'>
            <h3>📈 Content Optimization</h3>
            <p>Auto-generates SEO titles, descriptions, and tags for discovery.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>Everything you need to know about YouTube Agent</h3>", unsafe_allow_html=True)
    
    faq_c1, faq_c2 = st.columns(2)
    with faq_c1:
        st.markdown("<div class='jai-card'><h4>Do I need editing skills?</h4><p>YouTube Agent uses AI to generate complete videos from scripts, including visuals, voiceover, music, and editing. It handles everything from ideation to final render.</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='jai-card' style='margin-top:20px;'><h4>Are thumbnails included?</h4><p>Yes! Our AI creates eye-catching, click-worthy thumbnails optimized for maximum CTR. It analyzes trending designs and applies proven conversion strategies.</p></div>", unsafe_allow_html=True)
    with faq_c2:
        st.markdown("<div class='jai-card'><h4>What about SEO?</h4><p>Absolutely. YouTube Agent automatically generates SEO-optimized titles, descriptions, and tags to maximize your video's discoverability and ranking.</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='jai-card' style='margin-top:20px;'><h4>Can I choose the voice?</h4><p>Yes! Choose from multiple premium global AI voices, languages, and tones.</p></div>", unsafe_allow_html=True)

    # Footer
    st.markdown("""
        <div class='custom-footer'>
            © 2026 AutoX Portal. All rights reserved. | Created by Prince<br>
            <a href='https://www.instagram.com/rajputbusyguy?stkn=MTkyaG1zeWZzcWlpMw==' target='_blank' style='color:#71717a;'>Instagram</a>
        </div>
    """, unsafe_allow_html=True)
    st.stop()


# ==========================================
# POST-LOGIN: DASHBOARD (JAI STYLE)
# ==========================================
current_user = get_user(st.session_state.logged_in_email)
if not current_user: st.stop()

yt_pro_active = current_user.get('yt_pro', False)
insta_pro_active = current_user.get('insta_pro', False)
v_left = current_user.get('videos_left', 0)
is_admin = (st.session_state.logged_in_email == ADMIN_EMAIL)
if is_admin: yt_pro_active, insta_pro_active = True, True

# Top Nav inside App
c1, c2 = st.columns([4, 1])
with c1: st.markdown("<h2>⚡ AutoX Portal</h2>", unsafe_allow_html=True)
with c2: 
    if st.button("Logout", key="logout_btn"): 
        st.session_state.logged_in_email = None
        st.rerun()
st.divider()


# --- CORE GENERATION ENGINE (UPGRADED WITH TEMPLATES) ---
def run_video_agent(agent_topic, template, is_landscape, agent_voice):
    try: user_gemini_key = st.secrets["GEMINI_API_KEY"]; user_pexels_key = st.secrets["PEXELS_API_KEY"]
    except: st.error("API Keys missing in secrets."); return
    genai.configure(api_key=user_gemini_key); model = genai.GenerativeModel('gemini-3.6-flash')
    
    width, height = (1280, 720) if is_landscape else (720, 1280)
    
    with st.status("⚙️ AutoX AI Agent is processing...", expanded=True) as status:
        try:
            lang, code = LANGUAGE_VOICES[agent_voice]
            
            # Dynamic Prompting based on JAI templates
            st.write(f"✍️ Writing {template} script & SEO...")
            base_prompt = f"Write a 60-second video script about: {agent_topic}. Format: {'16:9' if is_landscape else '9:16'}. Language: {lang}. "
            
            if template == "AI Tutorial": base_prompt += "Make it a step-by-step educational tutorial."
            elif template == "Product Review": base_prompt += "Make it a product review highlighting pros, cons, and a final verdict."
            elif template == "Top 10 Compilation": base_prompt += "Make it a fast-paced Top 5 or Top 10 ranking list."
            elif template == "Gaming Commentary": base_prompt += "Make it sound like an energetic gaming streamer commentary."
            elif template == "Vlog Style Creator": base_prompt += "Make it sound like a personal, cinematic daily vlog storytelling script."
            
            base_prompt += "\nFormat EXACTLY like this:\nKEYWORDS: kw1, kw2\nSCRIPT:\n[script]\nSEO_TITLE:\n[title]\nSEO_TAGS:\n[tags]"
            
            res = model.generate_content(base_prompt).text
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

            st.write("🎞️ Rendering Final Video (Applying Auto-Subtitles)...")
            vis = concatenate_videoclips(videos, padding=-0.5, method="compose") if len(videos)>1 else videos[0]
            aclip = AudioFileClip("a.mp3")
            vis = vis.fx(vfx.loop, duration=aclip.duration) if vis.duration < aclip.duration else vis.subclip(0, aclip.duration)
            final_vid = vis.set_audio(aclip)
            
            if os.path.exists("a.vtt"):
                subs = webvtt.read("a.vtt")
                txts = [TextClip(s.text, fontsize=int(width/15), color='white', stroke_color='black', stroke_width=3, method='caption', size=(width-100, None)).set_position('center').set_start(int(s.start.split(':')[0])*3600 + int(s.start.split(':')[1])*60 + float(s.start.split(':')[2])).set_end(int(s.end.split(':')[0])*3600 + int(s.end.split(':')[1])*60 + float(s.end.split(':')[2])) for s in subs]
                final_vid = CompositeVideoClip([final_vid] + txts)
            
            final_vid.write_videofile("final.mp4", fps=24, codec="libx264", audio_codec="aac", logger=None)
            
            st.write("🖼️ Generating Thumbnail...")
            thumb_prompt = model.generate_content(f"Create an 8k image prompt for a video thumbnail about: '{agent_topic}'. NO TEXT.").text.strip()
            with open("thumb.jpg", "wb") as f: f.write(requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(thumb_prompt)}?width=1280&height=720&nologo=true").content)
            
            status.update(label="✅ Video Ready for YouTube/Insta!", state="complete", expanded=True)
            
            c1, c2 = st.columns(2)
            with c1: 
                st.video("final.mp4")
                with open("final.mp4", "rb") as file: st.download_button("💾 Download Video", file, "Video.mp4", "video/mp4")
            with c2: 
                st.image("thumb.jpg", caption="Auto-Generated Thumbnail")
                with open("thumb.jpg", "rb") as file: st.download_button("💾 Download Thumbnail", file, "Thumb.jpg", "image/jpeg")
        except Exception as e:
            status.update(label="❌ Agent Error", state="error")
            st.error(f"Error Details: {str(e)}")


# --- MAIN APP ROUTING ---
st.sidebar.markdown("### Agent Models")
app_mode = st.sidebar.radio("Select Model", ["YouTube Tools", "Instagram Tools", "My Account", "Pricing"])

if app_mode == "YouTube Tools":
    st.markdown("<div class='jai-card'>", unsafe_allow_html=True)
    st.markdown("<h3>YouTube Video Agent</h3><p>Automate long-form and short-form YouTube content.</p><br>", unsafe_allow_html=True)
    
    if not (yt_pro_active or is_admin or v_left > 0):
        st.error("🔒 Enterprise Access Required (YouTube PRO)")
        st.markdown(f"<a href='https://gumroad.com/l/youtube_pro_autox' target='_blank'><button style='background:#ffffff; color:#09090b; padding:10px 20px; border-radius:8px; border:none; font-weight:bold;'>Upgrade to PRO ($99)</button></a>", unsafe_allow_html=True)
    else:
        c1, c2 = st.columns([2, 1])
        with c1: agent_topic = st.text_input("Video Topic / Prompt")
        with c2: agent_template = st.selectbox("Agent Template", ["Custom Idea", "AI Tutorial", "Product Review", "Top 10 Compilation", "Gaming Commentary", "Vlog Style Creator"])
        
        c3, c4 = st.columns(2)
        with c3: yt_format = st.selectbox("Video Format", ["Standard (16:9)", "Shorts (9:16)"])
        with c4: agent_voice = st.selectbox("Global Voice", list(LANGUAGE_VOICES.keys()))
        
        st.markdown("<div class='btn-primary'>", unsafe_allow_html=True)
        if st.button("Generate Video", use_container_width=True) and agent_topic:
            is_land = "16:9" in yt_format
            run_video_agent(agent_topic, agent_template, is_land, agent_voice)
            if not (yt_pro_active or is_admin): update_videos_left(st.session_state.logged_in_email, v_left - 1)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif app_mode == "Instagram Tools":
    st.markdown("<div class='jai-card'>", unsafe_allow_html=True)
    st.markdown("<h3>Instagram Viral Reels Agent</h3><p>Automate 9:16 portrait content for Instagram growth.</p><br>", unsafe_allow_html=True)
    
    if not (insta_pro_active or is_admin or v_left > 0):
        st.error("🔒 Enterprise Access Required (Instagram PRO)")
        st.markdown(f"<a href='https://gumroad.com/l/insta_pro_autox' target='_blank'><button style='background:#ffffff; color:#09090b; padding:10px 20px; border-radius:8px; border:none; font-weight:bold;'>Upgrade to PRO ($99)</button></a>", unsafe_allow_html=True)
    else:
        agent_topic = st.text_input("Reel Topic / Hook")
        agent_voice = st.selectbox("Voiceover", list(LANGUAGE_VOICES.keys()))
        
        st.markdown("<div class='btn-primary'>", unsafe_allow_html=True)
        if st.button("Generate Viral Reel", use_container_width=True) and agent_topic:
            run_video_agent(agent_topic, "Custom Idea", False, agent_voice)
            if not (insta_pro_active or is_admin): update_videos_left(st.session_state.logged_in_email, v_left - 1)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif app_mode == "My Account":
    st.markdown("<div class='jai-card'>", unsafe_allow_html=True)
    st.markdown("<h3>Profile & Billing</h3>", unsafe_allow_html=True)
    st.write(f"**Email:** {st.session_state.logged_in_email}")
    st.write(f"**YouTube PRO:** {'Active' if yt_pro_active else 'Inactive'}")
    st.write(f"**Insta PRO:** {'Active' if insta_pro_active else 'Inactive'}")
    st.write(f"**Credits Remaining:** {v_left}")
    st.divider()
    st.markdown("<h3>Refer & Earn</h3>", unsafe_allow_html=True)
    my_ref = current_user.get('referral_code', 'N/A')
    st.write(f"Your Code: **{my_ref}**")
    friend_code = st.text_input("Enter a friend's code:")
    if st.button("Redeem Code"):
        if friend_code.strip().upper() == my_ref: st.error("Cannot use own code.")
        else:
            friend_data = get_user_by_referral(friend_code.strip().upper())
            if friend_data:
                add_referral_bonus(st.session_state.logged_in_email, friend_data['email'], v_left, friend_data.get('videos_left',0), friend_data.get('referral_count',0))
                st.success("Code Redeemed!")
                time.sleep(2); st.rerun()
            else: st.error("Invalid Code.")
    st.markdown("</div>", unsafe_allow_html=True)

elif app_mode == "Pricing":
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='jai-card'><h3>YouTube PRO</h3><h2 style='font-size:30px;'>$99 <span style='font-size:14px; color:#a1a1aa;'>lifetime</span></h2><p>Unlimited 16:9 cinematic generations.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='jai-card'><h3>Instagram PRO</h3><h2 style='font-size:30px;'>$99 <span style='font-size:14px; color:#a1a1aa;'>lifetime</span></h2><p>Unlimited 9:16 viral reels generations.</p></div>", unsafe_allow_html=True)
