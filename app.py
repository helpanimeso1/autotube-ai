import streamlit as st
import subprocess, os, requests, google.generativeai as genai, webvtt, urllib.parse, smtplib, random, time, re, string
from email.mime.text import MIMEText
from PIL import Image
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, TextClip
    import moviepy.video.fx.all as vfx
except: pass

# --- CONFIGURATION ---
if os.path.exists("/usr/bin/convert"): os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"

LANGUAGE_VOICES = {
    "English (US)": ("English", "en-US-ChristopherNeural"),
    "English (UK)": ("English", "en-GB-RyanNeural"),
    "Hindi (India)": ("Hindi", "hi-IN-MadhurNeural")
}
ADMIN_EMAIL = "helpanimeso1@gmail.com"

# --- DB HELPERS ---
def get_sb_headers(): return {"apikey": st.secrets["SUPABASE_KEY"], "Authorization": f"Bearer {st.secrets['SUPABASE_KEY']}", "Content-Type": "application/json", "Prefer": "return=representation"}
def get_user(email):
    try:
        url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers?email=eq.{email}"
        res = requests.get(url, headers=get_sb_headers())
        if res.status_code == 200 and len(res.json()) > 0: return res.json()[0]
    except: pass
    return None
def create_user(email, password):
    url = f"{st.secrets['SUPABASE_URL']}/rest/v1/paid_customers"
    ref_code = f"AUTOX-{email.split('@')[0][:4].upper()}-{''.join(random.choices(string.digits, k=4))}"
    data = {"email": email, "password": password, "has_paid": False, "videos_left": 1, "referral_code": ref_code, "yt_pro": False, "insta_pro": False, "referral_count": 0}
    requests.post(url, headers=get_sb_headers(), json=data)
    return data
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

