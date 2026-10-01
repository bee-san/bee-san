#!/usr/bin/env python3
"""Prepare the assets for the about-me HyperFrames video (media/about-me/video/assets).

  sprites/  horizontal sprite sheets cut from the README's GIFs (assets/*.gif) and from the
            Lilo & Stitch GIFs on Disney's official GIPHY channel, plus video/sprites.js, which
            lists each sheet's frame size and per-frame durations. The composition steps through
            the frames on its GSAP timeline, so playback is seekable and deterministic (an <img>
            pointing at an animated GIF would play on wall-clock time instead).
  logos/    project logos, downloaded from the projects' own repos at pinned commits
  fonts/    woff2 subsets of the fonts (all SIL OFL 1.1), pinned to google/fonts and
            googlefonts/noto-emoji commits, with their licence files

Usage: python3 media/about-me/tools/prepare_assets.py
Needs Python 3.9+, Pillow, fontTools 4.60.1 + brotli (pip install fonttools==4.60.1 brotli==1.1.0),
and network access for the first run (downloads are cached in media/about-me/.cache/, which is
git-ignored).
"""
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # only needed to (re)build assets, not for --check-only
    Image = None

HERE = Path(__file__).resolve().parent.parent  # media/about-me
REPO = HERE.parent.parent
ASSETS = HERE / "video" / "assets"
CACHE = HERE / ".cache"

GOOGLE_FONTS = "https://raw.githubusercontent.com/google/fonts/9710da1eacb3be272583c3224dcb70f9da6eadbb"
NOTO_EMOJI = "✨🐝🗼💂⚡⭐📦🔗🛡🏛🏆👑🎤🔥🏁🚀👾🌺⏱💖💻📝🐦"
DOWNLOADS = {
    # fonts
    "Fredoka-VF.ttf": f"{GOOGLE_FONTS}/ofl/fredoka/Fredoka%5Bwdth,wght%5D.ttf",
    "LICENSE-Fredoka-OFL.txt": f"{GOOGLE_FONTS}/ofl/fredoka/OFL.txt",
    "Nunito-VF.ttf": f"{GOOGLE_FONTS}/ofl/nunito/Nunito%5Bwght%5D.ttf",
    "LICENSE-Nunito-OFL.txt": f"{GOOGLE_FONTS}/ofl/nunito/OFL.txt",
    "DotGothic16-Regular.ttf": f"{GOOGLE_FONTS}/ofl/dotgothic16/DotGothic16-Regular.ttf",
    "LICENSE-DotGothic16-OFL.txt": f"{GOOGLE_FONTS}/ofl/dotgothic16/OFL.txt",
    "Mali-SemiBold.ttf": f"{GOOGLE_FONTS}/ofl/mali/Mali-SemiBold.ttf",
    "LICENSE-Mali-OFL.txt": f"{GOOGLE_FONTS}/ofl/mali/OFL.txt",
    "NotoColorEmoji.ttf": f"{NOTO_EMOJI}/2D/fonts/NotoColorEmoji.ttf",
    "LICENSE-NotoColorEmoji-OFL.txt": f"{NOTO_EMOJI}/2D/fonts/LICENSE",
    # logos (each project's own repo, pinned)
    "rustscan.png": "https://raw.githubusercontent.com/bee-san/RustScan/cfb864590161d1c8a003811dcf4846ceb8c8284f/pictures/rustscan.png",
    "kali.png": "https://raw.githubusercontent.com/bee-san/RustScan/cfb864590161d1c8a003811dcf4846ceb8c8284f/pictures/kali.png",
    "pywhat.png": "https://raw.githubusercontent.com/bee-san/pyWhat/6f82e1624b619c6c901bcc63e9aebe3654e15452/images/logo.png",
    "cyberchef.png": "https://raw.githubusercontent.com/gchq/CyberChef/d0267c3cf7691e9c2ed51e2d5071b9fd6004fcc1/src/web/static/images/cyberchef-256x256.png",
    "hachidori-icon.svg": "https://raw.githubusercontent.com/bee-san/hachidori/fd54fa503a4118e89344b9f0f40096e301438657/docs/assets/hachidori-icon.svg",
    "ciphey-org.png": "https://avatars.githubusercontent.com/u/66118688?v=4&s=240",  # github.com/Ciphey avatar
    # Lilo & Stitch, from Disney's official GIPHY channel (giphy.com/disney)
    "stitch-hula-giphy.gif": "https://media.giphy.com/media/mVJpyylkUvu9ixSmbL/giphy.gif",
    "stitch-hi-giphy.gif": "https://media.giphy.com/media/iKLQUYOwz5R3hHsEtn/giphy.gif",
}

