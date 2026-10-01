#!/usr/bin/env bash
# Rebuild the about-me intro video for the bee-san profile README:
#   1. (optional) regenerate sprite sheets, logos and font subsets  (--assets)
#   2. hyperframes lint + check
#   3. render the 1920x1080 MP4
#   4. render the README preview GIF (same composition, background stars held still) and stills
#
# Needs: Node.js >= 22, ffmpeg + ffprobe on PATH; for --assets also Python 3 with Pillow,
#        fontTools 4.60.1 and brotli.
# Usage: media/about-me/build.sh [--assets]
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HF="hyperframes@0.8.104"
OUT="${OUT_DIR:-$HERE/out}"
MP4="$OUT/about-me.mp4"
GIF="$OUT/about-me-preview.gif"
# Anonymous HyperFrames usage telemetry stays off unless you opt back in.
export HYPERFRAMES_NO_TELEMETRY="${HYPERFRAMES_NO_TELEMETRY:-1}"

if [[ "${1:-}" == "--assets" ]]; then
  python3 "$HERE/tools/prepare_assets.py"
else
  python3 "$HERE/tools/prepare_assets.py" --check-only   # fails if a character has no font
fi

mkdir -p "$OUT"
cd "$HERE/video"
npx --yes "$HF" browser ensure
npx --yes "$HF" lint
npx --yes "$HF" check
npx --yes "$HF" render --crf 20 --output "$MP4"

# README preview: the stars twinkle in the MP4 but hold still here, which keeps the GIF under 5 MB.
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
npx --yes "$HF" render --variables '{"twinkle":false}' --strict-variables --crf 18 --output "$TMP/preview.mp4"
ffmpeg -v error -y -i "$TMP/preview.mp4" \
  -vf "fps=8,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" \
  -loop 0 "$GIF"

# 2x2 stills for the PR / issue description
ffmpeg -v error -y -ss 2.8 -i "$MP4" -ss 8.8 -i "$MP4" -ss 15.2 -i "$MP4" -ss 21.8 -i "$MP4" \
  -filter_complex "[0]scale=960:540[a];[1]scale=960:540[b];[2]scale=960:540[c];[3]scale=960:540[d];[a][b]hstack[t];[c][d]hstack[u];[t][u]vstack" \
  -frames:v 1 -q:v 3 "$OUT/stills.jpg"

ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate -of compact "$MP4"
ls -l "$OUT"
