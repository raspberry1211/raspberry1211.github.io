import os
from pathlib import Path
from PIL import Image
import numpy as np
import shutil
import json
import pytesseract

# Adjust these paths if needed
SOURCE_DIR = Path("CardImages")
OUTPUT_DIR = Path("docs")
THUMBNAIL_SIZE = (200, 300)  # tweak as needed

def extract_ocr_text(image_path):
    img = Image.open(image_path)
    raw_text = pytesseract.image_to_string(img)
    # Replace all newlines (and other whitespace sequences) with single spaces
    clean_text = ' '.join(raw_text.split())
    return clean_text

def get_top_right_color(img_path, crop_size=(30, 30)):
    img = Image.open(img_path).convert("RGB")
    width, height = img.size
    crop = img.crop((width - crop_size[0], 0, width, crop_size[1]))
    arr = np.array(crop)
    mean_color = arr.mean(axis=(0, 1))
    hex_color = '#{:02x}{:02x}{:02x}'.format(int(mean_color[0]), int(mean_color[1]), int(mean_color[2]))
    return hex_color

def create_thumbnail(src_path, dest_path):
    img = Image.open(src_path)
    img.thumbnail(THUMBNAIL_SIZE)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest_path)

def copy_file_if_newer(src_path, dest_path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if not dest_path.exists() or src_path.stat().st_mtime > dest_path.stat().st_mtime:
        shutil.copy2(src_path, dest_path)

def generate_cards_json_and_copy_images():
    cards = []
    for folder in SOURCE_DIR.iterdir():
        if not folder.is_dir():
            continue

        thumb_dir = OUTPUT_DIR / "CardImages" / folder.name / "thumbnails"
        thumb_dir.mkdir(parents=True, exist_ok=True)

        for img_file in folder.iterdir():
            if not img_file.is_file() or img_file.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
                continue

            # Generate thumbnail
            thumb_path = thumb_dir / img_file.name
            create_thumbnail(img_file, thumb_path)

            # Copy full image to docs/CardImages
            full_img_out = OUTPUT_DIR / "CardImages" / folder.name / img_file.name
            copy_file_if_newer(img_file, full_img_out)

            # Extract OCR text
            ocr_text = extract_ocr_text(img_file)

            # Extract top-right corner color
            color = get_top_right_color(img_file)
            

            cards.append({
                "filename": img_file.name,
                "url": f"CardImages/{folder.name}/{img_file.name}",
                "thumb_url": f"CardImages/{folder.name}/thumbnails/{img_file.name}",
                "text": ocr_text,
                "color": color
            })

    # Save JSON file
    OUTPUT_DIR.mkdir(exist_ok=True)
    json_path = OUTPUT_DIR / "cards.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2)
    return cards

def generate_index_page(subfolders, cards_json_filename="cards.json"):
    html = r"""<!DOCTYPE html>
<html>
<head>
    <title>Card Gallery</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 700px; margin: auto; }
        h1 { text-align: center; }
        input[type="search"] {
            width: 100%;
            padding: 10px;
            font-size: 1.1em;
            margin-bottom: 10px;
            box-sizing: border-box;
        }
        button#backButton {
            display: none;
            margin-bottom: 20px;
            padding: 8px 15px;
            font-size: 1em;
            cursor: pointer;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 4px;
        }
        button#backButton:hover {
            background-color: #0056b3;
        }
        ul {
            list-style: none;
            padding: 0;
        }
        li {
            margin: 8px 0;
        }
        a {
            text-decoration: none;
            color: #007BFF;
            font-weight: bold;
        }
        a:hover {
            text-decoration: underline;
        }
        .search-result {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }
        .search-result img {
            max-width: 60px;
            max-height: 90px;
            border: 1px solid #ccc;
        }
        .search-result div {
            flex: 1;
        }
        /* Colored card titles with subtle shadow for readability */
        strong {
            font-weight: 700;
            text-shadow: 0 0 3px rgba(0,0,0,0.6);
        }
    </style>
</head>
<body>
<h1>Card Gallery</h1>
<input type="search" id="searchInput" placeholder="Search cards by name or text...">
<button id="backButton">⬅ Back</button>
<div id="searchResults"></div>
<ul id="folderList" style="display:block;">
"""
    for folder in subfolders:
        html += f'<li><a href="{folder}.html">{folder}</a></li>\n'

    html += r"""
</ul>
<script>
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');
const folderList = document.getElementById('folderList');
const backButton = document.getElementById('backButton');
let cards = [];

fetch('""" + cards_json_filename + r"""')
  .then(res => res.json())
  .then(data => {
    cards = data;
  });

searchInput.addEventListener('input', () => {
  const query = searchInput.value.trim().toLowerCase();
  if (query.length === 0) {
    searchResults.innerHTML = '';
    folderList.style.display = 'block';
    backButton.style.display = 'none';
    return;
  }

  folderList.style.display = 'none';
  backButton.style.display = 'inline-block';

  const filtered = cards.filter(card =>
    card.filename.toLowerCase().includes(query) ||
    card.text.toLowerCase().includes(query)
  );

  if (filtered.length === 0) {
    searchResults.innerHTML = '<p>No matching cards found.</p>';
    return;
  }

  searchResults.innerHTML = filtered.map(card => `
    <div class="search-result">
      <a href="${card.url}" target="_blank" rel="noopener noreferrer">
        <img src="${card.thumb_url}" alt="${card.filename}" loading="lazy">
      </a>
      <div>
        <strong style="color: ${card.color}">${card.filename.replace(/\.[^/.]+$/, "")}</strong><br>
        <small>${card.text.substring(0, 150).replace(/\n/g, ' ')}${card.text.length > 150 ? '...' : ''}</small>
      </div>
    </div>
  `).join('');
});

backButton.addEventListener('click', () => {
  searchInput.value = '';
  searchInput.dispatchEvent(new Event('input'));
  searchInput.focus();
});
</script>
</body>
</html>
"""
    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")

def generate_gallery_pages(cards):
    from collections import defaultdict
    # Group cards by folder name extracted from their URL: "CardImages/folder/image.png"
    cards_by_folder = defaultdict(list)
    for card in cards:
        parts = card['url'].split('/')
        if len(parts) >= 3:
            folder_name = parts[1]
            cards_by_folder[folder_name].append(card)

    for folder_name, folder_cards in cards_by_folder.items():
        html = rf"""<!DOCTYPE html>
<html>
<head>
    <title>{folder_name} Gallery</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: auto; }}
        h1 {{ text-align: center; }}
        .card-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            justify-content: center;
        }}
        .card {{
            border: 1px solid #ccc;
            border-radius: 5px;
            width: 180px;
            padding: 10px;
            box-sizing: border-box;
            text-align: center;
            background: #fafafa;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
        }}
        .card img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #999;
            border-radius: 3px;
        }}
        .card h3 {{
            margin: 8px 0 4px 0;
            font-weight: 700;
            text-shadow: 0 0 1px rgba(0,0,0,0.6);
        }}
        .card p {{
            font-size: 0.9em;
            color: #333;
            max-height: 60px;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        a.back-link {{
            display: inline-block;
            margin: 15px 0;
            font-weight: bold;
            color: #007BFF;
            text-decoration: none;
        }}
        a.back-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <a href="index.html" class="back-link">&larr; Back to all sets</a>
    <h1>{folder_name} Gallery</h1>
    <div class="card-container">
"""

        # Add each card's thumbnail and info
        for card in folder_cards:
            # Escape any HTML special characters in text if needed (optional)
            safe_filename = card['filename'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            safe_text = card['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', ' ')

            html += rf"""
        <div class="card">
            <a href="{card['url']}" target="_blank" rel="noopener noreferrer">
                <img src="{card['thumb_url']}" alt="{safe_filename}" loading="lazy">
            </a>
            <h3 style="color: {card['color']}">{safe_filename.replace(r'\.[^/.]+$', '').replace('.png', '')}</h3>
            <p>{safe_text[:150]}{'...' if len(safe_text) > 150 else ''}</p>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""

        # Write out the gallery page file
        filename = OUTPUT_DIR / f"{folder_name}.html"
        filename.write_text(html, encoding="utf-8")

def main():
    # Step 1: Process all images and generate cards.json
    print("Processing images and generating cards.json...")
    cards = generate_cards_json_and_copy_images()

    # Step 2: Get all subfolder names to generate index links
    subfolders = [f.name for f in SOURCE_DIR.iterdir() if f.is_dir()]
    print("Generating index.html page...")
    generate_index_page(subfolders)
    print("Generating gallery pages per folder...")
    generate_gallery_pages(cards)

    print("Done! Your site is generated in the 'docs/' folder.")

if __name__ == "__main__":
    main()