import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Constants
OUTPUT_FOLDER = "./finished_material/40K_thumbnails"
FONT_PATH = "./fonts/Roboto-Thin.ttf"
FONT_SIZE = 100
TEXT_COLOR = (255, 255, 255, 255)  # White color with full opacity
ROUNDED_CORNER_RADIUS = 50
IMAGE_SIZE = (1280, 720)  # New size for the thumbnails

def create_rounded_thumbnail(image_path, output_path, title_text, subtitle_text):
    try:
        # Open image and resize
        with Image.open(image_path).convert("RGBA") as img:
            img = img.resize(IMAGE_SIZE)

            # Create rounded mask
            mask = Image.new("L", img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle([(0, 0), img.size], ROUNDED_CORNER_RADIUS, fill=255)

            # Apply mask to image
            img.putalpha(mask)

            # Create an image with transparent background for the text overlay
            txt_img = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_img)

            # Load font
            font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
            subtitle_font = font  # Same font size for subtitle

            # Calculate text size and position for title
            title_bbox = draw.textbbox((0, 0), title_text, font=font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]

            # Calculate text size and position for subtitle
            subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]

            # Calculate total width and height for the black box
            box_width = max(title_width, subtitle_width) + 40  # 20px padding on each side
            total_height = title_height + subtitle_height + 100  # 50px spacing between title and subtitle, 10px padding above and below
            box_x = (img.width - box_width) // 2
            box_y = img.height - total_height - 160  # 50 pixels from the bottom

            # Draw semi-transparent black box for both title and subtitle
            draw.rectangle(
                [(box_x, box_y), (box_x + box_width, box_y + total_height)],
                fill=(0, 0, 0, 128)
            )

            # Draw title text
            title_x = (img.width - title_width) // 2
            title_y = box_y + 10  # 10 pixels padding
            draw.text((title_x, title_y), title_text, font=font, fill=TEXT_COLOR)

            # Draw subtitle text
            subtitle_x = (img.width - subtitle_width) // 2
            subtitle_y = title_y + title_height + 35  # 50 pixels padding between title and subtitle
            draw.text((subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=TEXT_COLOR)

            # Combine the image with the text overlay
            combined_img = Image.alpha_composite(img, txt_img)

            # Convert RGBA to RGB before saving
            combined_img = combined_img.convert("RGB")

            # Save the final thumbnail
            combined_img.save(output_path, format="JPEG")
            print(f"Thumbnail saved to {output_path}")

    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def create_thumbnails_from_folder(images_folder, title_text, subtitle_text):
    # Ensure output folder exists
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Process each image in the folder
    for image_file in os.listdir(images_folder):
        if image_file.endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(images_folder, image_file)
            output_path = os.path.join(OUTPUT_FOLDER, f"thumbnail_{image_file}")
            create_rounded_thumbnail(image_path, output_path, title_text, subtitle_text)

def main():
    print("Debug: Starting the thumbnail maker script.")  # Debug print
    images_folder = input("Enter the path to the images folder: ")
    print(f"Debug: images_folder = {images_folder}")  # Debug print
    title_text = input("Enter the title text for the thumbnails: ")
    print(f"Debug: title_text = {title_text}")  # Debug print
    subtitle_text = input("Enter the subtitle text for the thumbnails: ")
    print(f"Debug: subtitle_text = {subtitle_text}")  # Debug print

    create_thumbnails_from_folder(images_folder, title_text, subtitle_text)

if __name__ == "__main__":
    main()
