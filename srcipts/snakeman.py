import os
import random
import shutil
import cv2
from datetime import datetime
from PIL import Image
from pathlib import Path
import ffmpeg
from pydub import AudioSegment
from transformers import pipeline
from openai import OpenAI

os.environ["TOKENIZERS_PARALLELISM"] = "false"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
image_to_text_model = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")

TEMP_DIR = "temp"

def cleanup_folder(folder, exclude=[]):
    if os.path.exists(folder):
        for file in os.listdir(folder):
            if file not in exclude:
                file_path = os.path.join(folder, file)
                os.remove(file_path)
    else:
        os.makedirs(folder)

def extract_frames(video_path, output_folder, duration=60, interval=2, start_time=0):
    print(f"Extracting frames from {start_time} seconds...")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    trimmed_video_path = os.path.join(output_folder, os.path.basename(video_path))
    (
        ffmpeg
        .input(video_path, ss=start_time, t=duration)
        .output(trimmed_video_path, vcodec='libx264', pix_fmt='yuv420p')
        .run()
    )

    cap = cv2.VideoCapture(trimmed_video_path)
    frame_count = 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    interval_frames = int(fps * interval)

    success, image = cap.read()
    while success:
        if frame_count % interval_frames == 0:
            frame_filename = os.path.join(output_folder, f"frame{frame_count}.jpg")
            cropped_image = image[:720, :1280]   
            cv2.imwrite(frame_filename, cropped_image)
        success, image = cap.read()
        frame_count += 1
    cap.release()
    print(f"Extracted frames to {output_folder}")
    os.remove(trimmed_video_path)

def generate_descriptions(frames_folder, user_description, video_name):
    print("Generating descriptions for frames...")
    descriptions = []
    custom_image_prompt = "Describe the key elements in each frame, focusing on the main actions and subjects. Avoid irrelevant details like the background or clothing unless necessary for context. Describe each frame as part of a continuous sequence of events."
    context = (
        f"{user_description}\n"
        f"Video name: {video_name}\n"
        f"{custom_image_prompt}"
    )

    for frame in sorted(os.listdir(frames_folder)):
        frame_path = os.path.join(frames_folder, frame)
        image = Image.open(frame_path)
        prompt = f"{context[:500]}\nFrame description:"  
        description = image_to_text_model(image, max_new_tokens=50)[0]['generated_text']
        if not any(irrelevant in description for irrelevant in ["background", "flower", "standing next to", "lion", "wrestling", "flag", "wrestling ring", "white shirt"]):
            descriptions.append(description)
        context += f" {description}"

    return descriptions

def summarize_descriptions(descriptions, user_description="", video_name="", duration=60):
    print("Summarizing descriptions...")
    concatenated_text = user_description + " " + " ".join(descriptions)
    max_summary_characters = 700 
    if len(concatenated_text) > max_summary_characters:
        concatenated_text = concatenated_text[:max_summary_characters]

    custom_system_message = (
        "You are a sports narrator narrating for legendary boxers. Never metaspeak. "
        "Everything you say will be text to speech over a short form video. "
        "Only speak as the video narrator. Never mention video length or timestamps. "
        "What follows are image AI descriptions of frames. Please keep the summary concise to fit within 50 seconds of speech."
    )
    
    prompt = (
        f"Video name: {video_name}\n"
        f"{custom_system_message}\n"
        f"{concatenated_text}"
    )

    print(f"Sending prompt to OpenAI:\n{prompt}")

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": custom_system_message},
            {"role": "user", "content": prompt}
        ],
        model="gpt-4o"
    )
    summary = response.choices[0].message.content
    return summary

def generate_tts_for_summary(summary, tts_output_folder, instrumental_folder, duration):
    os.makedirs(tts_output_folder, exist_ok=True)
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    tts_output_path = os.path.join(tts_output_folder, "summary_tts.mp3")
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=summary
    )
    response.stream_to_file(Path(tts_output_path))
    print(f"Generated TTS audio and saved to {tts_output_path}")

    beat_files = [file for file in os.listdir(instrumental_folder) if file.endswith('.wav')]
    if not beat_files:
        print("No beat files found in the directory.")
        return False
    
    beat_path = os.path.join(instrumental_folder, random.choice(beat_files))
    beat_audio = AudioSegment.from_wav(beat_path)
    beat_wav_path = os.path.join(tts_output_folder, "selected_beat.wav")
    beat_audio.export(beat_wav_path, format="wav")

    tts_audio = AudioSegment.from_file(tts_output_path)
    tts_duration_ms = tts_audio.duration_seconds * 1000

    if tts_duration_ms < duration * 1000:
        silence_duration_ms = (duration * 1000) - tts_duration_ms
        silence = AudioSegment.silent(duration=silence_duration_ms)
        tts_audio = tts_audio + silence
        tts_duration_ms = duration * 1000

    if tts_duration_ms > duration * 1000:
        tts_audio = tts_audio[:duration * 1000]
        tts_duration_ms = duration * 1000

    beat_audio = beat_audio[:tts_duration_ms]

    beat_audio = beat_audio - 7  
    tts_audio = tts_audio + 5     

    combined = beat_audio.overlay(tts_audio)
    combined_output_path = os.path.join(tts_output_folder, "combined_summary.mp3")
    combined.export(combined_output_path, format="mp3")
    
    return True

