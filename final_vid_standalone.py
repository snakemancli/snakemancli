import os
import random
from datetime import datetime
from pydub import AudioSegment
import ffmpeg

def create_final_video(image_folders, audio_path, project_folder):
    temp_video_path = os.path.join(project_folder, "temp_video.mp4")
    final_output_path = os.path.join(project_folder, f"final_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")

    if os.path.exists(final_output_path):
        print(f"Final video already exists at {final_output_path}. Skipping video creation.")
        return final_output_path

    if not os.path.exists(temp_video_path):
        print("Creating temp video...")
        if not os.path.exists(project_folder):
            os.makedirs(project_folder)

        image_files = []
        for folder in image_folders:
            image_files += [os.path.join(folder, file) for file in os.listdir(folder) if file.endswith(('.png', '.jpg', '.jpeg'))]

        random.shuffle(image_files)

        tts_audio = AudioSegment.from_file(audio_path)
        tts_duration_sec = tts_audio.duration_seconds

        # Calculate the total number of images needed and repeat the images list to cover the entire duration
        image_display_time = 120  # Display each image for 120 seconds
        num_images_needed = int(tts_duration_sec // image_display_time) + 1
        extended_image_files = image_files * (num_images_needed // len(image_files) + 1)
        selected_images = extended_image_files[:num_images_needed]

        images_list_path = os.path.join(project_folder, "images_list.txt")
        with open(images_list_path, "w") as f:
            for image in selected_images:
                f.write(f"file '{os.path.abspath(image)}'\n")
                f.write(f"duration {image_display_time}\n")
            f.write(f"file '{os.path.abspath(selected_images[-1])}'\n")  # Last image to persist for duration

        # Create the video from images
        ffmpeg.input(images_list_path, format='concat', safe=0).output(
            temp_video_path,
            vcodec='libx264',
            pix_fmt='yuv420p',
            r=25
        ).run()

    # Combine the video with the TTS audio
    print("Combining video with audio...")
    ffmpeg.input(temp_video_path).input(audio_path).output(
        final_output_path,
        vcodec='libx264',
        acodec='aac',
        pix_fmt='yuv420p',
        shortest=1
    ).run(overwrite_output=True)

    os.remove(images_list_path)
    print(f'Final video saved to "{final_output_path}"')

    return final_output_path

# Example usage
if __name__ == "__main__":
    image_folders = ["/home/vandross/project/snakeman_2/source_material/40K/images/hades"]
    audio_path = "/home/vandross/project/snakeman_2/finished_material/project_final_clips/final_combined_audio.mp3"
    project_folder = "/home/vandross/project/snakeman_2/finished_material/project_final_clips"
    create_final_video(image_folders, audio_path, project_folder)
