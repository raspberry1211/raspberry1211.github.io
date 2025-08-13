import os
from pathlib import Path
from PIL import Image

# --- CONFIG ---
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
BASE_DIR = Path(".") / "CardImages"  # Look inside CardImages folder
OUTPUT_DIR = Path(".")               # HTML files go here
THUMBNAIL_SIZE = (300, 300)           # Max width, height
# --------------

def make_thumbnail(src_path, thumb_path):
    """Create a thumbnail if missing or outdated."""
    thumb_path.parent.mkdir(exist_ok=True)
    
    if thumb_path.exists():
        # Skip if thumbnail is newer than original
        if thumb_path.stat().st_mtime >= src_path.stat().st_mtime:
            return  # No need to recreate
    
    try:
        img = Image.open(src_path)
        img.thumbnail(THUMBNAIL_SIZE)
        img.save(thumb_path)
        print(f"🖼️ Made thumbnail: {thumb_path}")
    except Exception as e:
        print(f"⚠️ Could not make thumbnail for {src_path}: {e}")

def generate_index(subfolders):
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Image Gallery</title>
<style>
    body { font-family: Arial, sans-serif; text-align: center; margin: 20px; }
    h1 { margin-bottom: 20px; }
    ul { list-style: none; padding: 0; }
    li { margin: 10px 0; }
    a { text-decoration: none; color: #007BFF; font-size: 1.2em; }
    a:hover { text-decoration: underline; }
</style>
</head>
<body>
<h1>Image Gallery</h1>
<ul>
"""
    for folder in subfolders:
        html += f'    <li><a href="{folder}.html">{folder}</a></li>\n'

    html += """</ul>
</body>
</html>"""
    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")


def generate_folder_page(folder, images):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{folder}</title>
<style>
    body {{ font-family: Arial, sans-serif; text-align: center; margin: 20px; }}
    h1 {{ margin-bottom: 20px; }}
    .gallery {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; }}
    .item {{ max-width: 200px; }}
    img {{ width: 100%; height: auto; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }}
    .caption {{ margin-top: 8px; font-size: 0.9em; color: #555; word-wrap: break-word; }}
    a.back {{ display: inline-block; margin-bottom: 20px; text-decoration: none; color: #007BFF; }}
</style>
</head>
<body>
<a class="back" href="index.html">← Back to Index</a>
<h1>{folder}</h1>
<div class="gallery">
"""
    for img in images:
        thumb_path = f"CardImages/{folder}/thumbnails/{img}"
        full_img_path = f"CardImages/{folder}/{img}"
        html += f"""    <div class="item">
        <a href="{full_img_path}" target="_blank">
            <img src="{thumb_path}" alt="{img}" loading="lazy">
        </a>
        <div class="caption">{img}</div>
    </div>
"""

    html += """</div>
</body>
</html>"""

    (OUTPUT_DIR / f"{folder}.html").write_text(html, encoding="utf-8")


def main():
    if not BASE_DIR.exists():
        print(f"❌ Folder {BASE_DIR} not found.")
        return
    
    subfolders = []
    for entry in sorted(BASE_DIR.iterdir()):
        if entry.is_dir():
            images = sorted([
                f.name for f in entry.iterdir()
                if f.suffix.lower() in IMAGE_EXTENSIONS and not f.name.startswith("thumbnails")
            ])
            if images:
                subfolders.append(entry.name)
                # Create thumbnails only if missing or outdated
                for img_name in images:
                    src = entry / img_name
                    thumb = entry / "thumbnails" / img_name
                    make_thumbnail(src, thumb)
                generate_folder_page(entry.name, images)

    generate_index(subfolders)
    print(f"✅ Generated gallery with lazy-loaded thumbnails for {len(subfolders)} folders in {BASE_DIR}.")


if __name__ == "__main__":
    main()