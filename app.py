import streamlit as st
import subprocess
import os
import requests
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, TextClip
import moviepy.video.fx.all as vfx
import webvtt
import urllib.parse

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
        txt_clip = TextClip(sub.text.upper(), fontsize=70, color='yellow', font='Arial-Bold',
                            stroke_color='black', stroke_width=4, method='caption', size=(video_clip.w - 100, None))
        txt_clip = txt_clip.set_position(('center', 'center')).set_start(start_time).set_end(end_time)
        subtitle_clips.append(txt_clip)
    return CompositeVideoClip([video_clip] + subtitle_clips)


# --- UI SETUP ---
st.set_page_config(page_title="AutoX AI Suite", page_icon="🤖", layout="wide")

# --- SIDEBAR: NAVIGATION ---
with st.sidebar:
    st.title("🤖 AutoX AI")
    st.markdown("*The Ultimate Creator Suite*")
    st.divider()
    app_mode = st.radio("🛠️ Select Tool:", [
        "🏢 AutoX Dashboard", 
        "🎬 AutoTube (Video Maker)", 
        "🖼️ AutoThumb (Thumbnails)", 
        "✍️ AutoBlog (Blogging)",
        "📱 AutoSocial (Social Media)",
        "🚀 AutoSEO (YouTube Growth)"
    ])
    st.divider()
    st.markdown("**Powered by AutoX**\n\n*Founded by Prince Kumar Singh*")

# --- SECURE API KEYS ---
try:
    user_gemini_key = st.secrets["GEMINI_API_KEY"]
    user_pexels_key = st.secrets["PEXELS_API_KEY"]
except:
    user_gemini_key = None
    user_pexels_key = None


# --- PAGE: DASHBOARD ---
if app_mode == "🏢 AutoX Dashboard":
    st.title("Welcome to AutoX AI 🚀")
    st.markdown("### The All-in-One Content Automation Empire")
    st.write("You now own the most powerful AI creator suite on the internet. Choose a tool below:")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("### 🎬 AutoTube\nGenerate viral faceless YouTube Shorts in 1-click.\n\n**Status: ✅ LIVE**")
        st.success("### ✍️ AutoBlog\nInstantly convert any topic into a 1000-word SEO blog.\n\n**Status: ✅ LIVE**")
        st.error("### 🚀 AutoSEO\nGenerate Viral Titles, Descriptions, and Tags for YouTube.\n\n**Status: ✅ NEW**")
    with col2:
        st.warning("### 🖼️ AutoThumb\nGenerate hyper-realistic YouTube thumbnails.\n\n**Status: ✅ LIVE**")
        st.info("### 📱 AutoSocial\nWrite viral Twitter Threads, Instagram & LinkedIn posts.\n\n**Status: ✅ NEW**")


# --- PAGE: AUTOTUBE ---
elif app_mode == "🎬 AutoTube (Video Maker)":
    st.title("🎬 AutoTube - Viral Shorts Generator")
    
    if not user_gemini_key or not user_pexels_key:
        st.error("⚠️ SYSTEM ERROR: The CEO has not set up the API Keys in the Server Vault yet.")
        st.stop()
        
    genai.configure(api_key=user_gemini_key)
    model = genai.GenerativeModel('gemini-3.6-flash')
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Video Settings")
        topic = st.text_input("🎯 Enter video topic:")
        voice_option = st.selectbox("🌍 Select Language & Voice:", list(LANGUAGE_VOICES.keys()))
        selected_lang_name, selected_voice_code = LANGUAGE_VOICES[voice_option]
        enable_captions = st.checkbox("📝 Add Subtitles", value=True)
        generate_btn = st.button("🚀 Generate Viral Video", use_container_width=True)

    with col2:
        st.subheader("Live Output")
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
                        st.expander("Show Script").write(generated_script)
                        st.download_button("💾 Download Script (TXT)", data=generated_script, file_name="AutoTube_Script.txt", mime="text/plain")

                    with st.spinner("🎙️ Generating realistic voice..."):
                        audio_path = "auto_voice.mp3"
                        vtt_path = "auto_voice.vtt"
                        subprocess.run(["python3", "-m", "edge_tts", "--text", generated_script, "--voice", selected_voice_code, "--write-media", audio_path, "--write-subtitles", vtt_path], check=True)
                        st.audio(audio_path, format="audio/mp3")
                        with open(audio_path, "rb") as f:
                            st.download_button("💾 Download Voiceover (MP3)", data=f, file_name="AutoTube_Voice.mp3", mime="audio/mpeg")

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
                            img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(topic)}?width=720&height=1280&nologo=true"
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
                        st.success("🎉 Final Video Ready!")
                        st.video(final_video_path)
                        with open(final_video_path, "rb") as file:
                            st.download_button("💾 Download Final Video (MP4)", data=file, file_name="AutoTube_Final_Video.mp4", mime="video/mp4", use_container_width=True)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


