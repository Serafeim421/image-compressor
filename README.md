# 🖼 Image Compressor for Web

A lightweight Windows desktop app that compresses images for website use — built with Python, Pillow, and CustomTkinter.

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **Drag-and-drop** files or folders directly onto the app
- **Batch processing** — compress dozens of images at once
- **Quality slider** (1–100) for fine-grained compression control
- **Output format** — choose between web-optimised JPG or WEBP
- **Non-destructive** — originals are never overwritten; compressed files get a `_compressed` suffix
- **Per-file report** — see exactly how much space was saved on each image
- **Dark mode UI** powered by CustomTkinter

---

## Supported Formats

| Input | Output |
|---|---|
| JPG / JPEG | JPG (progressive, web-optimised) |
| PNG | WEBP (with transparency support) |
| WEBP | |
| BMP | |
| TIFF / TIF | |

---

## Screenshots

> _Add screenshots here once the app is running._

---

## Download

Grab the latest standalone `.exe` from the [Releases](../../releases) page — no Python installation required.

---

## Run from Source

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/image-compressor.git
cd image-compressor

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the app
python main.py
```

---

## Build the .exe yourself

```bash
# With the venv active:
pyinstaller --noconfirm --onefile --windowed --name "ImageCompressor" ^
  --icon="icon.ico" ^
  --add-data "venv\Lib\site-packages\customtkinter;customtkinter" ^
  main.py

# Output: dist\ImageCompressor.exe
```

---

## Dependencies

| Library | Purpose |
|---|---|
| [Pillow](https://python-pillow.org/) | Image processing & compression |
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Modern dark-mode GUI |
| [tkinterdnd2](https://github.com/pmgagne/tkinterdnd2) | Drag-and-drop support |
| [PyInstaller](https://pyinstaller.org/) | Packaging into a standalone `.exe` |

---

## How Compression Works

- **JPG output** — images are saved with progressive encoding and Pillow's optimize flag, compositing any transparent layers onto a white background.
- **WEBP output** — uses method 6 (best compression) and preserves transparency from PNG/WEBP sources.
- The quality slider maps directly to Pillow's `quality` parameter (1 = smallest file, 100 = lossless-like).

---

## Project Structure

```
ImageCompressor/
├── main.py              # Application entry point
├── generate_icon.py     # Icon generation script (Pillow)
├── icon.ico             # App icon (embedded in .exe)
├── requirements.txt     # Python dependencies
├── .gitignore           # Excludes venv, build artifacts, binaries
└── README.md            # This file
```

---

## License

MIT — free to use, modify, and distribute.
