import json
import random
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont




quotes_file = Path("quotes.json")
if quotes_file.exists():
    with open(quotes_file, "r") as file:
        quotes_db = json.load(file)
else:
    quotes_db = []


IMAGES_DIR = Path("source_material/boxing/boxer_images")
CAPTIONED_IMAGES_DIR = Path("finished_material/captioned_boxer_images")
if CAPTIONED_IMAGES_DIR.exists():
    shutil.rmtree(CAPTIONED_IMAGES_DIR)
CAPTIONED_IMAGES_DIR.mkdir(exist_ok=True)




def get_quotes_for_boxer(boxer_name):
    for boxer in quotes_db:
        if boxer["name"].lower() == boxer_name.lower().replace("_", " "):
            return boxer["quotes"]
    return []




def crop_center(image, target_size=1080):
    width, height = image.size
    new_width = new_height = min(width, height)

    left = (width - new_width) / 2
    top = (height - new_height) / 2
    right = (width + new_width) / 2
    bottom = (height + new_height) / 2

    cropped_image = image.crop((left, top, right, bottom))
    return cropped_image.resize((target_size, target_size))




def wrap_text(text, font, max_width, credit):
    lines = []
    words = text.split()
    while words:
        line = ''
        while words and (font.getlength(line + words[0]) <= max_width):
            line += (words.pop(0) + ' ')
        lines.append(line.strip())

    lines.append(f"- {credit}")  
    return '\n'.join(lines)




def caption_images():
    font_path = Path("fonts/Roboto-Thin.ttf").resolve()  
    font_size = 85  
    font = ImageFont.truetype(str(font_path), font_size)
    line_spacing = 15  

    for boxer_dir in IMAGES_DIR.iterdir():
        if boxer_dir.is_dir():
            boxer_name = boxer_dir.stem.replace('_', ' ').title() 
            quotes = get_quotes_for_boxer(boxer_name)
            if not quotes:
                continue

            captioned_boxer_dir = CAPTIONED_IMAGES_DIR / boxer_name
            captioned_boxer_dir.mkdir(exist_ok=True)

            for image_file in boxer_dir.glob("*.jpg"):
                with Image.open(image_file) as img:
                    img = crop_center(img)
                    draw = ImageDraw.Draw(img)
                    quote = random.choice(quotes)
                    max_width = img.width * 0.8  
                    wrapped_text = wrap_text(quote, font, max_width, boxer_name)
                    text_bbox = draw.textbbox((0, 0), wrapped_text, font=font, spacing=line_spacing)
                    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1] + (wrapped_text.count('\n') * line_spacing)
                    width, height = img.size
                    x = (width - text_width) / 2
                    y = (height - text_height) / 2  
                    
                    # semi-transparent overlay
                    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                    overlay_draw = ImageDraw.Draw(overlay)
                    margin = 10
                    box_coords = [x - margin, y - margin, x + text_width + margin, y + text_height + margin]
                    overlay_draw.rectangle(box_coords, fill=(0, 0, 0, 128))
                    img = Image.alpha_composite(img.convert('RGBA'), overlay)
                    draw = ImageDraw.Draw(img)
                    draw.text((x, y), wrapped_text, font=font, fill="white", stroke_width=3, stroke_fill="black", spacing=line_spacing)

                    captioned_image_path = captioned_boxer_dir / image_file.name
                    img.convert('RGB').save(captioned_image_path)


if __name__ == "__main__":
    caption_images()