# --- PAGE: AUTOTHUMB ---
elif app_mode == "🖼️ AutoThumb (Thumbnails)":
    st.title("🖼️ AutoThumb AI - Realistic Thumbnail Maker")
    st.markdown("Create Hyper-Realistic, eye-catching YouTube thumbnails instantly.")
    
    if not user_gemini_key:
        st.error("⚠️ SYSTEM ERROR: The CEO has not set up the API Keys in the Server Vault yet.")
        st.stop()
        
    genai.configure(api_key=user_gemini_key)
    model = genai.GenerativeModel('gemini-3.6-flash')
    
    thumb_topic = st.text_input("🎯 What is your video about?", placeholder="e.g. Discovering Aliens on Mars")
    thumb_style = st.selectbox("🎨 Select Style:", ["Hyper-Realistic (8k Photography)", "Cinematic Drama (Epic Lighting)", "MrBeast Style (Bright & Saturated)"])
    
    if st.button("🚀 Generate Thumbnail", use_container_width=True):
        if not thumb_topic.strip():
            st.warning("⚠️ Please enter a topic.")
        else:
            try:
                with st.spinner("🧠 AI is designing a hyper-realistic concept..."):
                    prompt_design = f"Create a highly detailed image generation prompt for a YouTube thumbnail about: '{thumb_topic}'. Style: {thumb_style}. The image MUST be hyper-realistic, photorealistic, 8k resolution, shot on an expensive DSLR camera. Extremely high quality. NO TEXT, NO WORDS, NO LETTERS, NO WATERMARKS. Describe the visual scene perfectly in max 40 words."
                    img_prompt = model.generate_content(prompt_design).text.strip()
                    safe_prompt = urllib.parse.quote(img_prompt)
                    
                with st.spinner("🖼️ Rendering Ultra-HD Image (Takes 10 seconds)..."):
                    img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1280&height=720&nologo=true"
                    img_data = requests.get(img_url).content
                    
                    with open("thumbnail.jpg", "wb") as f:
                        f.write(img_data)
                        
                st.success("✅ Realistic Thumbnail Ready!")
                st.image("thumbnail.jpg", caption=f"AI Prompt Used: {img_prompt}")
                with open("thumbnail.jpg", "rb") as file:
                    st.download_button("💾 Download HD Thumbnail (JPG)", data=file, file_name="AutoThumb_Thumbnail.jpg", mime="image/jpeg", use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# --- PAGE: AUTOBLOG ---
elif app_mode == "✍️ AutoBlog (Blogging)":
    st.title("✍️ AutoBlog AI - SEO Article Writer")
    st.markdown("Instantly generate a 1000-word, fully formatted, SEO-optimized blog post.")
    
    if not user_gemini_key:
        st.error("⚠️ SYSTEM ERROR: The CEO has not set up the API Keys in the Server Vault yet.")
        st.stop()
        
    genai.configure(api_key=user_gemini_key)
    model = genai.GenerativeModel('gemini-3.6-flash')
    
    blog_topic = st.text_input("📝 Enter your Blog Topic:", placeholder="e.g. 5 Ways to Make Money with AI")
    blog_lang = st.selectbox("🌍 Blog Language:", ["English", "Hindi", "Spanish"])
    
    if st.button("🚀 Generate SEO Blog", use_container_width=True):
        if not blog_topic.strip():
            st.warning("⚠️ Please enter a topic.")
        else:
            try:
                with st.spinner("🧠 AI is researching and writing your 1000-word article..."):
                    blog_prompt = f"Write a comprehensive, highly engaging, and SEO-optimized blog post about '{blog_topic}'. The language must be {blog_lang}. Include a catchy Title, introduction, multiple H2 and H3 subheadings, bullet points, and a strong conclusion. Write at least 800-1000 words. Format strictly in Markdown."
                    blog_content = model.generate_content(blog_prompt).text
                    
                st.success("✅ SEO Blog Generated Successfully!")
                with st.expander("📖 Read Generated Blog", expanded=True):
                    st.markdown(blog_content)
                st.download_button("💾 Download Blog as Text File (TXT)", data=blog_content, file_name=f"AutoBlog_{blog_topic.replace(' ', '_')}.txt", mime="text/plain", use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# --- PAGE: AUTOSOCIAL ---
elif app_mode == "📱 AutoSocial (Social Media)":
    st.title("📱 AutoSocial AI - Viral Content Creator")
    st.markdown("Automate your Twitter, Instagram, and LinkedIn presence in 1-click.")
    
    if not user_gemini_key:
        st.error("⚠️ SYSTEM ERROR: The CEO has not set up the API Keys in the Server Vault yet.")
        st.stop()
        
    genai.configure(api_key=user_gemini_key)
    model = genai.GenerativeModel('gemini-3.6-flash')
    
    social_topic = st.text_input("💡 What is your post about?", placeholder="e.g. Why AI will not replace programmers")
    platform = st.selectbox("🎯 Select Platform:", ["Twitter (Viral Thread)", "LinkedIn (Professional Story)", "Instagram (Reel Caption & Hashtags)"])
    
    if st.button("🚀 Generate Viral Post", use_container_width=True):
        if not social_topic.strip():
            st.warning("⚠️ Please enter a topic.")
        else:
            try:
                with st.spinner(f"🧠 AI is writing a viral {platform} post..."):
                    social_prompt = f"Act as a world-class social media manager. Write a highly engaging viral post for {platform} about '{social_topic}'. Include a strong hook to grab attention, format it perfectly for the specific platform, use relevant emojis, and include the best viral hashtags at the end."
                    social_content = model.generate_content(social_prompt).text
                    
                st.success("✅ Viral Post Generated!")
                st.markdown("### Your Output:")
                st.info(social_content)
                st.download_button("💾 Download Post (TXT)", data=social_content, file_name=f"AutoSocial_Post.txt", mime="text/plain", use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# --- PAGE: AUTOSEO ---
elif app_mode == "🚀 AutoSEO (YouTube Growth)":
    st.title("🚀 AutoSEO AI - Rank #1 on YouTube")
    st.markdown("Get the ultimate SEO Title, Description, and Tags to make your video go viral.")
    
    if not user_gemini_key:
        st.error("⚠️ SYSTEM ERROR: The CEO has not set up the API Keys in the Server Vault yet.")
        st.stop()
        
    genai.configure(api_key=user_gemini_key)
    model = genai.GenerativeModel('gemini-3.6-flash')
    
    seo_topic = st.text_input("🔍 What is your YouTube Video about?", placeholder="e.g. iPhone 15 Pro Max Review")
    
    if st.button("🚀 Generate SEO Strategy", use_container_width=True):
        if not seo_topic.strip():
            st.warning("⚠️ Please enter a topic.")
        else:
            try:
                with st.spinner("🧠 AI is analyzing YouTube algorithms..."):
                    seo_prompt = f"Act as a YouTube Algorithm Expert. My video is about '{seo_topic}'. Give me exactly 4 things formatted clearly: \n1. Top 5 Clickbait, High-CTR Titles. \n2. A highly SEO-optimized Video Description (including timestamps if relevant). \n3. A comma-separated list of the top 30 viral tags. \n4. The top 5 Hashtags."
                    seo_content = model.generate_content(seo_prompt).text
                    
                st.success("✅ SEO Strategy Ready!")
                st.markdown("### Your YouTube SEO Toolkit:")
                st.write(seo_content)
                st.download_button("💾 Download SEO Strategy (TXT)", data=seo_content, file_name=f"AutoSEO_Strategy.txt", mime="text/plain", use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
