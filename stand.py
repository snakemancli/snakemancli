import os
import ffmpeg
from datetime import datetime

def get_audio_duration(audio_path):
    probe = ffmpeg.probe(audio_path)
    duration = float(probe['format']['duration'])
    return duration

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

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create an enhanced video with transitions from a folder of images.")
    parser.add_argument('--images', type=str, required=True, help='Folder containing image files')
    parser.add_argument('--output', type=str, required=True, help='Output folder for the final video')
    parser.add_argument('--audio', type=str, required=False, help='Path to the audio file')

    args = parser.parse_args()

    create_enhanced_video(args.images, args.output, args.audio)
