import os
import random
import ffmpeg
from datetime import datetime
from pydub import AudioSegment
from pathlib import Path
from openai import OpenAI

os.environ["TOKENIZERS_PARALLELISM"] = "false"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_audio_duration(audio_path):
    probe = ffmpeg.probe(audio_path)
    duration = float(probe['format']['duration'])
    return duration

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

def combine_music_and_tts(tts_path, music_folder, output_folder):
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
    silence = AudioSegment.silent(duration=10 * 1000)  # 10 seconds of silence
    tts_audio = tts_audio + silence
    tts_duration_ms = len(tts_audio)

    combined_audio = combined_audio[:tts_duration_ms]
    combined_audio = combined_audio - 20  
    tts_audio = tts_audio + 2     
    final_combined = combined_audio.overlay(tts_audio)
    final_combined = final_combined.fade_in(2000).fade_out(2000)  
    final_combined.export(final_audio_path, format="mp3")
    
    return final_audio_path

def create_video_segment(image_path, output_path, duration=30):
    (
        ffmpeg
        .input(image_path, loop=1, t=duration)
        .filter('zoompan', z='min(zoom+0.00075,1.5)', d=duration * 25 + 100, s='1280x720')
        .filter('format', pix_fmts='yuv420p')
        .filter('fade', t='in', st=0, d=1)
        .filter('fade', t='out', st=duration-1, d=1)
        .output(output_path, vcodec='libx264', pix_fmt='yuv420p', r=25, t=duration)
        .run(overwrite_output=True)
    )

def concatenate_segments(segment_paths, output_path, audio_path=None):
    inputs = [ffmpeg.input(segment) for segment in segment_paths]
    concat_filter = ffmpeg.concat(*inputs, v=1, a=0).node
    video = concat_filter[0]

    if audio_path:
        audio = ffmpeg.input(audio_path)
        audio_duration = get_audio_duration(audio_path)
        final_audio_duration = audio_duration + 10  # Add 10 seconds of silence at the end
        audio = (
            audio
            .filter('atrim', end=audio_duration)
            .filter('apad', pad_len=10*44100)  # Assuming audio sample rate is 44100 Hz
            .filter('atrim', end=final_audio_duration)
        )
        output = ffmpeg.output(video, audio, output_path, vcodec='libx264', pix_fmt='yuv420p', acodec='aac')
    else:
        output = ffmpeg.output(video, output_path, vcodec='libx264', pix_fmt='yuv420p')

    output.run(overwrite_output=True)

