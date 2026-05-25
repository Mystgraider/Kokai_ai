import os
import edge_tts
from pydub import AudioSegment

async def render_standalone_audio(text: str, output_path: str):
    temp_voice = output_path + ".raw.mp3"
    try:
        communicate = edge_tts.Communicate(text.strip(), "fil-PH-AngeloNeural", rate="-6%", pitch="-3Hz")
        await communicate.save(temp_voice)
        
        voice_layer = AudioSegment.from_mp3(temp_voice)
        bgm_file = "static/assets/scary_bgm.mp3"
        sfx_file = "static/assets/jumpscare.mp3"
        
        if os.path.exists(bgm_file):
            bgm_layer = AudioSegment.from_mp3(bgm_file)
            if len(bgm_layer) < len(voice_layer):
                bgm_layer = bgm_layer * ((len(voice_layer) // len(bgm_layer)) + 1)
            bgm_layer = bgm_layer[:len(voice_layer)] - 24
            final_audio = voice_layer.overlay(bgm_layer)
        else:
            final_audio = voice_layer

        lowered_text = text.lower()
        if any(x in lowered_text for x in ["at biglang", "nagulat", "sumigaw"]):
            if os.path.exists(sfx_file):
                sfx_layer = AudioSegment.from_mp3(sfx_file) - 4
                final_audio = final_audio.overlay(sfx_layer, position=len(final_audio) // 2)

        final_audio = final_audio + 3
        final_audio.export(output_path, format="mp3")
        return len(final_audio) / 1000.0
    except Exception as e:
        raise e
    finally:
        if os.path.exists(temp_voice):
            os.remove(temp_voice)
