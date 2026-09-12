import streamlit as st
import subprocess
import os
import requests
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, TextClip
import moviepy.video.fx.all as vfx
import webvtt

# --- CONFIGURATION FOR SERVER ---
if os.path.exists("/usr/bin/convert"):
    os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"

LANGUAGE_VOICES = {
    "English (Deep Male)": ("English", "en-US-ChristopherNeural"),
    "English (Friendly Female)": ("English", "en-US-AriaNeural"),
    "Hindi (Male) - हिन्दी": ("Hindi", "hi-IN-MadhurNeural"),
    "Hindi (Female) - हिन्दी": ("Hindi", "hi-IN-SwaraNeural"),
    "Spanish (Male) - Español": ("Spanish", "es-ES-AlvaroNeural")
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
        txt_clip = TextClip(sub.text.upper(), fontsize=70, color='yellow', font='Arial',
                            stroke_color='black', stroke_width=3, method='caption', size=(video_clip.w - 100, None))
        txt_clip = txt_clip.set_position(('center', 'center')).set_start(start_time).set_end(end_time)
        subtitle_clips.append(txt_clip)
    return CompositeVideoClip([video_clip] + subtitle_clips)


# --- UI SETUP ---
st.set_page_config(page_title="AutoX AI Suite", page_icon="🤖", layout="wide")

# --- SIDEBAR: NAVIGATION ---
with st.sidebar:
    st.title("🤖 AutoX AI")
    st.markdown("*The Future of Automation*")
    
    st.divider()
    
    app_mode = st.radio("🛠️ Select Tool:", ["🏢 AutoX Dashboard", "🎬 AutoTube (Video Maker)", "🖼️ AutoThumb (Thumbnails)", "✍️ AutoBlog (Blogging)"])
    
    st.divider()
    st.markdown("**Powered by AutoX**\n\n*Founded by Prince Kumar Singh*")

# --- SECURE API KEYS (HIDDEN FROM CUSTOMERS) ---
try:
    # This reads keys directly from Streamlit's secure vault
    user_gemini_key = st.secrets["GEMINI_API_KEY"]
    user_pexels_key = st.secrets["PEXELS_API_KEY"]
except:
    # If vault is empty, it will throw an error telling you to add them
    user_gemini_key = None
    user_pexels_key = None

# --- PAGE: DASHBOARD ---
if app_mode == "🏢 AutoX Dashboard":
    st.title("Welcome to AutoX AI 🚀")
    st.markdown("### The Ultimate Automation Ecosystem")
    st.write("At AutoX, our vision is to automate everything from digital content to physical robots. You are currently exploring our Software Suite.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("### 🎬 AutoTube\nGenerate viral faceless YouTube Shorts in 1-click with real HD background videos and realistic AI voices.\n\n**Status: ✅ LIVE**")
        
    with col2:
        st.warning("### 🖼️ AutoThumb\nGenerate hyper-realistic, clickbait YouTube thumbnails using advanced Image AI.\n\n**Status: 🚧 Building...**")
        
    with col3:
        st.success("### ✍️ AutoBlog\nInstantly convert any topic into a 1000-word SEO optimized blog post.\n\n**Status: 🚧 Coming Soon**")
        
    st.divider()
    st.write("👈 Select a tool from the sidebar to begin!")

# --- PAGE: AUTOTUBE ---
elif app_mode == "🎬 AutoTube (Video Maker)":
    st.title("🎬 AutoTube - Viral Shorts Generator")
    
    if not user_gemini_key or not user_pexels_key:
        st.error("⚠️ SYSTEM ERROR: The CEO has not set up the API Keys in the Server Vault yet. Please try again later.")
        st.stop()
        
    genai.configure(api_key=user_gemini_key)
    model = genai.GenerativeModel('gemini-3.6-flash')
    
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Video Settings")
        topic = st.text_input("🎯 Enter video topic:")
        voice_option = st.selectbox("🌍 Select Language & Voice:", list(LANGUAGE_VOICES.keys()))
        selected_lang_name, selected_voice_code = LANGUAGE_VOICES[voice_option]
        enable_captions = st.checkbox("📝 Add Alex Hormozi Style Captions", value=True)
        generate_btn = st.button("🚀 Generate Viral Video", use_container_width=True)

    with col2:
        st.subheader("Live Preview")
        if generate_btn:
            if not topic.strip():
                st.warning("⚠️ Please enter a topic.")
            else:
                try:
                    with st.spinner(f"🧠 Writing script in {selected_lang_name}..."):
                        prompt = f"Write a fast-paced 60-second YouTube Shorts script about: {topic}. Language: {selected_lang_name}. Format EXACTLY like this:\nKEYWORDS: keyword1, keyword2, keyword3\nSCRIPT:\n[script]"
                        text_response = model.generate_content(prompt).text
                        try:
                            keywords_part = text_response.split("SCRIPT:")[0].replace("KEYWORDS:", "").strip()
                            generated_script = text_response.split("SCRIPT:")[1].strip()
                            search_keywords = [k.strip() for k in keywords_part.split(",")][:3]
                        except:
                            generated_script = text_response
                            search_keywords = [topic.split()[0]]
                        
                        st.success("✅ Script Written!")
                        with st.expander("Show Generated Script"):
                            st.write(generated_script)

                    with st.spinner("🎙️ Generating realistic voice..."):
                        audio_path = "auto_voice.mp3"
                        vtt_path = "auto_voice.vtt"
                        subprocess.run(["python3", "-m", "edge_tts", "--text", generated_script, "--voice", selected_voice_code, "--write-media", audio_path, "--write-subtitles", vtt_path], check=True)

                    with st.spinner("🎥 Downloading HD Stock Videos..."):
                        headers = {"Authorization": user_pexels_key}
                        video_clips = []
                        for kw in search_keywords:
                            res = requests.get(f"https://api.pexels.com/videos/search?query={kw}&per_page=1&orientation=portrait&size=medium", headers=headers).json()
                            videos_data = res.get('videos', [])
                            if videos_data and videos_data[0].get('video_files'):
                                link = videos_data[0]['video_files'][0]['link']
                                vid_path = f"temp_vid_{kw}.mp4"
                                with open(vid_path, 'wb') as f:
                                    f.write(requests.get(link).content)
                                video_clips.append(VideoFileClip(vid_path).resize(newsize=(720, 1280)))
                        
                        if not video_clips:
                            img_url = f"https://image.pollinations.ai/prompt/{topic.replace(' ', '%20')}?width=720&height=1280&nologo=true"
                            with open("fallback.jpg", 'wb') as f:
                                f.write(requests.get(img_url).content)
                            video_clips.append(ImageClip("fallback.jpg").resize(newsize=(720, 1280)))

                    with st.spinner("🎬 Finalizing Video..."):
                        final_video_path = "viral_short.mp4"
                        audio_clip = AudioFileClip(audio_path)
                        final_visuals = concatenate_videoclips(video_clips, method="compose") if len(video_clips) > 1 else video_clips[0]
                        if final_visuals.duration < audio_clip.duration:
                            final_visuals = final_visuals.fx(vfx.loop, duration=audio_clip.duration)
                        else:
                            final_visuals = final_visuals.subclip(0, audio_clip.duration)
                        
                        final_video = final_visuals.set_audio(audio_clip)
                        if enable_captions:
                            try:
                                final_video = add_subtitles(final_video, vtt_path)
                            except:
                                pass
                        
                        final_video.write_videofile(final_video_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
                        st.success("🎉 Video Ready!")
                        st.video(final_video_path)
                        with open(final_video_path, "rb") as file:
                            st.download_button("💾 Download Output Video", data=file, file_name="viral_short.mp4", mime="video/mp4")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# --- PAGE: AUTOTHUMB ---
elif app_mode == "🖼️ AutoThumb (Thumbnails)":
    st.title("🖼️ AutoThumb AI - Viral Thumbnail Maker")
    st.markdown("Create High-CTR, eye-catching YouTube thumbnails instantly.")
    
    if not user_gemini_key:
        st.error("⚠️ SYSTEM ERROR: The CEO has not set up the API Keys in the Server Vault yet. Please try again later.")
        st.stop()
        
    genai.configure(api_key=user_gemini_key)
    model = genai.GenerativeModel('gemini-3.6-flash')
    
    thumb_topic = st.text_input("🎯 What is your video about?", placeholder="e.g. Discovering Aliens on Mars")
    thumb_style = st.selectbox("🎨 Select Style:", ["MrBeast Style (Hyper-Realistic, Bright Colors)", "Cinematic Drama (Dark, Epic, Glowing Lights)", "3D Cartoon (Fun, Expressive)"])
    
    if st.button("🚀 Generate Thumbnail", use_container_width=True):
        if not thumb_topic.strip():
            st.warning("⚠️ Please enter a topic.")
        else:
            try:
                with st.spinner("🧠 AI is designing the perfect clickbait concept..."):
                    prompt_design = f"I want to generate a viral YouTube thumbnail image for a video about: '{thumb_topic}'. The visual style should be {thumb_style}. Write a highly detailed, dramatic image generation prompt (max 40 words) describing the scene, lighting, subject's expression, and background. DO NOT include any text or words in the image. Just describe the pure visuals."
                    img_prompt = model.generate_content(prompt_design).text.strip()
                    
                    import urllib.parse
                    safe_prompt = urllib.parse.quote(img_prompt)
                    
                with st.spinner("🖼️ Generating 1280x720 HD Image (Takes 10 seconds)..."):
                    img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1280&height=720&nologo=true"
                    img_data = requests.get(img_url).content
                    
                    with open("thumbnail.jpg", "wb") as f:
                        f.write(img_data)
                        
                st.success("✅ Thumbnail Ready! (Warning: Always double-check AI images for minor errors)")
                st.image("thumbnail.jpg", caption=f"AI Concept: {img_prompt}")
                
                with open("thumbnail.jpg", "rb") as file:
                    st.download_button("💾 Download HD Thumbnail", data=file, file_name="AutoThumb_Thumbnail.jpg", mime="image/jpeg", use_container_width=True)
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# --- PAGE: AUTOBLOG ---
elif app_mode == "✍️ AutoBlog (Blogging)":
    st.title("✍️ AutoBlog AI")
    st.warning("🚧 This tool is currently being built by the AutoX Engineering Team. Come back soon!")
