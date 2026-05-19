# JSON Updater

A CLI tool that scans portfolio project images, converts them to WebP, and automatically updates `projects.json` and the JS fallback array.

## Features

- Scans `assets/images/` for new, unreferenced images
- Converts images to WebP format (keeps originals untouched)
- Interactive prompts for project metadata (title, category, tags, description, URLs)
- Updates `data/projects.json` and `js/projects.js` fallback simultaneously
- Skips SVG files and already-converted WebP images

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python updater.py
```

By default, it looks for the portfolio at `~/Portfolio-v2`. Override with:

```bash
python updater.py /path/to/portfolio
```

Or set the environment variable:

```bash
export PORTFOLIO_PATH=/path/to/portfolio
python updater.py
```

## How It Works

1. Loads existing `projects.json`
2. Scans `assets/images/` for image files not referenced by any project
3. Converts new images to WebP (quality 85)
4. Prompts you for metadata: title, category, tags, description, URLs
5. Appends new entries to `projects.json`
6. Regenerates the `fallbackProjects` array in `projects.js`

## Supported Image Formats

PNG, JPG, JPEG, WebP, GIF, SVG

## License

MIT
