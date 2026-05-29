"""
ImageCompressor - A Windows desktop app for compressing images for web use.
Supports JPG, PNG, WEBP, BMP, TIFF input. Outputs web-optimized JPG or WEBP.
GUI built with CustomTkinter. Image processing via Pillow.
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import customtkinter as ctk
from PIL import Image, UnidentifiedImageError


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

SUPPORTED_INPUT_FORMATS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif")
OUTPUT_FORMATS = ["JPG", "WEBP"]
APP_TITLE = "Image Compressor for Web"
APP_WIDTH = 780
APP_HEIGHT = 620

# CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ─────────────────────────────────────────────────────────────────────────────
# Compression logic
# ─────────────────────────────────────────────────────────────────────────────

def compress_image(input_path: Path, output_path: Path, quality: int, output_format: str) -> tuple[bool, str]:
    """
    Compress a single image and save it to output_path.

    Returns (success: bool, message: str).
    quality is 1–100 for JPG; for WEBP, Pillow maps it the same way.
    """
    try:
        with Image.open(input_path) as img:
            # Convert palette/transparency modes to RGB so JPG can save them
            if img.mode in ("RGBA", "LA", "P"):
                if output_format == "WEBP":
                    # WEBP supports transparency — keep RGBA
                    img = img.convert("RGBA")
                else:
                    # JPG does not support alpha — composite onto white
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                    img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            save_kwargs = {"quality": quality, "optimize": True}

            if output_format == "JPG":
                # Progressive encoding improves perceived load time on the web
                save_kwargs["progressive"] = True
                img.save(output_path, format="JPEG", **save_kwargs)
            else:
                # WEBP — method=6 gives best compression at cost of encoding time
                save_kwargs["method"] = 6
                img.save(output_path, format="WEBP", **save_kwargs)

        original_size = input_path.stat().st_size
        compressed_size = output_path.stat().st_size
        saved_pct = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        msg = f"{input_path.name}  →  {_human_size(original_size)} → {_human_size(compressed_size)}  ({saved_pct:.1f}% saved)"
        return True, msg

    except UnidentifiedImageError:
        return False, f"SKIP (not a valid image): {input_path.name}"
    except Exception as exc:
        return False, f"ERROR {input_path.name}: {exc}"


def _human_size(num_bytes: int) -> str:
    """Return a human-readable file size string."""
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


# ─────────────────────────────────────────────────────────────────────────────
# Main Application Window
# ─────────────────────────────────────────────────────────────────────────────

class ImageCompressorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.resizable(True, True)
        self.minsize(640, 520)

        # State
        self._selected_files: list[Path] = []
        self._output_folder: Path | None = None
        self._is_running = False

        self._build_ui()
        self._enable_drag_and_drop()

    # ── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # log box expands

        # ── Header ──
        header = ctk.CTkLabel(
            self,
            text="🖼  Image Compressor for Web",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        header.grid(row=0, column=0, pady=(18, 4), padx=20, sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Compress JPG · PNG · WEBP · BMP · TIFF  →  web-ready JPG or WEBP",
            font=ctk.CTkFont(size=13),
            text_color="gray60",
        )
        subtitle.grid(row=1, column=0, pady=(0, 12), padx=20, sticky="w")

        # ── Controls frame ──
        ctrl = ctk.CTkFrame(self, corner_radius=12)
        ctrl.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        ctrl.grid_columnconfigure(1, weight=1)

        # Row 0 — file / folder selectors
        ctk.CTkButton(ctrl, text="Add Files", width=110, command=self._pick_files).grid(
            row=0, column=0, padx=(14, 6), pady=(14, 6), sticky="w"
        )
        ctk.CTkButton(ctrl, text="Add Folder", width=110, command=self._pick_folder).grid(
            row=0, column=1, padx=6, pady=(14, 6), sticky="w"
        )
        ctk.CTkButton(
            ctrl, text="Clear List", width=100, fg_color="gray30",
            hover_color="gray20", command=self._clear_files
        ).grid(row=0, column=2, padx=6, pady=(14, 6), sticky="w")

        self._file_count_label = ctk.CTkLabel(ctrl, text="No files selected", text_color="gray60")
        self._file_count_label.grid(row=0, column=3, padx=10, pady=(14, 6), sticky="w")

        # Row 1 — output folder
        ctk.CTkButton(ctrl, text="Output Folder", width=110, command=self._pick_output).grid(
            row=1, column=0, padx=(14, 6), pady=6, sticky="w"
        )
        self._output_label = ctk.CTkLabel(ctrl, text="(same folder as originals)", text_color="gray60", anchor="w")
        self._output_label.grid(row=1, column=1, columnspan=3, padx=6, pady=6, sticky="ew")

        # Row 2 — quality slider
        ctk.CTkLabel(ctrl, text="Quality:").grid(row=2, column=0, padx=(14, 6), pady=6, sticky="w")
        self._quality_var = tk.IntVar(value=82)
        self._quality_slider = ctk.CTkSlider(
            ctrl, from_=1, to=100, number_of_steps=99,
            variable=self._quality_var, command=self._on_quality_change,
        )
        self._quality_slider.grid(row=2, column=1, padx=6, pady=6, sticky="ew")
        self._quality_display = ctk.CTkLabel(ctrl, text="82", width=34)
        self._quality_display.grid(row=2, column=2, padx=4, pady=6)
        ctk.CTkLabel(ctrl, text="(1 = smallest file, 100 = best quality)", text_color="gray60").grid(
            row=2, column=3, padx=6, pady=6, sticky="w"
        )

        # Row 3 — output format + compress button
        ctk.CTkLabel(ctrl, text="Output format:").grid(row=3, column=0, padx=(14, 6), pady=(6, 14), sticky="w")
        self._format_var = tk.StringVar(value="JPG")
        fmt_menu = ctk.CTkOptionMenu(ctrl, values=OUTPUT_FORMATS, variable=self._format_var, width=100)
        fmt_menu.grid(row=3, column=1, padx=6, pady=(6, 14), sticky="w")

        self._compress_btn = ctk.CTkButton(
            ctrl, text="Compress  ▶", width=140, height=36,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_compression,
        )
        self._compress_btn.grid(row=3, column=2, columnspan=2, padx=(6, 14), pady=(6, 14), sticky="e")

        # ── Progress bar ──
        self._progress_var = tk.DoubleVar(value=0.0)
        self._progress_bar = ctk.CTkProgressBar(self, variable=self._progress_var, height=12)
        self._progress_bar.grid(row=3, column=0, padx=20, pady=(0, 4), sticky="ew")
        self._progress_bar.set(0)

        self._status_label = ctk.CTkLabel(self, text="Ready.", anchor="w", text_color="gray60")
        self._status_label.grid(row=4, column=0, padx=22, pady=(0, 4), sticky="ew")

        # ── Log / results box ──
        log_frame = ctk.CTkFrame(self, corner_radius=10)
        log_frame.grid(row=5, column=0, padx=20, pady=(0, 16), sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        self._log_box = ctk.CTkTextbox(log_frame, font=ctk.CTkFont(family="Consolas", size=12), wrap="none")
        self._log_box.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self._log("Drop image files here, or use the buttons above to get started.")

    # ── Drag-and-drop (Windows TkinterDnD or fallback) ──────────────────────

    def _enable_drag_and_drop(self):
        """
        Try to enable native drag-and-drop via tkinterdnd2.
        Silently falls back to button-only mode if the library is not installed.
        """
        try:
            from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore
            # Re-parenting trick: tkinterdnd2 requires the root to be a TkinterDnD.Tk
            # Since we subclass CTk directly, we register the drop target on the log box.
            self._log_box.drop_target_register(DND_FILES)
            self._log_box.dnd_bind("<<Drop>>", self._on_drop)
            self._log("  ✔ Drag-and-drop is enabled. Drop files or folders onto this log area.")
        except Exception:
            self._log("  ℹ  Install tkinterdnd2 for drag-and-drop support (see README).")

    def _on_drop(self, event):
        """Parse the raw path string returned by tkinterdnd2."""
        raw = event.data
        # tkinterdnd2 wraps paths with spaces in braces on Windows
        paths = self.tk.splitlist(raw)
        new_files = []
        for p in paths:
            path = Path(p)
            if path.is_dir():
                new_files.extend(self._collect_from_folder(path))
            elif path.suffix.lower() in SUPPORTED_INPUT_FORMATS:
                new_files.append(path)
        self._add_files(new_files)

    # ── File / folder pickers ────────────────────────────────────────────────

    def _pick_files(self):
        paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif"),
                ("All files", "*.*"),
            ],
        )
        self._add_files([Path(p) for p in paths])

    def _pick_folder(self):
        folder = filedialog.askdirectory(title="Select Folder Containing Images")
        if folder:
            self._add_files(self._collect_from_folder(Path(folder)))

    def _pick_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self._output_folder = Path(folder)
            self._output_label.configure(text=str(self._output_folder), text_color="white")

    def _collect_from_folder(self, folder: Path) -> list[Path]:
        """Recursively collect supported image files from a folder."""
        return [
            f for f in folder.rglob("*")
            if f.is_file() and f.suffix.lower() in SUPPORTED_INPUT_FORMATS
        ]

    def _add_files(self, new_files: list[Path]):
        existing = set(self._selected_files)
        added = [f for f in new_files if f not in existing]
        self._selected_files.extend(added)
        count = len(self._selected_files)
        self._file_count_label.configure(
            text=f"{count} file{'s' if count != 1 else ''} selected",
            text_color="white" if count else "gray60",
        )
        if added:
            self._log(f"Added {len(added)} file(s).  Total: {count}")

    def _clear_files(self):
        self._selected_files.clear()
        self._file_count_label.configure(text="No files selected", text_color="gray60")
        self._progress_bar.set(0)
        self._status_label.configure(text="Ready.")
        self._log("File list cleared.")

    # ── Quality slider ───────────────────────────────────────────────────────

    def _on_quality_change(self, value):
        self._quality_display.configure(text=str(int(float(value))))

    # ── Compression orchestration ────────────────────────────────────────────

    def _start_compression(self):
        if self._is_running:
            return
        if not self._selected_files:
            messagebox.showwarning("No files", "Please select at least one image file.")
            return

        self._is_running = True
        self._compress_btn.configure(state="disabled", text="Working…")
        self._progress_bar.set(0)

        # Run on a background thread so the GUI stays responsive
        thread = threading.Thread(target=self._run_compression, daemon=True)
        thread.start()

    def _run_compression(self):
        files = list(self._selected_files)
        quality = self._quality_var.get()
        output_fmt = self._format_var.get()
        ext = ".jpg" if output_fmt == "JPG" else ".webp"
        total = len(files)
        success_count = 0
        error_count = 0

        self._log(f"\n── Starting compression: {total} file(s)  |  Quality {quality}  |  Format {output_fmt} ──")

        for idx, src in enumerate(files, start=1):
            # Resolve output path
            if self._output_folder:
                out_dir = self._output_folder
            else:
                out_dir = src.parent

            out_dir.mkdir(parents=True, exist_ok=True)
            dest = out_dir / (src.stem + "_compressed" + ext)

            ok, msg = compress_image(src, dest, quality, output_fmt)
            self._log(("  ✔ " if ok else "  ✖ ") + msg)

            if ok:
                success_count += 1
            else:
                error_count += 1

            # Update progress bar from the main thread
            progress = idx / total
            self.after(0, self._progress_bar.set, progress)
            self.after(0, self._status_label.configure, {"text": f"Processing {idx}/{total}: {src.name}"})

        summary = f"\n── Done: {success_count} succeeded, {error_count} failed ──\n"
        self._log(summary)
        self.after(0, self._status_label.configure, {"text": f"Finished. {success_count}/{total} compressed successfully."})
        self.after(0, self._compress_btn.configure, {"state": "normal", "text": "Compress  ▶"})
        self._is_running = False

    # ── Logging helper ───────────────────────────────────────────────────────

    def _log(self, message: str):
        """Append a line to the log box (thread-safe via after())."""
        def _append():
            self._log_box.configure(state="normal")
            self._log_box.insert("end", message + "\n")
            self._log_box.see("end")
            self._log_box.configure(state="disabled")

        # If called from a non-main thread, schedule on the main thread
        try:
            self.after(0, _append)
        except RuntimeError:
            pass  # window already destroyed


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = ImageCompressorApp()
    app.mainloop()
