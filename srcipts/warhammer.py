# srcipts/warhammer.py  |  makes long form warhammer content from existing sources

import os
import random
import ffmpeg
from datetime import datetime
from pydub import AudioSegment
from pathlib import Path
from openai import OpenAI

os.environ["TOKENIZERS_PARALLELISM"] = "false"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



def cleanup_folder(folder, exclude=[]):
    if os.path.exists(folder):
        for file in os.listdir(folder):
            if file not in exclude:
                file_path = os.path.join(folder, file)
                os.remove(file_path)
    else:
        os.makedirs(folder)




def generate_tts_for_script(script_path, tts_output_folder):
    tts_output_path = os.path.join(tts_output_folder, "script_tts.mp3")
    if os.path.exists(tts_output_path):
        print(f"TTS audio already exists at {tts_output_path}. Skipping TTS generation.")
        return tts_output_path
    
    os.makedirs(tts_output_folder, exist_ok=True)
    
    with open(script_path, 'r') as file:
        script_content = file.read()
    
    tts_parts = []
    part_size = 2000  
    for i in range(0, len(script_content), part_size):
        part_content = script_content[i:i+part_size]
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=part_content
        )
        part_path = os.path.join(tts_output_folder, f"script_tts_part_{i//part_size}.mp3")
        response.stream_to_file(Path(part_path))
        tts_parts.append(part_path)
        print(f"Generated TTS for part {i//part_size} and saved to {part_path}")
    
    combined_tts_audio = AudioSegment.empty()
    for part in tts_parts:
        part_audio = AudioSegment.from_file(part)
        combined_tts_audio += part_audio
    
    combined_tts_audio.export(tts_output_path, format="mp3")
    print(f"Generated TTS audio and saved to {tts_output_path}")
    
    return tts_output_path




def combine_music_and_tts(tts_path, music_folder, output_folder, duration=780):
    final_audio_path = os.path.join(output_folder, "final_combined_audio.mp3")
    if os.path.exists(final_audio_path):
        print(f"Combined audio already exists at {final_audio_path}. Skipping music combination.")
        return final_audio_path
    
    os.makedirs(output_folder, exist_ok=True)
    
    beat_files = [file for file in os.listdir(music_folder) if file.endswith('.wav')]
    if not beat_files:
        print("No beat files found in the directory.")
        return False
    
    combined_audio = AudioSegment.silent(duration=0)
    for beat_file in beat_files:
        beat_path = os.path.join(music_folder, beat_file)
        beat_audio = AudioSegment.from_wav(beat_path)
        combined_audio += beat_audio
    
    tts_audio = AudioSegment.from_file(tts_path)
    tts_duration_ms = tts_audio.duration_seconds * 1000

    if tts_duration_ms < duration * 1000:
        silence_duration_ms = (duration * 1000) - tts_duration_ms
        silence = AudioSegment.silent(duration=silence_duration_ms)
        tts_audio = tts_audio + silence
        tts_duration_ms = duration * 1000

    if tts_duration_ms > duration * 1000:
        tts_audio = tts_audio[:duration * 1000]
        tts_duration_ms = duration * 1000


    combined_audio = combined_audio[:tts_duration_ms]
    combined_audio = combined_audio - 18  
    tts_audio = tts_audio + 6     
    final_combined = combined_audio.overlay(tts_audio)
    final_combined = final_combined.fade_in(2000).fade_out(2000)  
    final_combined.export(final_audio_path, format="mp3")
    
    return final_audio_path




