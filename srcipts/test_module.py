import unittest
import os
import shutil
from googleapiclient.discovery import build
from openai import OpenAI
from google.cloud import texttospeech
import yt_dlp as youtube_dl
import cv2
import ffmpeg
import random
from pathlib import Path
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip


def download_videos(api_key, keyword, source_folder):
    def create_source_material_folder(folder):
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created folder: {folder}")
        else:
            print(f"Folder already exists: {folder}")

    def search_youtube_videos(api_key, keyword, max_results=1):
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
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
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

            for start_time in range(0, end_time, clip_duration):
                clip_path = os.path.join(output_folder, f"{base_name}_part_{start_time // clip_duration + 1}.mp4")
                ffmpeg_extract_subclip(trimmed_path, start_time, start_time + clip_duration, targetname=clip_path)
            os.remove(trimmed_path)
            print(f"Video split into 1-minute clips and saved to: {output_folder}")

        except Exception as e:
            print(f"Error splitting video {input_path}: {e}")

    create_source_material_folder(source_folder)
    video_urls = search_youtube_videos(api_key, keyword)

    for video_id, title in video_urls:
        output_file_name = f"{source_folder}/{title.replace(' ', '_')}.mp4"
        if download_video(video_id, title, output_file_name):
            print(f"Successfully downloaded video: {title}")
            split_video_into_clips(output_file_name, source_folder)
        else:
            print(f"Failed to download video: {title}")

class TestDependenciesAndAPIs(unittest.TestCase):

    def setUp(self):
        self.source_folder = "./source_material"
        self.frames_folder = "./frames"
        self.keyword = "boxing"
        os.makedirs(self.source_folder, exist_ok=True)
        os.makedirs(self.frames_folder, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.source_folder)
        shutil.rmtree(self.frames_folder)

    def test_youtube_api(self):
        try:
            youtube = build('youtube', 'v3', developerKey=os.getenv('YOUTUBE_API_KEY'))
            request = youtube.search().list(
                part='snippet',
                q='boxing',
                maxResults=1,
                type='video',
                videoLicense='creativeCommon'
            )
            response = request.execute()
            self.assertTrue('items' in response)
        except Exception as e:
            self.fail(f"Google YouTube API test failed: {e}")

    def test_openai_api(self):
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            custom_system_message = os.getenv("CUSTOM_SYSTEM_MESSAGE", "You are a sports commentator prepared to describe legendary boxers in interviews, general demeanor, and matches. Everything you say will be text to speech over a short form video. Only speak as the video narrator.")
            response = client.chat_completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": custom_system_message},
                    {"role": "user", "content": "Test prompt max two words"}
                ],
                max_tokens=50
            )
            self.assertTrue('choices' in response)
        except Exception as e:
            self.fail(f"OpenAI API test failed: {e}")

    def test_openai_tts_api(self):
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.audio.speech.create(
                model="tts-1",
                voice="onyx",
                input="Test text"
            )
            tts_output_path = Path("test_tts_output.mp3")
            response.stream_to_file(tts_output_path)
            self.assertTrue(tts_output_path.exists())
        except Exception as e:
            self.fail(f"OpenAI TTS API test failed: {e}")

    def test_yt_dlp(self):
        try:
            ydl_opts = {
                'format': 'best[height<=1080]',
                'outtmpl': 'test_video.mp4',
                'noprogress': True,
                'quiet': True,
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download(['https://www.youtube.com/watch?v=dQw4w9WgXcQ'])
            self.assertTrue(os.path.exists('test_video.mp4'))
            os.remove('test_video.mp4')
        except Exception as e:
            self.fail(f"yt-dlp test failed: {e}")

    def extract_frames(self, video_path, output_folder, duration=60, interval=2, start_time=0):
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

        os.remove(trimmed_video_path)

    def test_youtube_downloader_and_frame_extraction(self):
        download_videos(os.getenv('YOUTUBE_API_KEY'), self.keyword, self.source_folder)
        video_files = os.listdir(self.source_folder)
        clip_files = [f for f in video_files if "part" in f]

        self.assertEqual(len(clip_files), 5, "There should be 5 one-minute clips.")

       
        for clip_file in clip_files:
            clip_path = os.path.join(self.source_folder, clip_file)
            self.extract_frames(clip_path, self.frames_folder, duration=60, interval=2)
            frame_files = os.listdir(self.frames_folder)
            self.assertGreater(len(frame_files), 0, f"Frames should be extracted from the clip {clip_file}.")
            
            for frame_file in frame_files:
                os.remove(os.path.join(self.frames_folder, frame_file))

    def test_music_selector(self):
        instrumental_folders = {
            "1": "90s_boom-bap",
            "2": "dark_instrumental",
            "3": "chill_instrumental",
            "4": "hardest_darkest",
            "5": "instrumental_instrumental"
        }

        choice = random.choice(list(instrumental_folders.keys()))
        instrumental_folder = instrumental_folders[choice]

        if not os.path.exists(instrumental_folder):
            self.skipTest(f"Instrumental folder {instrumental_folder} does not exist.")

        beat_files = [file for file in os.listdir(instrumental_folder) if file.endswith('.wav')]
        self.assertTrue(beat_files, "No beat files found in the directory.")

        for _ in range(5):
            selected_beat = random.choice(beat_files)
            print(f"Selected beat: {selected_beat}")
            self.assertTrue(selected_beat.endswith('.wav'), "Selected file is not a .wav file.")

if __name__ == '__main__':
    unittest.main()
