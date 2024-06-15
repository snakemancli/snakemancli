import unittest
import os
import shutil
from video_downloader import main as download_videos
from snakeman import extract_frames  

class TestYouTubeDownloader(unittest.TestCase):

    def setUp(self):
        self.source_folder = "./source_material"
        self.frames_folder = "./frames"
        self.keyword = "boxing"
        os.makedirs(self.source_folder, exist_ok=True)
        os.makedirs(self.frames_folder, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.source_folder)
        shutil.rmtree(self.frames_folder)

    def test_youtube_downloader(self):
    
        download_videos(os.getenv('YOUTUBE_API_KEY'), self.keyword, self.source_folder)
        video_files = os.listdir(self.source_folder)
        clip_files = [f for f in video_files if "part" in f]

        self.assertEqual(len(clip_files), 5, "There should be 5 one-minute clips.")

       
        for clip_file in clip_files:
            clip_path = os.path.join(self.source_folder, clip_file)
            extract_frames(clip_path, self.frames_folder, duration=60, interval=2)


            frame_files = os.listdir(self.frames_folder)
            self.assertGreater(len(frame_files), 0, f"Frames should be extracted from the clip {clip_file}.")
            

            for frame_file in frame_files:
                os.remove(os.path.join(self.frames_folder, frame_file))

if __name__ == '__main__':
    unittest.main()
