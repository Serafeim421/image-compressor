"""
Generates icon.ico for ImageCompressor.
Run once with: venv\Scripts\python.exe generate_icon.py
"""

from PIL import Image, ImageDraw, ImageFont
import math

def make_icon():
    sizes = [256, 128, 64, 48, 32, 16]
    frames = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        pad = max(2, size // 16)
        r = size // 10  # corner radius

        # ── Background rounded rectangle (deep blue-indigo) ──
        draw.rounded_rectangle(
            [pad, pad, size - pad, size - pad],
            radius=r,
            fill=(30, 64, 175),   # indigo-800
        )

        # ── Inner highlight strip at top (lighter blue) ──
        hl_h = max(2, size // 8)
        draw.rounded_rectangle(
            [pad, pad, size - pad, pad + hl_h],
            radius=r,
            fill=(99, 140, 255),
        )

        # ── Mountain / landscape silhouette (represents an image) ──
        cx = size / 2
        cy = size / 2

        # Sky area — white semi-transparent rectangle representing the image frame
        frame_pad = size * 0.18
        frame_rect = [frame_pad, frame_pad, size - frame_pad, size - frame_pad]
        draw.rounded_rectangle(frame_rect, radius=max(1, size // 20), fill=(255, 255, 255, 220))

        # Sun circle (top-right inside frame)
        sun_r = size * 0.09
        sun_cx = frame_rect[0] + (frame_rect[2] - frame_rect[0]) * 0.72
        sun_cy = frame_rect[1] + (frame_rect[3] - frame_rect[1]) * 0.28
        draw.ellipse(
            [sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r],
            fill=(251, 191, 36),
        )

        # Mountain polygons inside frame
        ft = frame_rect  # shorthand
        fw = ft[2] - ft[0]
        fh = ft[3] - ft[1]

        # Back mountain (lighter)
        bm = [
            ft[0] + fw * 0.15, ft[1] + fh * 0.85,
            ft[0] + fw * 0.50, ft[1] + fh * 0.35,
            ft[0] + fw * 0.78, ft[1] + fh * 0.85,
        ]
        draw.polygon(bm, fill=(148, 163, 184))

        # Front mountain (darker)
        fm2 = [
            ft[0],             ft[1] + fh * 0.85,
            ft[0] + fw * 0.35, ft[1] + fh * 0.48,
            ft[0] + fw * 0.62, ft[1] + fh * 0.85,
        ]
        draw.polygon(fm2, fill=(71, 85, 105))

        # Ground strip
        draw.rectangle(
            [ft[0], ft[1] + fh * 0.85, ft[2], ft[3]],
            fill=(100, 116, 139),
        )

        # ── Compression arrows (↔) at bottom of main tile ──
        if size >= 32:
            arrow_y = size - pad - max(3, size // 12)
            arrow_len = size * 0.22
            arrow_cx = size / 2
            lw = max(1, size // 32)

            # Left arrow  ←
            draw.line(
                [(arrow_cx - size * 0.06, arrow_y),
                 (arrow_cx - size * 0.06 - arrow_len, arrow_y)],
                fill=(255, 255, 255, 200), width=lw,
            )
            ah = max(2, size // 20)
            ax = arrow_cx - size * 0.06 - arrow_len
            draw.polygon(
                [(ax, arrow_y), (ax + ah, arrow_y - ah // 2), (ax + ah, arrow_y + ah // 2)],
                fill=(255, 255, 255, 200),
            )

            # Right arrow  →
            draw.line(
                [(arrow_cx + size * 0.06, arrow_y),
                 (arrow_cx + size * 0.06 + arrow_len, arrow_y)],
                fill=(255, 255, 255, 200), width=lw,
            )
            ax2 = arrow_cx + size * 0.06 + arrow_len
            draw.polygon(
                [(ax2, arrow_y), (ax2 - ah, arrow_y - ah // 2), (ax2 - ah, arrow_y + ah // 2)],
                fill=(255, 255, 255, 200),
            )

        frames.append(img)

    frames[0].save(
        "icon.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print("icon.ico created successfully.")

if __name__ == "__main__":
    make_icon()
