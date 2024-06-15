import os
import random
import shutil
from datetime import datetime
from pathlib import Path
import ffmpeg
from pydub import AudioSegment


os.environ["TOKENIZERS_PARALLELISM"] = "false"



def cleanup_folder(folder):
    if os.path.exists(folder):
        shutil.rmtree(folder)



def extract_clip(video_path, output_path, start_time, clip_duration):
    if os.path.exists(output_path):
        os.remove(output_path)  
    (
        ffmpeg
        .input(video_path, ss=start_time, t=clip_duration)
        .output(output_path, vcodec='libx264', pix_fmt='yuv420p', an=None)  
        .run()
    )



def create_final_clip(video_path, instrumental_folder, temp_project_folder):
    print("Creating final clip...")
    if not os.path.exists(temp_project_folder):
        os.makedirs(temp_project_folder)

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_video_name = f"{video_name}_{timestamp}.mp4"
    final_output_path = os.path.join("finished_material/project_final_clips", output_video_name)

    clip_durations = [random.randint(8, 14) for _ in range(3)]
    start_times = sorted(random.sample(range(0, 60 - max(clip_durations)), 3))
    clip_paths = []

    for i, start_time in enumerate(start_times):
        clip_duration = clip_durations[i]
        clip_output_path = os.path.join(temp_project_folder, f"clip_{i}.mp4")
        extract_clip(video_path, clip_output_path, start_time, clip_duration)
        clip_paths.append(clip_output_path)

    for clip_path in clip_paths:
        if not os.path.exists(clip_path):
            print(f"Error: Clip not found at {clip_path}")
            return

    filelist_path = os.path.join(temp_project_folder, 'filelist.txt')
    with open(filelist_path, 'w') as f:
        for clip_path in clip_paths:
            abs_clip_path = os.path.abspath(clip_path)
            f.write(f"file '{abs_clip_path}'\n")

    with open(filelist_path, 'r') as f:
        print(f"filelist.txt content:\n{f.read()}")

    concatenated_clip_path = os.path.join(temp_project_folder, "concatenated_clip.mp4")
    try:
        ffmpeg.input(filelist_path, format='concat', safe=0).output(concatenated_clip_path, c='copy').run()  
    except ffmpeg.Error as e:
        error_message = e.stderr.decode() if e.stderr else "Unknown ffmpeg error"
        print(f"ffmpeg error: {error_message}")
        return

    video = ffmpeg.input(concatenated_clip_path)

    beat_files = [file for file in os.listdir(instrumental_folder) if file.endswith('.wav')]
    if not beat_files:
        print("No beat files found in the directory.")
        return False

    beat_path = os.path.join(instrumental_folder, random.choice(beat_files))
    beat_audio = AudioSegment.from_wav(beat_path)
    beat_audio = beat_audio - 3  

    total_duration = sum(clip_durations)
    beat_audio = beat_audio[:total_duration * 1000]  

    audio_output_path = os.path.join(temp_project_folder, "beat_audio.mp3")
    beat_audio.export(audio_output_path, format="mp3")

    audio = ffmpeg.input(audio_output_path)

    (
        ffmpeg
        .output(video, audio, final_output_path, vcodec='libx264', acodec='aac', pix_fmt='yuv420p', y=None)
        .run()
    )

    print(f'Final clip saved to "{final_output_path}"')

    
    cleanup_folder(temp_project_folder)



def process_videos(source_folder, old_source_folder, project_folder):
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
        "finished_material/project_final_clips"
    ]

    for folder in necessary_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

    if not os.path.exists(old_source_folder):
        os.makedirs(old_source_folder)

    for video_file in os.listdir(source_folder):
        video_path = os.path.join(source_folder, video_file)
        temp_project_folder = os.path.join("temp", f"temp_{os.path.splitext(video_file)[0]}")
        print(f"Processing video: {video_path}")

        try:
            create_final_clip(video_path, instrumental_folder, temp_project_folder)
        except Exception as e:
            print(f"Skipping video {video_file} due to error: {e}")
            continue

        shutil.move(video_path, os.path.join(old_source_folder, video_file))

if __name__ == "__main__":
    source_folder = input("Enter the path to the source material folder: ")
    old_source_folder = "finished_material/old_source_material"
    project_folder = "finished_material/project_final_clips"
    process_videos(source_folder, old_source_folder, project_folder)
