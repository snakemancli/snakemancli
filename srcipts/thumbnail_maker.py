import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path

# Constants
OUTPUT_FOLDER = "./finished_material/40K_thumbnails"
FONT_PATH = "./fonts/Roboto-Thin.ttf"
TITLE_FONT_SIZE = 110
SUBTITLE_FONT_SIZE = 100
TEXT_COLOR = (255, 255, 255, 255)  # White color with full opacity
STROKE_WIDTH = 2  # Decreased stroke width
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

            # Load fonts
            title_font = ImageFont.truetype(FONT_PATH, TITLE_FONT_SIZE)
            subtitle_font = ImageFont.truetype(FONT_PATH, SUBTITLE_FONT_SIZE)

            # Calculate text size and position for title
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font, stroke_width=STROKE_WIDTH)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]

            # Calculate text size and position for subtitle
            subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font, stroke_width=STROKE_WIDTH)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]

            # Calculate total width and height for the black box with padding
            padding = 20
            box_width = max(title_width, subtitle_width) + 2 * padding
            total_height = title_height + subtitle_height + 2 * padding + 50  # 50px spacing between title and subtitle, 20px padding above and below
            box_x = (img.width - box_width) // 2
            box_y = img.height - total_height - 160  # 50 pixels from the bottom

            # Draw semi-transparent black box with blur for both title and subtitle
            black_box = Image.new("RGBA", (box_width, total_height), (0, 0, 0, 238))
            txt_img.paste(black_box, (box_x, box_y), black_box)

            # Debug: Save the black box image for inspection
            black_box.save("debug_black_box.png")
    

            # Draw title text with stroke
            title_x = (img.width - title_width) // 2
            title_y = box_y + padding  # 20 pixels padding
            draw.text((title_x, title_y), title_text, font=title_font, fill=TEXT_COLOR, stroke_width=STROKE_WIDTH, stroke_fill=TEXT_COLOR)

            # Draw subtitle text with stroke
            subtitle_x = (img.width - subtitle_width) // 2
            subtitle_y = title_y + title_height + 30  # 30 pixels padding between title and subtitle
            draw.text((subtitle_x, subtitle_y), subtitle_text, font=subtitle_font, fill=TEXT_COLOR, stroke_width=STROKE_WIDTH, stroke_fill=TEXT_COLOR)




            # black corners 
            corner_length = 90  # Length 
            corner_thickness = 7  # Thickness
            corner_color = (0, 0, 0, 255)  # Black 
            draw.rectangle([(box_x - padding, box_y - padding), (box_x - padding + corner_length, box_y - padding + corner_thickness)], fill=corner_color)  # Top left horizontal
            draw.rectangle([(box_x - padding, box_y - padding), (box_x - padding + corner_thickness, box_y - padding + corner_length)], fill=corner_color)  # Top left vertical
            draw.rectangle([(box_x + box_width + padding - corner_length, box_y - padding), (box_x + box_width + padding, box_y - padding + corner_thickness)], fill=corner_color)  # Top right horizontal
            draw.rectangle([(box_x + box_width + padding - corner_thickness, box_y - padding), (box_x + box_width + padding, box_y - padding + corner_length)], fill=corner_color)  # Top right vertical
            draw.rectangle([(box_x - padding, box_y + total_height + padding - corner_thickness), (box_x - padding + corner_length, box_y + total_height + padding)], fill=corner_color)  # Bottom left horizontal
            draw.rectangle([(box_x - padding, box_y + total_height + padding - corner_length), (box_x - padding + corner_thickness, box_y + total_height + padding)], fill=corner_color)  # Bottom left vertical
            draw.rectangle([(box_x + box_width + padding - corner_length, box_y + total_height + padding - corner_thickness), (box_x + box_width + padding, box_y + total_height + padding)], fill=corner_color)  # Bottom right horizontal
            draw.rectangle([(box_x + box_width + padding - corner_thickness, box_y + total_height + padding - corner_length), (box_x + box_width + padding, box_y + total_height + padding)], fill=corner_color)  # Bottom right vertical

           
            combined_img = Image.alpha_composite(img, txt_img)

            # RGBA to RGB 
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
