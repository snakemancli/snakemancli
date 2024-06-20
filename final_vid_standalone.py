import os
import random
import ffmpeg
from datetime import datetime
from pydub import AudioSegment
from pathlib import Path

def create_enhanced_video(image_folder, output_folder, video_duration=60):
    temp_video_path = os.path.join(output_folder, "temp_video.mp4")
    final_output_path = os.path.join(output_folder, f"final_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")

    if os.path.exists(final_output_path):
        print(f"Final video already exists at {final_output_path}. Skipping video creation.")
        return final_output_path

    if not os.path.exists(temp_video_path):
        print("Creating temp video...")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        image_files = [os.path.join(image_folder, file) for file in os.listdir(image_folder) if file.endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            print("No image files found in the specified folder. Exiting...")
            return

        random.shuffle(image_files)

        # Limit video duration to 1 minute (60 seconds) for faster testing
        total_duration_sec = video_duration
        image_display_time = 5  # Display each image for 5 seconds
        num_images_needed = int(total_duration_sec // image_display_time) + 1

        extended_image_files = image_files * (num_images_needed // len(image_files) + 1)
        selected_images = extended_image_files[:num_images_needed]

        # Create the video from images with fade and zoom effects
        filters = []
        for i in range(num_images_needed):
            start_time = i * image_display_time
            end_time = start_time + image_display_time
            filters.append(
                f"[{i}:v]zoompan=z='min(1.5,zoom+0.0015)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={image_display_time * 25}:s=1280x720,fade=t=in:st=0:d=1,fade=t=out:st={image_display_time-1}:d=1[v{i}];"
            )

        filter_complex = "".join(filters) + "".join(f"[v{i}]" for i in range(num_images_needed)) + f"concat=n={num_images_needed}:v=1:a=0,format=yuv420p[v]"
        input_files = [ffmpeg.input(image) for image in selected_images]

        video = ffmpeg.concat(*input_files, v=1, a=0)
        video = ffmpeg.output(video, temp_video_path, vcodec='libx264', pix_fmt='yuv420p', r=25, filter_complex=filter_complex)
        ffmpeg.run(video, overwrite_output=True)

    print(f'Final video saved to "{final_output_path}"')

    return final_output_path

# Example usage for sanity testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Create an enhanced video from images.')
    parser.add_argument('--images', type=str, required=True, help='Path to the folder containing images')
    parser.add_argument('--output', type=str, required=True, help='Path to the output folder')

    args = parser.parse_args()

    create_enhanced_video(args.images, args.output)