# Every character the composition draws in each face (keeps the subsets tiny).
ASCII = "".join(chr(c) for c in range(0x20, 0x7F))
SUBSETS = {
    "Fredoka-VF.ttf": ("fredoka.woff2", ASCII + "·×’—–…"),
    "Nunito-VF.ttf": ("nunito.woff2", ASCII + "·×’—–…ʻōāēīū"),
    "DotGothic16-Regular.ttf": ("dotgothic16.woff2", ASCII + "·日本語・♡→"),
    "Mali-SemiBold.ttf": ("mali.woff2", ASCII + "ภาษาไทย→"),
}
EMOJI = "✨🐝🗼💂⚡⭐📦🔗🛡🏛🏆👑🎤🔥🏁🚀👾🌺⏱💖💻📝🐦"


def fetch(name):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / name
    if not path.exists():
        req = urllib.request.Request(DOWNLOADS[name], headers={"User-Agent": "bee-san-readme-video"})
        with urllib.request.urlopen(req, timeout=120) as resp, open(path, "wb") as fh:
            shutil.copyfileobj(resp, fh)
    return path


def gif_frames(path, keep=None):
    im = Image.open(path)
    frames, durations = [], []
    for i in range(im.n_frames):
        im.seek(i)
        if keep is not None and i not in keep:
            continue
        frames.append(im.convert("RGBA"))
        durations.append(im.info.get("duration", 100) or 100)
    return frames, durations