def create_final_video(image_folders, audio_path, project_folder, duration=780):
    temp_video_path = os.path.join(project_folder, "temp_video.mp4")
    final_output_path = os.path.join(project_folder, f"final_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")

    if os.path.exists(final_output_path):
        print(f"Final video already exists at {final_output_path}. Skipping video creation.")
        return final_output_path

    print("Creating final video...")
    if not os.path.exists(project_folder):
        os.makedirs(project_folder)

    image_files = []
    for folder in image_folders:
        image_files += [os.path.join(folder, file) for file in os.listdir(folder) if file.endswith(('.png', '.jpg', '.jpeg'))]
    
    random.shuffle(image_files)
    selected_images = image_files[:int(duration / 60)]
    images_list_path = os.path.join(project_folder, "images_list.txt")
    with open(images_list_path, "w") as f:
        for image in selected_images:
            f.write(f"file '{os.path.abspath(image)}'\n")
            f.write(f"duration {duration / len(selected_images)}\n")
        f.write(f"file '{os.path.abspath(selected_images[-1])}'\n")  

    
    ffmpeg.input(images_list_path, format='concat', safe=0).output(
        temp_video_path,
        vcodec='libx264',
        pix_fmt='yuv420p'
    ).run()

    tts_audio = AudioSegment.from_file(audio_path)
    tts_duration_sec = tts_audio.duration_seconds

    ffmpeg.concat(ffmpeg.input(temp_video_path), ffmpeg.input(audio_path), v=1, a=1).output(
        final_output_path,
        vcodec='libx264',
        acodec='aac',
        pix_fmt='yuv420p',
        shortest=None
    ).run()

    trimmed_output_path = os.path.join(project_folder, f"final_video_trimmed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
    ffmpeg.input(final_output_path).output(
        trimmed_output_path,
        t=tts_duration_sec + 10,
        vcodec='libx264',
        acodec='aac',
        pix_fmt='yuv420p'
    ).run()

    os.remove(temp_video_path)
    os.remove(images_list_path)
    os.remove(final_output_path)
    print(f'Final video saved to "{trimmed_output_path}"')
    
    return trimmed_output_path



def process_warhammer40k_content():
    root_folder = "40K"
    music_folder = os.path.join(root_folder, "music")
    images_folder = os.path.join(root_folder, "images")
    scripts_folder = os.path.join(root_folder, "scripts")
    
    available_image_folders = {
        "1": os.path.join(images_folder, "emperor"),
        "2": os.path.join(images_folder, "mechanicus"),
        "3": os.path.join(images_folder, "siege_of_terra"),
        "4": os.path.join(images_folder, "space_battle"),
        "5": os.path.join(images_folder, "stc"),
        "6": os.path.join(images_folder, "orcs"),
        "7": os.path.join(images_folder, "filler"),
        "8": os.path.join(images_folder, "astronomican"),
        "9": os.path.join(images_folder, "warp"),
        "10": os.path.join(images_folder, "necron"),
        "11": os.path.join(images_folder, "tyranid"),
        "12": os.path.join(images_folder, "scale"),
        "13": os.path.join(images_folder, "hive")

    }
    
    print("Select image folders to use (comma separated list of numbers):")
    print("1 = emperor")
    print("2 = mechanicus")
    print("3 = siege_of_terra")
    print("4 = space_battle")
    print("5 = stc")
    print("6 = orcs")
    print("7 = filler")
    print("8 = astronomican")
    print("9 = warp")
    print("10 = necron")
    print("11 = tyranid")
    print("12 = scale")
    print("13 = hive")
    selected_image_folders = input("Enter your choice: ").split(',')
    selected_folders = [available_image_folders[choice.strip()] for choice in selected_image_folders if choice.strip() in available_image_folders]
    
    if not selected_folders:
        print("No valid folders selected. Exiting...")
        return
    
    print("Available scripts:")
    scripts = [file for file in os.listdir(scripts_folder) if file.endswith('.txt')]
    for i, script in enumerate(scripts):
        print(f"{i + 1} = {script}")
    script_choice = int(input("Select a script to use: ")) - 1
    
    if script_choice < 0 or script_choice >= len(scripts):
        print("Invalid choice. Exiting...")
        return
    
    script_path = os.path.join(scripts_folder, scripts[script_choice])
    tts_output_folder = "tts_outputs"
    project_folder = "project_final_clips"
    
    os.makedirs(tts_output_folder, exist_ok=True)
    os.makedirs(project_folder, exist_ok=True)

    tts_path = generate_tts_for_script(script_path, tts_output_folder)
    final_audio_path = combine_music_and_tts(tts_path, music_folder, project_folder)
    if final_audio_path:
        create_final_video(selected_folders, final_audio_path, project_folder)
        cleanup_folder(tts_output_folder)
        cleanup_folder(os.path.join(root_folder, "source_material"))
    else:
        print("Failed to create final audio. Exiting...")

if __name__ == "__main__":
    process_warhammer40k_content()
