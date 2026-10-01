#!/usr/bin/env python3
"""Build the extra stickers used in README.md and the about-me video.

  assets/cutiefly.gif       PMD Sprite Collab Cutiefly "Idle" (row 0), CC BY-NC 4.0
  assets/stitch.gif         chibi Stitch from Disney's official GIPHY channel (oCsBDE7QQ77HO)
  assets/stitch-hula.gif    Lilo & Stitch hula from Disney's official GIPHY channel (mVJpyylkUvu9ixSmbL)

Usage: python3 tools/make_stickers.py <download dir>
The download dir needs cutiefly-Idle-Anim.png (sprite/0742 in PMDCollab/SpriteCollab) and the
two GIPHY originals saved as <id>.gif (https://media.giphy.com/media/<id>/giphy.gif).
Needs Pillow.
"""
import sys
from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
OUT = Path(__file__).resolve().parent.parent / "assets"
WHITE = (255, 255, 255, 255)


def outline(frame, px):
    """White sticker outline: grow the alpha mask by `px` pixels (square corners)."""
    alpha = frame.getchannel("A").point(lambda a: 255 if a > 0 else 0)
    grown = alpha.filter(ImageFilter.MaxFilter(2 * px + 1))
    sticker = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    sticker.paste(WHITE, mask=grown)
    sticker.alpha_composite(frame)
    return sticker


def save_gif(frames, durations, path):
    """Save RGBA frames as a looping GIF with 1-bit transparency."""
    pal_frames = []
    for f in frames:
        rgb = Image.new("RGB", f.size, (0, 0, 0))
        rgb.paste(f.convert("RGB"), mask=f.getchannel("A"))
        p = rgb.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        # Shift palette by one so index 0 can be the transparent colour.
        pal = p.getpalette()[: 255 * 3]
        idx = p.point(lambda i: i + 1)
        idx.putpalette([0, 0, 0] + pal)
        clear = f.getchannel("A").point(lambda a: 255 if a < 128 else 0)
        idx.paste(0, mask=clear)
        idx.info["transparency"] = 0
        pal_frames.append(idx)
    pal_frames[0].save(
        path, save_all=True, append_images=pal_frames[1:], duration=durations,
        loop=0, disposal=2, transparency=0, optimize=False,
    )
    print(f"{path.name}: {frames[0].size}, {len(frames)} frames, {path.stat().st_size // 1024} KB")


def sparkle(img, x, y, colour, big):
    """4-point pixel sparkle (1x pixels)."""
    pts = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
    if big:
        pts += [(-2, 0), (2, 0), (0, -2), (0, 2)]
    for dx, dy in pts:
        if 0 <= x + dx < img.width and 0 <= y + dy < img.height:
            img.putpixel((x + dx, y + dy), colour)


