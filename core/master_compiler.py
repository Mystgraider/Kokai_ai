# core/master_compiler.py
import os
import re
from moviepy import VideoFileClip, AudioFileClip  # Inayos para sa MoviePy v2 standard layout
from core.audio_engine import render_standalone_audio
from core.video_engine import render_standalone_video
from shared.uploaders import upload_to_youtube, upload_to_facebook
from memory.store import save_memory

async def compile_and_publish_marathon(title: str, script_chapters: list, scenes_keywords: list):
    os.makedirs("static/final_marathon", exist_ok=True)
    os.makedirs("static/temp_compile", exist_ok=True)
    
    published_links = {"youtube": [], "facebook": []}
    
    try:
        for index, story_text in enumerate(script_chapters):
            part_num = index + 1
            print(f"[COMPILER]: Processing Segment Part {part_num} of 3...")
            
            clean_title = title.replace(" ", "_")
            aud_temp = f"static/temp_compile/audio_p{part_num}_{clean_title}.mp3"
            vid_temp = f"static/temp_compile/silent_p{part_num}_{clean_title}.mp4"
            final_mp4_path = f"static/final_marathon/Part_{part_num}_{clean_title}.mp4"
            
            exact_duration = await render_standalone_audio(story_text, aud_temp)
            keyword = scenes_keywords[index] if index < len(scenes_keywords) else "creepy illustration"
            video_success = render_standalone_video(keyword, exact_duration, vid_temp)
            
            if not video_success:
                print(f"[COMPILER WARNING]: Visual harvest failed for part {part_num}. Skipping layer merge.")
                continue

            silent_video_clip = VideoFileClip(vid_temp)
            audio_track_clip = AudioFileClip(aud_temp)
            final_synced_clip = silent_video_clip.set_audio(audio_track_clip)
            
            final_synced_clip.write_videofile(
                final_mp4_path, 
                fps=24, 
                codec="libx264", 
                audio_codec="aac",
                verbose=False,
                logger=None
            )
            
            silent_video_clip.close()
            audio_track_clip.close()
            final_synced_clip.close()
            
            print(f"[COMPILER SUCCESS]: Part {part_num} rendering done -> {final_mp4_path}")
            
            try:
                yt_url = upload_to_youtube(
                    video_path=final_mp4_path,
                    title=f"{title} - Part {part_num} (Tuloy-tuloy na Kwento)",
                    description=f"Bahagi {part_num} ng ating pang-araw-araw na kwentong aswang.\n\nSalamat sa pakikinig kay KOKAI_AI!"
                )
                if yt_url != "UPLOAD_SKIPPED":
                    published_links["youtube"].append(yt_url)
            except Exception as yt_err:
                print(f"[YOUTUBE UPLOAD ERROR]: {yt_err}")

            try:
                fb_res = upload_to_facebook(
                    video_path=final_mp4_path,
                    title=f"{title} - Part {part_num}",
                    description=f"Panoorin ang Bahagi {part_num} ng ating tuloy-tuloy na horror series."
                )
                published_links["facebook"].append(fb_res)
            except Exception as fb_err:
                print(f"[FACEBOOK UPLOAD ERROR]: {fb_err}")

        for f in os.listdir("static/temp_compile"):
            os.remove(os.path.join("static/temp_compile", f))
            
        print("[COMPILER EXECUTION COMPLETED]: All segments processed and cleaned up successfully.")
        return published_links

    except Exception as master_err:
        print(f"[MASTER COMPILER CRITICAL CRASH]: {master_err}")
        return {"error": str(master_err)}
