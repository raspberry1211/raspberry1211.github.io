import os
from pathlib import Path
from PIL import Image, ExifTags
import pytesseract
import json
import hashlib

# --- CONFIG ---
BASE_DIR = Path(__file__).parent.parent / "CardImages"  # ../CardImages
OUTPUT_DIR = Path(__file__).parent.parent / "docs"      # ../docs
THUMBNAIL_SIZE = (500, 500)
CARD_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
# --------------

def get_thumb_hash():
    """Hash thumbnail size to detect changes and trigger re-gen."""
    return hashlib.md5(str(THUMBNAIL_SIZE).encode()).hexdigest()

def auto_orient_image(img):
    """Auto-rotate based on EXIF Orientation."""
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == "Orientation":
                break
        exif = img._getexif()
        if exif is not None:
            orientation_value = exif.get(orientation)
            if orientation_value == 3:
                img = img.rotate(180, expand=True)
            elif orientation_value == 6:
                img = img.rotate(270, expand=True)
            elif orientation_value == 8:
                img = img.rotate(90, expand=True)
    except Exception:
        pass
    return img

def make_thumbnail(img_path, thumb_path):
    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    if thumb_path.exists():
        # Check timestamp to avoid regenerating
        if thumb_path.stat().st_mtime >= img_path.stat().st_mtime:
            return
    try:
        with Image.open(img_path) as img:
            img = auto_orient_image(img)
            img.thumbnail(THUMBNAIL_SIZE)
            img.save(thumb_path)
            print(f"Thumbnail created: {thumb_path}")
    except Exception as e:
        print(f"Failed to create thumbnail for {img_path}: {e}")

def extract_text(img_path):
    try:
        with Image.open(img_path) as img:
            img = auto_orient_image(img)
            text = pytesseract.image_to_string(img)
            return text.strip()
    except Exception as e:
        print(f"Failed OCR for {img_path}: {e}")
        return ""

def generate_folder_page(folder_name, images):
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{folder_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: auto; }}
        h1 {{ text-align: center; }}
        .gallery {{ display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }}
        .item {{ text-align: center; max-width: 200px; }}
        img {{ max-width: 100%; height: auto; border: 1px solid #ccc; }}
        .caption {{ font-size: 0.9em; margin-top: 5px; word-wrap: break-word; }}
        a.back {{ display: block; margin: 20px auto; text-align: center; color: #007BFF; text-decoration: none; }}
    </style>
</head>
<body>
<a class="back" href="index.html">← Back to Index</a>
<h1>{folder_name}</h1>
<div class="gallery">
"""
    for img in images:
        caption = Path(img).stem
        thumb_path = f"CardImages/{folder_name}/thumbnails/{Path(img).name}"
        full_img_path = f"CardImages/{folder_name}/{Path(img).name}"
        html += f"""    <div class="item">
        <a href="{full_img_path}" target="_blank" rel="noopener noreferrer">
            <img src="{thumb_path}" alt="{caption}" loading="lazy">
        </a>
        <div class="caption">{caption}</div>
    </div>
"""
    html += """
</div>
<a class="back" href="index.html">← Back to Index</a>
</body>
</html>"""

    (OUTPUT_DIR / f"{folder_name}.html").write_text(html, encoding="utf-8")

def generate_index_page(subfolders, cards_json_filename="cards.json"):
    html = rf"""<!DOCTYPE html>
<html>
<head>
    <title>Card Gallery</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 700px; margin: auto; }}
        h1 {{ text-align: center; }}
        input[type="search"] {{
            width: 100%;
            padding: 10px;
            font-size: 1.1em;
            margin-bottom: 20px;
            box-sizing: border-box;
        }}
        ul {{
            list-style: none;
            padding: 0;
        }}
        li {{
            margin: 8px 0;
        }}
        a {{
            text-decoration: none;
            color: #007BFF;
            font-weight: bold;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .search-result {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }}
        .search-result img {{
            max-width: 60px;
            max-height: 90px;
            border: 1px solid #ccc;
        }}
        .search-result div {{
            flex: 1;
        }}
    </style>
</head>
<body>
<h1>Card Gallery</h1>
<input type="search" id="searchInput" placeholder="Search cards by name or text...">
<div id="searchResults"></div>
<ul id="folderList" style="display:block;">
"""
    for folder in subfolders:
        html += f'<li><a href="{folder}.html">{folder}</a></li>\n'

    html += rf"""
</ul>
<script>
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');
const folderList = document.getElementById('folderList');
let cards = [];

fetch('{cards_json_filename}')
  .then(res => res.json())
  .then(data => {{
    cards = data;
  }});

searchInput.addEventListener('input', () => {{
  const query = searchInput.value.trim().toLowerCase();
  if (query.length === 0) {{
    searchResults.innerHTML = '';
    folderList.style.display = 'block';
    return;
  }}

  folderList.style.display = 'none';
  const filtered = cards.filter(card => 
    card.filename.toLowerCase().includes(query) ||
    card.text.toLowerCase().includes(query)
  );

  if (filtered.length === 0) {{
    searchResults.innerHTML = '<p>No matching cards found.</p>';
    return;
  }}

  searchResults.innerHTML = filtered.map(card => `
    <div class="search-result">
      <a href="\${{card.url}}" target="_blank" rel="noopener noreferrer">
        <img src="\${{card.thumb_url}}" alt="\${{card.filename}}" loading="lazy">
      </a>
      <div>
        <strong>\${{card.filename.replace(/\\.[^/.]+$/, "")}}</strong><br>
        <small>\${{card.text.substring(0, 150).replace(/\\n/g, ' ')}}${{card.text.length > 150 ? '...' : ''}}</small>
      </div>
    </div>
  `).join('');
}});
</script>
</body>
</html>
"""
    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")

def main():
    if not BASE_DIR.exists():
        print(f"❌ CardImages folder not found at {BASE_DIR}")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)

    subfolders = [f for f in BASE_DIR.iterdir() if f.is_dir()]
    thumb_hash = hashlib.md5(str(THUMBNAIL_SIZE).encode()).hexdigest()

    all_cards = []

    for folder in subfolders:
        folder_out_thumb = OUTPUT_DIR / "CardImages" / folder.name / "thumbnails"
        folder_out_thumb.mkdir(parents=True, exist_ok=True)

        images = []
        for img_file in folder.iterdir():
            if img_file.is_file() and img_file.suffix.lower() in CARD_IMAGE_EXTS:
                thumb_file = folder_out_thumb / img_file.name
                # Generate thumbnail if missing or outdated
                if (not thumb_file.exists() or thumb_file.stat().st_mtime < img_file.stat().st_mtime):
                    try:
                        with Image.open(img_file) as img:
                            img = auto_orient_image(img)
                            img.thumbnail(THUMBNAIL_SIZE)
                            img.save(thumb_file)
                            print(f"Thumbnail created: {thumb_file}")
                    except Exception as e:
                        print(f"Failed to create thumbnail for {img_file}: {e}")

                # Extract OCR text
                text = extract_text(img_file)
                images.append(img_file.name)

                all_cards.append({
                    "folder": folder.name,
                    "filename": img_file.name,
                    "text": text,
                    "url": f"CardImages/{folder.name}/{img_file.name}",
                    "thumb_url": f"CardImages/{folder.name}/thumbnails/{img_file.name}"
                })

        generate_folder_page(folder.name, images)

    # Write cards.json
    with open(OUTPUT_DIR / "cards.json", "w", encoding="utf-8") as f:
        json.dump(all_cards, f, indent=2)

    generate_index_page([f.name for f in subfolders])

    print(f"✅ Generated gallery with OCR and search. Output in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()