def cutiefly():
    sheet = Image.open(SRC / "cutiefly-Idle-Anim.png").convert("RGBA")
    fw, fh = 24, 48  # AnimData.xml: Idle FrameWidth/FrameHeight
    frames = [sheet.crop((i * fw, 0, (i + 1) * fw, fh)) for i in range(sheet.width // fw)]
    # Common crop box so the bobbing stays relative, plus room for outline + sparkles.
    box = None
    for f in frames:
        b = f.getbbox()
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    pad_x, pad_top, pad_bottom = 6, 5, 2
    w = box[2] - box[0] + 2 * pad_x
    h = box[3] - box[1] + pad_top + pad_bottom
    yellow, lilac, blue = (255, 217, 90, 255), (183, 156, 255, 255), (124, 200, 255, 255)
    out = []
    for i, f in enumerate(frames):
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        canvas.alpha_composite(f.crop(box), (pad_x, pad_top))
        canvas = outline(canvas, 1)
        # Twinkling sparkles, alternating like the hibiscus/moon ones.
        phase = (i // 3) % 2
        sparkle(canvas, 2, 4, yellow if phase else lilac, big=bool(phase))
        sparkle(canvas, w - 3, h // 2 + 2, blue if phase else yellow, big=not phase)
        if i % 4 == 0:
            canvas.putpixel((w - 4, 2), (255, 126, 182, 255))
        out.append(canvas.resize((w * 4, h * 4), Image.NEAREST))
    save_gif(out, [90] * len(out), OUT / "cutiefly.gif")


def keyed_stitch(frame, tol=28):
    """Remove the flat white background by flood-filling from the border; keep the largest blob."""
    rgb = frame.convert("RGB")
    W, H = rgb.size
    px = rgb.load()
    bg = [[False] * W for _ in range(H)]
    q = deque((x, y) for x in range(W) for y in (0, H - 1))
    q.extend((x, y) for y in range(H) for x in (0, W - 1))
    while q:
        x, y = q.popleft()
        if not (0 <= x < W and 0 <= y < H) or bg[y][x]:
            continue
        r, g, b = px[x, y]
        if min(r, g, b) < 255 - tol:
            continue
        bg[y][x] = True
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    # Largest connected foreground component (drops the small "Disney" watermark).
    seen = [[False] * W for _ in range(H)]
    best = []
    for y0 in range(H):
        for x0 in range(W):
            if bg[y0][x0] or seen[y0][x0]:
                continue
            comp, q = [], deque([(x0, y0)])
            seen[y0][x0] = True
            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < W and 0 <= ny < H and not bg[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            if len(comp) > len(best):
                best = comp
    mask = Image.new("L", (W, H), 0)
    mp = mask.load()
    for x, y in best:
        mp[x, y] = 255
    out = frame.convert("RGBA")
    out.putalpha(mask)
    return out


def stitch_sticker():
    src = Image.open(SRC / "oCsBDE7QQ77HO.gif")
    # Frames 0 (eyes open) and 1 (blink) come before the valentine text appears.
    src.seek(0)
    open_eyes = keyed_stitch(src.copy())
    src.seek(1)
    blink = keyed_stitch(src.copy())
    box = open_eyes.getbbox()
    # Scale so Stitch is 144 px wide (2x the 72 px it is shown at in the README).
    scale = 144 / (box[2] - box[0])

    def small(img):
        part = img.crop(box)
        return part.resize((round(part.width * scale), round(part.height * scale)), Image.LANCZOS)

    open_eyes, blink = small(open_eyes), small(blink)
    pad, hop = 5, 4
    frames, durations = [], []
    # A blink and a little hop: (frame, dy, ms)
    script = [(open_eyes, 0, 1600), (blink, 0, 110), (open_eyes, 0, 900), (open_eyes, -2, 120),
              (open_eyes, -hop, 140), (open_eyes, -2, 120), (open_eyes, 0, 1300), (blink, 0, 110)]
    for img, dy, ms in script:
        canvas = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad + hop), (0, 0, 0, 0))
        canvas.alpha_composite(img, (pad, pad + hop + dy))
        frames.append(outline(canvas, 3))
        durations.append(ms)
    save_gif(frames, durations, OUT / "stitch.gif")


def resized_gif(gid, width, name, keep=None, colours=128):
    src = Image.open(SRC / f"{gid}.gif")
    frames, durations = [], []
    for i in range(src.n_frames):
        if keep and i not in keep:
            continue
        src.seek(i)
        f = src.convert("RGB")
        h = round(f.height * width / f.width)
        small = f.resize((width, h), Image.LANCZOS)
        small.info = {}  # drop the source frame's transparency/background keys
        frames.append(small)
        durations.append(src.info.get("duration", 70))
    pal = frames[len(frames) // 2].quantize(colors=colours, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(OUT / name, save_all=True, append_images=q[1:], duration=durations, loop=0, optimize=True)
    print(f"{name}: {frames[0].size}, {len(q)} frames, {(OUT / name).stat().st_size // 1024} KB")


if __name__ == "__main__":
    cutiefly()
    stitch_sticker()
    resized_gif("mVJpyylkUvu9ixSmbL", 280, "stitch-hula.gif", keep=range(0, 16))
