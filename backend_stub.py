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
