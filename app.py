import streamlit as st
import subprocess
import os
import requests
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, TextClip
import moviepy.video.fx.all as vfx
import webvtt

# --- CONFIGURATION FOR SERVER ---
# Linux server (like HuggingFace/Streamlit Cloud) ImageMagick path
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
st.set_page_config(page_title="AutoTube AI SaaS", page_icon="🚀", layout="wide")

# --- SIDEBAR: SAAS API KEY MANAGEMENT ---
with st.sidebar:
    st.header("⚙️ Software Settings")
    st.write("To use this software, please enter your API keys below. We do not store your keys.")
    user_gemini_key = st.text_input("🔑 Gemini API Key:", type="password")
    user_pexels_key = st.text_input("🔑 Pexels API Key:", type="password")
    
    st.divider()
    st.markdown("**Powered by AutoTube AI**\n\n*Created by CEO Prince Kumar Singh*")

st.title("🎬 AutoTube AI - Viral Shorts Generator")
st.markdown("Generate Faceless YouTube Shorts automatically in seconds!")

if not user_gemini_key or not user_pexels_key:
    st.info("👈 Please enter your Gemini and Pexels API keys in the sidebar to start using the software.")
    st.stop()

# Configure API
genai.configure(api_key=user_gemini_key)
model = genai.GenerativeModel('gemini-3.6-flash')

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. Video Settings")
    topic = st.text_input("🎯 Enter video topic:")
    voice_option = st.selectbox("🌍 Select Language & Voice:", list(LANGUAGE_VOICES.keys()))
    selected_lang_name, selected_voice_code = LANGUAGE_VOICES[voice_option]
    enable_captions = st.checkbox("📝 Add Alex Hormozi Style Captions", value=True)
    generate_btn = st.button("🚀 Generate Viral Video", use_container_width=True)

with col2:
    st.subheader("2. Live Video Preview")
    
    if generate_btn:
        if not topic.strip():
            st.warning("⚠️ Please enter a topic first.")
        else:
            try:
                # 1. SCRIPT
                with st.spinner(f"🧠 AI is writing script in {selected_lang_name}..."):
                    prompt = f"Write a highly engaging, fast-paced 60-second YouTube Shorts script about: {topic}. Language: {selected_lang_name}. Format EXACTLY like this:\nKEYWORDS: keyword1, keyword2, keyword3\nSCRIPT:\n[script]"
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

                # 2. VOICE
                with st.spinner("🎙️ Generating realistic voiceover..."):
                    audio_path = "auto_voice.mp3"
                    vtt_path = "auto_voice.vtt"
                    subprocess.run(["python3", "-m", "edge_tts", "--text", generated_script, "--voice", selected_voice_code, "--write-media", audio_path, "--write-subtitles", vtt_path], check=True)

                # 3. VIDEOS
                with st.spinner("🎥 Downloading HD Stock Videos..."):
                    headers = {"Authorization": user_pexels_key}
                    video_clips = []
                    
                    for kw in search_keywords:
                        search_url = f"https://api.pexels.com/videos/search?query={kw}&per_page=1&orientation=portrait&size=medium"
                        res = requests.get(search_url, headers=headers).json()
                        videos_data = res.get('videos', [])
                        
                        if videos_data and videos_data[0].get('video_files'):
                            link = videos_data[0]['video_files'][0]['link']
                            vid_path = f"temp_vid_{kw}.mp4"
                            with open(vid_path, 'wb') as f:
                                f.write(requests.get(link).content)
                            clip = VideoFileClip(vid_path).resize(newsize=(720, 1280))
                            video_clips.append(clip)
                    
                    if not video_clips:
                        img_url = f"https://image.pollinations.ai/prompt/{topic.replace(' ', '%20')}?width=720&height=1280&nologo=true"
                        with open("fallback.jpg", 'wb') as f:
                            f.write(requests.get(img_url).content)
                        video_clips.append(ImageClip("fallback.jpg").resize(newsize=(720, 1280)))

                # 4. MERGE
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