# --- UI OVERRIDES (EXACT JAI PORTAL CLONE) ---
st.set_page_config(page_title="AI YouTube Agent - Video Production | JAI Portal", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    .block-container { padding: 0 !important; max-width: 100% !important; }
    header, footer, #MainMenu { visibility: hidden !important; display: none !important; }
    .stApp {
        background-color: #0a0a14 !important;
        background-image: 
            radial-gradient(ellipse 80% 50% at 50% -20%, rgba(139, 92, 246, 0.12) 0%, transparent 50%),
            radial-gradient(ellipse 60% 40% at 90% 100%, rgba(236, 72, 153, 0.06) 0%, transparent 50%) !important;
        color: #ffffff !important;
        font-family: 'Inter', -apple-system, sans-serif !important;
    }
    
    /* JaiPortal EXACT Button */
    .stButton > button {
        background: linear-gradient(to right, #f97316, #ef4444, #ec4899) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(249, 115, 22, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(to right, #fb923c, #f87171, #f472b6) !important;
        box-shadow: 0 4px 15px rgba(249, 115, 22, 0.6) !important;
    }
    
    .stTextInput input, .stSelectbox div[data-baseweb="select"] { 
        background-color: rgba(255,255,255,0.05) !important; 
        color: #ffffff !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important; 
        border-radius: 8px !important;
    }
    
    /* Exact Nav */
    .jai-nav {
        position: fixed; top: 0; left: 0; right: 0; height: 64px; z-index: 50000;
        background: linear-gradient(135deg, rgba(10, 10, 25, 0.95) 0%, rgba(30, 15, 60, 0.9) 50%, rgba(10, 10, 25, 0.95) 100%);
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(139, 92, 246, 0.12);
        display: flex; justify-content: space-between; align-items: center; padding: 0 2rem;
    }
    .jai-nav-logo img { height: 40px; }
    .jai-nav-links { display: flex; gap: 1.5rem; color: #d1d5db; font-size: 0.875rem; font-weight: 500; align-items: center; }
    @media (max-width: 768px) { .jai-nav-links { display: none; } }
</style>

<div class="jai-nav">
    <div style="display: flex; align-items: center; gap: 1rem;">
        <img src="https://cdn.jaiportal.com/uploaded_images/1aa988a0-1a43-4f0b-a49d-8a8565aa216a.png" style="height: 40px;" />
    </div>
    <div class="jai-nav-links">
        <span style="display: flex; align-items: center; gap: 4px; cursor: pointer;">All Models <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M19 9l-7 7-7-7"></path></svg></span>
        <span style="display: flex; align-items: center; gap: 4px; cursor: pointer;">Explore <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M19 9l-7 7-7-7"></path></svg></span>
        <span style="display: flex; align-items: center; gap: 4px; cursor: pointer;">Tools <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M19 9l-7 7-7-7"></path></svg></span>
        <span style="cursor: pointer;">Pricing</span>
        <span style="cursor: pointer;">API</span>
    </div>
    <div style="display: flex; gap: 1rem; align-items: center;">
        <span style="color: #d1d5db; font-size: 0.875rem; cursor: pointer;">Sign In</span>
        <button style="background: linear-gradient(to right, #8b5cf6, #ec4899); color: white; padding: 0.5rem 1rem; border-radius: 0.5rem; font-size: 0.875rem; font-weight: 600; border: none; cursor: pointer;">Get Started</button>
    </div>
</div>
<div style="height: 64px;"></div>
""", unsafe_allow_html=True)

if 'logged_in_email' not in st.session_state:
    st.session_state.logged_in_email = None; st.session_state.otp_sent = False; st.session_state.expected_otp = None

if not st.session_state.logged_in_email:
    # Exact JaiPortal Hero
    st.markdown("""
    <div style="text-align: center; margin-top: 60px; padding: 0 20px;">
        <span style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: white; margin-bottom: 20px;">AI Video Agent</span>
        <h1 style="font-size: 3.5rem; font-weight: 900; letter-spacing: -1px; margin: 0 auto; line-height: 1.1; max-width: 800px; color: white;">AI YouTube Agent<br>Video Production</h1>
        <p style="color: #a1a1aa; font-size: 1.25rem; max-width: 700px; margin: 20px auto 40px auto; line-height: 1.6;">Automate your YouTube channel with AI. Video creation, thumbnail generation, and script writing on autopilot.</p>
    </div>
    
    <!-- Video Modal / Showcase -->
    <div style="display: flex; justify-content: center; margin-bottom: 60px; padding: 0 20px;">
        <div style="position: relative; width: 100%; max-width: 900px; border-radius: 12px; overflow: hidden; box-shadow: 0 15px 40px rgba(255, 0, 0, 0.2); background: rgba(0,0,0,0.3); aspect-ratio: 16/9; transition: transform 0.3s ease;">
            <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" src="https://www.youtube.com/embed/LXb3EKWsInQ?autoplay=1&mute=1&loop=1&playlist=LXb3EKWsInQ&controls=0&rel=0&modestbranding=1" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
        </div>
    </div>
    
    <!-- Exact Login Card matching JAI Features -->
    <div style="max-width: 500px; margin: 0 auto; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 30px;">
        <h3 style="text-align:center; color:white; font-size: 1.25rem; font-weight: 700; margin-bottom: 20px;">Login to AI Workspace</h3>
    """, unsafe_allow_html=True)
    
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
                st.success("Verification code sent via Email!")
                otp_in = st.text_input("Enter Code")
                pwd_in = st.text_input("Create Password", type="password")
                if st.button("Create AI Workspace"):
                    if otp_in == st.session_state.expected_otp and len(pwd_in) >= 4:
                        create_user(email_input.strip(), pwd_in)
                        st.session_state.logged_in_email = email_input.strip()
                        st.rerun()
        else:
            pwd_in = st.text_input("Password", type="password")
            if st.button("Log In"):
                if pwd_in == user['password']:
                    st.session_state.logged_in_email = email_input.strip()
                    st.rerun()
                else: st.error("Incorrect Password.")
    
    st.markdown("</div><br><br>", unsafe_allow_html=True)
    
else:
    def add_subtitles(video, vtt_file, width, height):
        try:
            subs = webvtt.read(vtt_file)
            sub_clips = []
            for sub in subs:
                start = sum(x * float(t) for x, t in zip([3600, 60, 1], sub.start.split(":")))
                end = sum(x * float(t) for x, t in zip([3600, 60, 1], sub.end.split(":")))
                txt = sub.text.strip().replace("\n", " ")
                txt_clip = TextClip(txt, font="Arial-Bold", fontsize=50 if width > height else 40, color='white', stroke_color='black', stroke_width=2, method="caption", size=(width*0.8, None)).set_start(start).set_end(end).set_position(('center', 'center' if width < height else 'bottom'))
                sub_clips.append(txt_clip)
            return CompositeVideoClip([video] + sub_clips)
        except: return video
    
    def run_video_agent(agent_topic, template, is_landscape, agent_voice):
        try: user_gemini_key = st.secrets["GEMINI_API_KEY"]; user_pexels_key = st.secrets["PEXELS_API_KEY"]
        except: st.error("API Keys missing in secrets."); return
        genai.configure(api_key=user_gemini_key); model = genai.GenerativeModel('gemini-3.6-flash')
        width, height = (1280, 720) if is_landscape else (720, 1280)
        orientation = "landscape" if is_landscape else "portrait"
        
        with st.status("⚙️ AutoX AI Agent is processing...", expanded=True) as status:
            try:
                lang, code = LANGUAGE_VOICES[agent_voice]
                st.write(f"✍️ Writing {template} script & SEO...")
                base_prompt = f"Write a 60-second video script about: {agent_topic}. Format: {'16:9' if is_landscape else '9:16'}. Language: {lang}. "
                
                if template == "AI Tutorial": base_prompt += "Make it a step-by-step educational tutorial."
                elif template == "Product Review": base_prompt += "Make it a product review highlighting pros, cons, and a final verdict."
                elif template == "Top 10 Compilation": base_prompt += "Make it a fast-paced Top 5 or Top 10 ranking list."
                elif template == "Gaming Commentary": base_prompt += "Make it sound like an energetic gaming streamer commentary."
                elif template == "Vlog Style Creator": base_prompt += "Make it sound like a personal, cinematic daily vlog storytelling script."
                else: base_prompt += "Make it engaging and viral."
                
                base_prompt += "\nFormat EXACTLY like this:\nKEYWORDS: kw1, kw2\nSCRIPT:\n[script]\nSEO_TITLE:\n[title]\nSEO_TAGS:\n[tags]"
                
                res = model.generate_content(base_prompt).text
                script = res.split("SCRIPT:")[1].split("SEO_TITLE:")[0].strip()
                kws = res.split("SCRIPT:")[0].replace("KEYWORDS:", "").strip().split(",")[:2]
                seo_title = res.split("SEO_TITLE:")[1].split("SEO_TAGS:")[0].strip()
                seo_tags = res.split("SEO_TAGS:")[1].strip()
                
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
                        with open(f"v_{kw}.mp4", 'wb') as f: f.write(requests.get(vdata[0]['video_files'][0]['link']).content)
                        clip = VideoFileClip(f"v_{kw}.mp4").resize(newsize=(width, height))
                        if len(videos) > 0: clip = clip.crossfadein(0.5)
                        videos.append(clip)
                
                if not videos:
                    with open("fb.jpg", 'wb') as f: f.write(requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(agent_topic)}?width={width}&height={height}&nologo=true").content)
                    videos.append(ImageClip("fb.jpg").resize(newsize=(width, height)).set_duration(5))
    
                st.write("🎞️ Rendering Advanced Timeline (Transitions & Subtitles)...")
                final_path = "agent_final.mp4"
                audioclip = AudioFileClip(audio_path)
                vis = concatenate_videoclips(videos, padding=-0.5, method="compose") if len(videos) > 1 else videos[0]
                vis = vis.fx(vfx.loop, duration=audioclip.duration) if vis.duration < audioclip.duration else vis.subclip(0, audioclip.duration)
                final_vid = vis.set_audio(audioclip)
                
                try: final_vid = add_subtitles(final_vid, vtt_path, width, height)
                except: pass
                final_vid.write_videofile(final_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
                
                st.write("🖼️ Generating 8K Thumbnail...")
                p = model.generate_content(f"Create an 8k hyper-realistic image prompt for a video thumbnail about: '{agent_topic}'. NO TEXT. Max 30 words.").text.strip()
                thumb_img = requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width=1280&height=720&nologo=true").content
                with open("thumb.jpg", 'wb') as f: f.write(thumb_img)
                
                st.success("✅ AutoX Process Complete!")
                st.video(final_path)
                st.image("thumb.jpg", caption="Generated Thumbnail")
                st.markdown(f"**Title:** {seo_title}")
                st.markdown(f"**Tags:** {seo_tags}")
                st.markdown(f"**Script:** {script}")
                
            except Exception as e:
                st.error(f"Error during agent generation: {e}")

    current_user = get_user(st.session_state.logged_in_email)
    if not current_user: st.stop()
    st.markdown("<h2 style='text-align:center; margin-top:20px; color:white;'>⚡ AutoX Dashboard</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns([4,1])
    with c2:
        if st.button("Logout"): 
            st.session_state.logged_in_email = None
            st.rerun()
    agent_topic = st.text_input("Enter Video Topic")
    c_type, c_voice = st.columns(2)
    with c_type:
        template = st.selectbox("Video Style", ["AI Tutorial", "Product Review", "Top 10 Compilation", "Gaming Commentary", "Vlog Style Creator"])
        is_landscape = st.selectbox("Format", ["YouTube (16:9)", "Instagram Reels (9:16)"]) == "YouTube (16:9)"
    with c_voice:
        agent_voice = st.selectbox("AI Voice", list(LANGUAGE_VOICES.keys()))
    if st.button("Generate Video Autonomously", use_container_width=True):
        run_video_agent(agent_topic, template, is_landscape, agent_voice)
