import os
import requests
from pathlib import Path
from time import sleep
from PIL import Image

# Set up directories
IMAGES_DIR = Path("source_material/boxing/boxer_images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Boxers and their refined search keywords
BOXERS = [
    ("Muhammad Ali", "Muhammad Ali HD"),
    ("Mike Tyson", "Mike Tyson HD"),
    ("Sugar Ray Leonard", "Sugar Ray Leonard HD"),
    ("Sonny Liston", "Sonny Liston HD"),
    ("George Foreman", "George Foreman HD"),
    ("Joe Frazier", "Joe Frazier HD")
]

# Google Custom Search API settings
API_KEY = os.getenv('YOUTUBE_API_KEY') 
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID') 
NUM_IMAGES_PER_REQUEST = 10

# Function to download images using Google Custom Search API
def download_images(query, output_dir, num_images=60):
    os.makedirs(output_dir, exist_ok=True)
    existing_images = len(list(output_dir.glob("*.jpg")))
    num_downloaded = existing_images
    start = 1

    if num_downloaded >= num_images:
        print(f"Already have {num_downloaded} images for {query}. Skipping download.")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    while num_downloaded < num_images:
        url = (
            f"https://www.googleapis.com/customsearch/v1?q={query}&searchType=image"
            f"&key={API_KEY}&cx={SEARCH_ENGINE_ID}&start={start}&num={NUM_IMAGES_PER_REQUEST}"
        )
        response = requests.get(url, headers=headers)
        data = response.json()

        if "items" not in data:
            print(f"No more images found for {query}. Downloaded {num_downloaded} images.")
            break

        for item in data["items"]:
            try:
                image_url = item["link"]
                image_response = requests.get(image_url, stream=True, headers=headers)
                image_response.raise_for_status()

                image_path = os.path.join(output_dir, f"{query.replace(' ', '_')}_{num_downloaded + 1}.jpg")
                with open(image_path, "wb") as file:
                    for chunk in image_response.iter_content(8192):
                        file.write(chunk)

                num_downloaded += 1
                if num_downloaded >= num_images:
                    break
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {image_url}: {e}")
                sleep(1) 

        start += NUM_IMAGES_PER_REQUEST

    print(f"Downloaded {num_downloaded} images for {query}.")


def crop_center(image_path, target_size=1080):
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            new_width = new_height = min(width, height)

            left = (width - new_width) / 2
            top = (height - new_height) / 2
            right = (width + new_width) / 2
            bottom = (height + new_height) / 2
            cropped_image = img.crop((left, top, right, bottom))
            cropped_image = cropped_image.resize((target_size, target_size))

    
            if cropped_image.mode == 'RGBA':
                cropped_image = cropped_image.convert('RGB')

            cropped_image.save(image_path)
    except Exception as e:
        print(f"Error processing {image_path}: {e}")


def process_images_for_boxers(boxers):
    for boxer, keywords in boxers:
        boxer_name = boxer.lower().replace(" ", "_")
        boxer_dir = IMAGES_DIR / boxer_name

        if not boxer_dir.exists() or len(list(boxer_dir.glob("*.jpg"))) < 60:
            download_images(keywords, boxer_dir)

        for image_file in boxer_dir.glob("*.jpg"):
            crop_center(image_file)
        print(f"Processed images for {boxer}")


if __name__ == "__main__":
    process_images_for_boxers(BOXERS)