def write_sheet(name, frames, durations, manifest, scale=1.0, quantize=None):
    w, h = frames[0].size
    if scale != 1.0:
        w, h = round(w * scale), round(h * scale)
        frames = [f.resize((w, h), Image.LANCZOS) for f in frames]
    sheet = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * w, 0))
    out = ASSETS / "sprites" / f"{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    if quantize:
        sheet = sheet.convert("RGB").quantize(colors=quantize, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    sheet.save(out, optimize=True)
    manifest[name] = {"src": f"assets/sprites/{name}.png", "w": w, "h": h, "frames": len(frames), "durations": durations}
    print(f"sprites/{name}.png  {len(frames)} x {w}x{h}  {out.stat().st_size // 1024} KB")


def need_pillow():
    if Image is None:
        sys.exit("Pillow is needed to rebuild the assets: pip install Pillow")


def sprites():
    need_pillow()
    manifest = {}
    for name in ["sailor-bee", "moon", "bee", "hibiscus", "mew", "mew-sleep", "cutiefly", "stitch"]:
        frames, durations = gif_frames(REPO / "assets" / f"{name}.gif")
        write_sheet(name, frames, durations, manifest)
    frames, durations = gif_frames(fetch("stitch-hula-giphy.gif"), keep=range(0, 16))
    write_sheet("stitch-hula", frames, durations, manifest, quantize=128)
    frames, durations = gif_frames(fetch("stitch-hi-giphy.gif"))
    write_sheet("stitch-hi", frames, durations, manifest, quantize=128)
    js = "// Generated by tools/prepare_assets.py: sprite sheet sizes and per-frame durations (ms).\n"
    js += "window.ABOUT_ME_SPRITES = " + json.dumps(manifest, indent=1) + ";\n"
    (HERE / "video" / "sprites.js").write_text(js)


def logos():
    need_pillow()
    out = ASSETS / "logos"
    out.mkdir(parents=True, exist_ok=True)
    # RustScan: keep the laptop + shield, drop the wordmark (dark text that vanishes on dark cards).
    rs = Image.open(fetch("rustscan.png")).convert("RGBA")
    rs = rs.crop((0, 0, rs.width, int(rs.height * 0.64)))
    rs.crop(rs.getbbox()).save(out / "rustscan.png", optimize=True)
    # Ciphey org avatar: crop to the padlock + wordmark.
    ci = Image.open(fetch("ciphey-org.png")).convert("RGBA")
    ci.crop(ci.getbbox()).save(out / "ciphey.png", optimize=True)
    for name in ["pywhat.png", "cyberchef.png", "kali.png"]:
        im = Image.open(fetch(name)).convert("RGBA")
        # crop to the visible logo (pyWhat's PNG has a faint full-canvas glow around it)
        im = im.crop(im.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox())
        im.thumbnail((360, 360), Image.LANCZOS)
        if name == "kali.png":
            # the grey dragon disappears on the dark stat pill, so draw it in the video's lilac
            lilac = Image.new("RGBA", im.size, (201, 179, 255, 255))
            lilac.putalpha(im.getchannel("A"))
            im = lilac
        im.save(out / name, optimize=True)
    shutil.copy(fetch("hachidori-icon.svg"), out / "hachidori-icon.svg")
    for f in sorted(out.iterdir()):
        print(f"logos/{f.name}  {f.stat().st_size // 1024} KB")


def fonts():
    out = ASSETS / "fonts"
    out.mkdir(parents=True, exist_ok=True)
    pyft = [sys.executable, "-m", "fontTools.subset"]
    for src, (dst, chars) in SUBSETS.items():
        subprocess.run(pyft + [str(fetch(src)), f"--text={chars}", "--flavor=woff2", "--layout-features=*",
                               f"--output-file={out / dst}"], check=True)
    # Emoji: keep the sequences too (ZWJ / VS16), so subset by text with all layout features.
    subprocess.run(pyft + [str(fetch("NotoColorEmoji.ttf")), f"--text={EMOJI}\ufe0f\u200d", "--flavor=woff2",
                           "--layout-features=*", f"--output-file={out / 'noto-color-emoji.woff2'}"], check=True)
    for lic in [k for k in DOWNLOADS if k.startswith("LICENSE-")]:
        shutil.copy(fetch(lic), out / lic)
    for f in sorted(out.iterdir()):
        print(f"fonts/{f.name}  {f.stat().st_size // 1024} KB")


def check_text_coverage():
    """Fail if index.html uses a character that none of its fonts can draw."""
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        print("text coverage check skipped (pip install fonttools==4.60.1 brotli==1.1.0 to run it)")
        return
    html = (HERE / "video" / "index.html").read_text()
    text = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", html, flags=re.S)
    scripts = re.findall(r'(?:html|text):\s*"([^"]*)"', html)
    chars = set(text + "".join(scripts))
    covered = set()
    for f in (ASSETS / "fonts").glob("*.woff2"):
        covered |= {chr(c) for c in TTFont(f).getBestCmap()}
    missing = sorted(c for c in chars if c not in covered and not c.isspace() and ord(c) > 0x7F
                     and c not in "\ufe0f\u200d")
    if missing:
        sys.exit("characters with no font: " + " ".join(f"{c} U+{ord(c):04X}" for c in missing))
    print("text coverage ok")


if __name__ == "__main__":
    if "--check-only" not in sys.argv:
        sprites()
        logos()
        fonts()
    if (HERE / "video" / "index.html").exists():
        check_text_coverage()
