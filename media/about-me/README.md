# about-me intro video

A 30-second "hi, i'm autumn" intro for people who've never met me, made with [HyperFrames](https://hyperframes.heygen.com/) and shown at the top of the profile README.

- `out/about-me.mp4`: 1920×1080, H.264 (High, yuv420p), 30 fps, 30 s, 7.2 MB
- `out/about-me-preview.gif`: the whole video at 800 px and 8 fps (4.8 MB), shown inline in the README
- `out/stills.jpg`: four frames in a 2×2 grid

| time | scene |
| --- | --- |
| 0:00 | hello: Sailor Bee, the sleepy moon and Mew. "hi, i'm autumn (but online i'm bee)", she/her, systems engineer 2 @ aws, tokyo / london |
| 0:04 | open source: Ciphey, RustScan, pyWhat and Name-That-Hash with their logos, stars and downloads, then counters for 50k+ ⭐, 4M+ downloads and 4 tools in Kali |
| 0:10 | achievements unlocked (Mew floats by): github secure open source fund 2026, 1 of 35 at the no. 10 hackathon, 9 hackathon wins, cyberchef maintainer, black hat, cvss 9.6 rce, cissp speedrun, tryhackme employee #4 |
| 0:17 | languages: 日本語 · ʻōlelo hawaiʻi · ภาษาไทย, hachidori and the hawaiian dictionaries (hibiscus + Cutiefly), Lilo & Stitch doing the hula |
| 0:23 | end card: Stitch says hi, the ʻohana line, github / blog / X links, sleeping Mew, chibi Stitch, Sailor Bee and the moon |

## Regenerate

Needs Node.js 22 or newer and `ffmpeg`/`ffprobe` on `PATH`. `--assets` also needs Python 3 with Pillow, `fontTools==4.60.1` and `brotli==1.1.0`.

```bash
media/about-me/build.sh            # lint, check, render the MP4, the preview GIF and the stills
media/about-me/build.sh --assets   # first re-cut the sprite sheets, logos and font subsets
```

Step by step:

```bash
python3 media/about-me/tools/prepare_assets.py   # writes video/assets/ and video/sprites.js
cd media/about-me/video
npx --yes hyperframes@0.8.104 preview            # live preview in the browser
npx --yes hyperframes@0.8.104 check
npx --yes hyperframes@0.8.104 render --crf 20 --output ../out/about-me.mp4
```

The script turns HyperFrames telemetry off (`HYPERFRAMES_NO_TELEMETRY=1`). To change the words, edit the scene markup in `video/index.html`. The timings are the numbers in its `<script>` (one block per scene). The composition has one variable, `twinkle` (default `true`). `build.sh` renders the preview GIF with `--variables '{"twinkle":false}'`, so the background stars hold still and the GIF stays under 5 MB. On this machine, rendering twice produced a byte-identical MP4.

## How it works

- `video/index.html` is a single HyperFrames composition: five scenes on one paused GSAP 3.14.2 timeline, registered as `window.__timelines.main`.
- The sprites are animated by the timeline rather than as `<img>` GIFs, which would play on wall-clock time and could differ between render workers. `tools/prepare_assets.py` cuts every GIF into a horizontal sprite sheet and writes each frame's duration to `video/sprites.js`. The composition then steps `background-position` on the timeline, using the original timings.
- Background stars come from a seeded PRNG (mulberry32), so every render matches.

## Sources

- Pixel art from the README (`assets/`): Sailor Bee, the moon, the bee and the hibiscus are original art drawn for this profile.
- Mew (`mew.gif`, `mew-sleep.gif`): by JFain, from the [PMD Sprite Collab](https://sprites.pmdcollab.org/#/0151), [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
- Cutiefly (`cutiefly.gif`): by baronessfaron, Mitsubachi and Emmuffin, from the [PMD Sprite Collab](https://sprites.pmdcollab.org/#/0742), [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
- Lilo & Stitch GIFs from Disney's official GIPHY channel ([giphy.com/disney](https://giphy.com/disney)): chibi Stitch `oCsBDE7QQ77HO`, hula `mVJpyylkUvu9ixSmbL`, "Hi!" `iKLQUYOwz5R3hHsEtn`. Lilo & Stitch is © Disney.
- Logos come from each project's own repo, pinned to a commit in `tools/prepare_assets.py`: RustScan and the Kali dragon (bee-san/RustScan), pyWhat, Hachidori, CyberChef (gchq/CyberChef) and the Ciphey org avatar.
- Fonts are all SIL OFL 1.1, subset to the characters the video uses. Licences are next to them in `video/assets/fonts/`.
  - Fredoka and Nunito for the text
  - DotGothic16 for the pixel captions and 日本語
  - Mali for ภาษาไทย
  - Noto Color Emoji for the emoji
- Every number on screen comes from the README and the history research: GitHub stars and download counters (PyPI, crates.io, Docker Hub, GitHub releases), Kali package pages, Cisco Talos / NVD, and skerritt.blog posts.
