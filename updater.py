#!/usr/bin/env python3
"""Scan portfolio images, convert to WebP, and update projects.json + projects.js fallback."""

import json
import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
CATEGORIES = ["design", "web", "python", "javascript"]


def get_portfolio_root():
    """Return portfolio root directory from CLI arg or default."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).expanduser().resolve()
    env = os.environ.get("PORTFOLIO_PATH")
    if env:
        return Path(env).expanduser().resolve()
    return Path.home() / "Portfolio-v2"


def load_projects(json_path):
    """Load existing projects from JSON file."""
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_projects(json_path, projects):
    """Write projects array to JSON file."""
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)
        f.write("\n")


def scan_images(images_dir):
    """Return list of image filenames in the directory."""
    return sorted(
        f.name for f in images_dir.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS
    )


def get_referenced_images(projects):
    """Return set of image filenames already referenced by projects."""
    refs = set()
    for p in projects:
        img = p.get("image", "")
        refs.add(Path(img).name)
        # Also consider webp variant
        stem = Path(img).stem
        refs.add(stem + ".webp")
    return refs


def convert_to_webp(src_path, quality=85):
    """Convert an image to WebP format. Returns the new filename."""
    dest_path = src_path.with_suffix(".webp")
    if dest_path.exists():
        return dest_path.name
    if src_path.suffix.lower() == ".svg":
        # SVGs can't be converted with Pillow, skip
        return src_path.name
    img = Image.open(src_path)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")
    img.save(dest_path, "WEBP", quality=quality)
    print(f"  Converted: {src_path.name} -> {dest_path.name}")
    return dest_path.name


def prompt_metadata(filename):
    """Interactively collect project metadata from the user."""
    print(f"\n--- New image: {filename} ---")

    # Title
    default_title = Path(filename).stem.replace("_", " ").replace("-", " ").title()
    title = input(f"  Title [{default_title}]: ").strip()
    if not title:
        title = default_title

    # Category
    print("  Categories:")
    for i, cat in enumerate(CATEGORIES, 1):
        print(f"    {i}. {cat}")
    while True:
        choice = input("  Category number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(CATEGORIES):
            category = CATEGORIES[int(choice) - 1]
            break
        # Allow typing the name directly
        if choice.lower() in CATEGORIES:
            category = choice.lower()
            break
        print("  Invalid choice. Pick a number or type the name.")

    # Tags
    tags_input = input("  Tags (comma-separated): ").strip()
    tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []

    # Description
    description = input("  Description: ").strip()
    if not description:
        description = f"Project: {title}"

    # Optional URLs
    live_url = input("  Live URL (optional, press Enter to skip): ").strip()
    github_url = input("  GitHub URL (optional, press Enter to skip): ").strip()

    entry = {
        "title": title,
        "category": category,
        "image": f"assets/images/{filename}",
        "tags": tags,
        "description": description,
    }
    if live_url:
        entry["liveUrl"] = live_url
    if github_url:
        entry["githubUrl"] = github_url

    return entry


def js_escape(s):
    """Escape a string for safe inclusion in JavaScript source."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def format_js_fallback(projects):
    """Format projects array as a JS const declaration."""
    lines = ["const fallbackProjects = ["]
    for i, p in enumerate(projects):
        lines.append("  {")
        for key, val in p.items():
            if isinstance(val, list):
                items = ", ".join(f'"{js_escape(v)}"' for v in val)
                lines.append(f'    {key}: [{items}],')
            elif isinstance(val, str):
                lines.append(f'    {key}: "{js_escape(val)}",')
            elif isinstance(val, int):
                lines.append(f'    {key}: {val},')
        lines.append("  },")
    lines.append("];")
    return "\n".join(lines) + "\n"


def update_js_fallback(js_path, projects):
    """Replace the fallbackProjects array in projects.js."""
    content = js_path.read_text(encoding="utf-8")

    # Find the start and end of the fallback array
    start_marker = "const fallbackProjects = ["
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print(f"  Warning: Could not find '{start_marker}' in {js_path.name}")
        return

    # Find the closing ]; after the start
    bracket_count = 0
    end_idx = start_idx
    for i in range(start_idx + len(start_marker) - 1, len(content)):
        if content[i] == "[":
            bracket_count += 1
        elif content[i] == "]":
            bracket_count -= 1
            if bracket_count == 0:
                end_idx = i + 1
                break

    js_fallback = format_js_fallback(projects)
    new_content = content[:start_idx] + js_fallback + content[end_idx:]
    js_path.write_text(new_content, encoding="utf-8")


def main():
    root = get_portfolio_root()
    images_dir = root / "assets" / "images"
    json_path = root / "data" / "projects.json"
    js_path = root / "js" / "projects.js"

    if not images_dir.exists():
        print(f"Images directory not found: {images_dir}")
        sys.exit(1)
    if not json_path.exists():
        print(f"projects.json not found: {json_path}")
        sys.exit(1)
    if not js_path.exists():
        print(f"projects.js not found: {js_path}")
        sys.exit(1)

    print(f"Portfolio: {root}")

    projects = load_projects(json_path)
    all_images = scan_images(images_dir)
    referenced = get_referenced_images(projects)

    new_images = [img for img in all_images if img not in referenced]

    if not new_images:
        print("No new images found. Everything is up to date.")
        return

    print(f"Found {len(new_images)} new image(s):")
    for img in new_images:
        print(f"  - {img}")

    next_id = max((p.get("id", 0) for p in projects), default=0) + 1

    for img in new_images:
        src_path = images_dir / img

        # Convert to webp (skip SVGs)
        webp_name = convert_to_webp(src_path)

        # Collect metadata
        entry = prompt_metadata(webp_name)
        entry["id"] = next_id
        next_id += 1

        projects.append(entry)

    # Save updated projects.json
    save_projects(json_path, projects)
    print(f"\nUpdated {json_path}")

    # Update projects.js fallback
    update_js_fallback(js_path, projects)
    print(f"Updated {js_path}")

    print(f"\nDone! Added {len(new_images)} project(s).")


if __name__ == "__main__":
    main()
