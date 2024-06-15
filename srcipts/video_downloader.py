import os
import sys
from googleapiclient.discovery import build
import yt_dlp as youtube_dl
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import ffmpeg

# Get the API key from the environment variable
API_KEY = os.getenv('YOUTUBE_API_KEY')

if not API_KEY:
    print("Error: API key not found. Please set the environment variable 'YOUTUBE_API_KEY'.")
    sys.exit(1)

def create_source_material_folder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created folder: {folder}")
    else:
        print(f"Folder already exists: {folder}")

def search_youtube_videos(api_key, keyword, max_results=50):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.search().list(
        part='snippet',
        q=keyword,
        maxResults=max_results,
        type='video',
        videoLicense='creativeCommon'
    )
    response = request.execute()
    return [(item['id']['videoId'], item['snippet']['title']) for item in response['items']]

def download_video(video_id, title, output_path):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': 'best[height<=1080]',
        'outtmpl': output_path,
        'retries': 3,
        'noprogress': True,
        'quiet': True,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            return True
        except Exception as e:
            print(f"Error downloading video {title}: {e}")
            return False

def split_video_into_clips(input_path, output_folder, clip_duration=60):
    try:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        video_duration = int(ffmpeg.probe(input_path)['format']['duration'].split('.')[0])
        end_time = min(video_duration, 300)
         
        trimmed_path = os.path.join(output_folder, f"{base_name}_trimmed.mp4")
        ffmpeg_extract_subclip(input_path, 0, end_time, targetname=trimmed_path)
        os.remove(input_path)
        print(f"Trimmed video saved as: {trimmed_path}")
        expected_clips = (end_time + clip_duration - 1) // clip_duration 
        for start_time in range(0, end_time, clip_duration):
            clip_path = os.path.join(output_folder, f"{base_name}_part_{start_time // clip_duration + 1}.mp4")
            ffmpeg_extract_subclip(trimmed_path, start_time, start_time + clip_duration, targetname=clip_path)
        
        os.remove(trimmed_path)
        print(f"Video split into {expected_clips} clips and saved to: {output_folder}")

    except Exception as e:
        print(f"Error splitting video {input_path}: {e}")

def count_clips_in_folder(folder):
    return len([f for f in os.listdir(folder) if f.endswith('.mp4')])

def main(api_key, keyword, source_folder):
    create_source_material_folder(source_folder)
    processed_videos = set()  

    while count_clips_in_folder(source_folder) < 200:
        video_urls = search_youtube_videos(api_key, keyword)
        for video_id, title in video_urls:
            if video_id in processed_videos:
                continue  
            processed_videos.add(video_id)

            output_file_name = f"{source_folder}/{title.replace(' ', '_')}.mp4"
            if download_video(video_id, title, output_file_name):
                print(f"Successfully downloaded video: {title}")
                split_video_into_clips(output_file_name, source_folder)
            else:
                print(f"Failed to download video: {title}")
            if count_clips_in_folder(source_folder) >= 200:
                break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
    else:
        keyword = input("Enter the keyword to search for: ")
    source_folder = "source_material/boxing/boxing_source_videos"
    main(API_KEY, keyword, source_folder)