def create_final_clip(video_path, tts_output_folder, project_folder, duration):
    print("Creating final clip...")
    if not os.path.exists(project_folder):
        os.makedirs(project_folder)
    
    tts_path = os.path.join(tts_output_folder, "combined_summary.mp3")
    if not os.path.exists(tts_path):
        print(f"TTS output file not found: {tts_path}")
        return
    
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_video_name = f"{video_name}_{timestamp}.mp4"
    final_output_path = os.path.join(project_folder, output_video_name)
    final_output_temp_path = os.path.join(project_folder, "final_temp_clip.mp4")

    if os.path.exists(final_output_temp_path):
        os.remove(final_output_temp_path)

    (
        ffmpeg
        .input(video_path, ss=0, t=duration)
        .filter('crop', 'in_h*9/16', 'in_h')
        .filter('scale', 1080, 1920)  
        .output(final_output_temp_path, vcodec='libx264', pix_fmt='yuv420p')
        .run()
    )
    
    video = ffmpeg.input(final_output_temp_path)
    audio = ffmpeg.input(tts_path)

    (
        ffmpeg
        .output(video, audio, final_output_path, vcodec='libx264', acodec='aac', pix_fmt='yuv420p')
        .run()
    )

    print(f'Final clip saved to "{final_output_path}"')

def process_videos(source_folder, old_source_folder, project_folder, user_description):
    instrumental_folders = {
        "1": "music/90s_boom-bap",
        "2": "music/dark_instrumental",
        "3": "music/chill_instrumental",
        "4": "music/hardest_darkest",
        "5": "music/instrumental_instrumenta"
    }

    instrumental_choice = input(
        "Select instrumental type (1-5):\n"
        "1=90s_boom-bap\n"
        "2=dark_instrumental\n"
        "3=chill_instrumental\n"
        "4=hardest_darkest\n"
        "5=instrumental_instrumental\n"
        "Enter your choice: "
    )
    
    instrumental_folder = instrumental_folders.get(instrumental_choice)
    if not instrumental_folder:
        print("Invalid choice. Exiting...")
        return
    
    necessary_folders = [
        source_folder,
        old_source_folder,
        project_folder,
        instrumental_folder,
        TEMP_DIR
    ]
    
    for folder in necessary_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    if not os.path.exists(old_source_folder):
        os.makedirs(old_source_folder)
        
    for video_file in os.listdir(source_folder):
        video_path = os.path.join(source_folder, video_file)
        video_name = os.path.splitext(video_file)[0]
        print(f"Processing video: {video_path}")
        
        frames_folder = os.path.join(TEMP_DIR, 'frames')
        tts_output_folder = os.path.join(TEMP_DIR, 'tts_outputs')
        
        video_duration = int(ffmpeg.probe(video_path)['format']['duration'].split('.')[0])
        start_times = [i for i in range(0, video_duration, 60)]

        for start_time in start_times:
            cleanup_folder(frames_folder)
            cleanup_folder(tts_output_folder)

            extract_frames(video_path, frames_folder, duration=60, interval=2, start_time=start_time)
            descriptions = generate_descriptions(frames_folder, user_description, video_name)
            summary = summarize_descriptions(descriptions, user_description, video_name, duration=60)
            
            summary_path = os.path.join(tts_output_folder, "summary.txt")
            with open(summary_path, 'w') as f:
                f.write(summary)
            
            tts_success = generate_tts_for_summary(summary, tts_output_folder, instrumental_folder, duration=60)
            if not tts_success:
                print(f"Skipping video due to TTS error: {video_path}")
                continue
            
            create_final_clip(video_path, tts_output_folder, project_folder, duration=60)
        
        shutil.move(video_path, os.path.join(old_source_folder, video_file))

if __name__ == "__main__":
    source_folder = input("Enter the path to the source material folder: ")
    old_source_folder = "finished_material/old_source_material"
    project_folder = "finished_material/project_final_clips"
    user_description = input("Enter a brief description of the video content (optional): ")
    process_videos(source_folder, old_source_folder, project_folder, user_description)