def create_enhanced_video(image_folder, output_folder, audio_file=None):
    temp_video_folder = os.path.join(output_folder, "temp_segments")
    if not os.path.exists(temp_video_folder):
        os.makedirs(temp_video_folder)

    final_output_path = os.path.join(output_folder, f"final_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")

    image_files = [os.path.join(image_folder, file) for file in os.listdir(image_folder) if file.endswith(('.png', '.jpg', '.jpeg'))]

    if not image_files:
        print("No image files found in the specified folder. Exiting...")
        return

    if audio_file:
        video_duration = get_audio_duration(audio_file) + 10  # Audio duration plus 10 seconds of silence
    else:
        video_duration = 60  # Default video duration if no audio file is provided

    # Calculate the number of images needed and the display duration for each
    image_display_time = 30  # Display each image for 30 seconds
    num_images_needed = int(video_duration // image_display_time)
    remaining_time = video_duration % image_display_time

    extended_image_files = image_files * (num_images_needed // len(image_files) + 1)
    selected_images = extended_image_files[:num_images_needed]

    segment_paths = []
    for i, image in enumerate(selected_images):
        segment_path = os.path.join(temp_video_folder, f"segment_{i}.mp4")
        create_video_segment(image, segment_path, duration=image_display_time)
        segment_paths.append(segment_path)

    if remaining_time > 0:
        last_segment_path = os.path.join(temp_video_folder, f"segment_{num_images_needed}.mp4")
        create_video_segment(selected_images[-1], last_segment_path, duration=remaining_time)
        segment_paths.append(last_segment_path)

    concatenate_segments(segment_paths, final_output_path, audio_file)
    print(f"Final video saved to {final_output_path}")

def process_warhammer40k_content():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_folder = os.path.abspath(os.path.join(script_dir, '..', 'source_material', '40K'))  # Adjusted path
    music_folder = os.path.join(root_folder, "music")
    images_folder = os.path.join(root_folder, "images")
    scripts_folder = os.path.join(root_folder, "scripts")
    project_folder = os.path.join(script_dir, '..', 'finished_material', 'project_final_clips')  # Adjusted path

    temp_video_path = os.path.join(project_folder, "temp_video.mp4")
    final_audio_path = os.path.join(project_folder, "final_combined_audio.mp3")
    
    # Check if both temp_video.mp4 and final_combined_audio.mp3 exist
    if os.path.exists(temp_video_path) and os.path.exists(final_audio_path):
        print("Using existing temp_video.mp4 and final_combined_audio.mp3")
        create_enhanced_video([], final_audio_path, project_folder)
        return

    # Print paths for debugging
    print(f"Script directory: {script_dir}")
    print(f"Root folder: {root_folder}")
    print(f"Music folder: {music_folder}")
    print(f"Images folder: {images_folder}")
    print(f"Scripts folder: {scripts_folder}")
    print(f"Project folder: {project_folder}")
    
    # Ensure necessary directories exist
    if not os.path.exists(scripts_folder):
        print(f"Scripts folder not found: {scripts_folder}. Exiting...")
        return
    if not os.path.exists(music_folder):
        print(f"Music folder not found: {music_folder}. Exiting...")
        return
    if not os.path.exists(images_folder):
        print(f"Images folder not found: {images_folder}. Exiting...")
        return

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
        "13": os.path.join(images_folder, "hive"),
        "14": os.path.join(images_folder, "MYTH_gods"),
        "15": os.path.join(images_folder, "poseidon"),
        "16": os.path.join(images_folder, "zeus"),
        "17": os.path.join(images_folder, "hades"),
        "18": os.path.join(images_folder, "odin"),
        "19": os.path.join(images_folder, "thor"),
        "20": os.path.join(images_folder, "loki"),
        "21": os.path.join(images_folder, "tzneecht"),
        "22": os.path.join(images_folder, "nurgle"),
        "23": os.path.join(images_folder, "slaanesh"),
        "24": os.path.join(images_folder, "khrone")
    }
    
    print("Select image folders to use (comma separated list of numbers):")
    for key, value in available_image_folders.items():
        print(f"{key} = {os.path.basename(value)}")
    
    selected_image_folders = input("Enter your choice: ").split(',')
    selected_folders = [available_image_folders[choice.strip()] for choice in selected_image_folders if choice.strip() in available_image_folders]
    
    if not selected_folders:
        print("No valid folders selected. Exiting...")
        return
    
    print("Available scripts:")
    scripts = [file for file in os.listdir(scripts_folder) if file.endswith('.txt')]
    if not scripts:
        print("No script files found in the scripts folder. Exiting...")
        return
    for i, script in enumerate(scripts):
        print(f"{i + 1} = {script}")
    script_choice = int(input("Select a script to use: ")) - 1
    
    if script_choice < 0 or script_choice >= len(scripts):
        print("Invalid choice. Exiting...")
        return
    
    script_path = os.path.join(scripts_folder, scripts[script_choice])
    tts_output_folder = os.path.join(script_dir, '..', 'temp', 'tts_outputs')  # Adjusted path
    
    os.makedirs(tts_output_folder, exist_ok=True)
    os.makedirs(project_folder, exist_ok=True)

    tts_path = generate_tts_for_script(script_path, tts_output_folder)
    final_audio_path = combine_music_and_tts(tts_path, music_folder, project_folder)
    if final_audio_path:
        for selected_folder in selected_folders:
            create_enhanced_video(selected_folder, project_folder, final_audio_path)
        cleanup_folder(tts_output_folder)
        cleanup_folder(os.path.join(root_folder, "source_material"))
    else:
        print("Failed to create final audio. Exiting...")

if __name__ == "__main__":
    process_warhammer40k_content()
