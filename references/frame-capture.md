# Capturing key frames

Two steps in every method: **locate** candidate moments cheaply (contact sheets / storyboards), then **capture** the exact frames at full resolution. Graphics often build up over several seconds (a spectrum gains one icon at a time) — capture the most complete state, and sometimes an intermediate one if it tells part of the story.

Where to look first: chapters whose titles promise a framework, comparison, data or an incident; transcript lines like "I have some visuals", "this slide", "here's a chart", "these are real logs"; and the first minute (news clips, product shots).

## A. Local video file (best quality, most reliable)

Needs `pip install imageio-ffmpeg` (ships its own ffmpeg) or a system `ffmpeg`.

```bash
# 1) Contact sheets to locate: one tile every 10 s, 8x6 per sheet
python3 scripts/extract_frames.py video.mp4 sheet --every 10 --out work/sheets
# narrower search inside a segment
python3 scripts/extract_frames.py video.mp4 sheet --start 40:50 --end 43:10 --every 2 --out work/sheets
# 2) Exact frames (full resolution, named by time)
python3 scripts/extract_frames.py video.mp4 grab 41:55 42:57 34:47 --out work/frames
```

Look at the sheets (Read the PNGs), pick timestamps, grab them, then rename each to `MM-SS_short-description.jpg`.

## B. Online video in a browser

Only with a browser you're allowed to drive. If it is the user's own browser (e.g. Claude in Chrome), ask first unless they already agreed and mention that playing the video may show up in their watch history. Open a new tab for it and close it when done.

Lessons that save a lot of time:

1. **Check that frames decode before anything else.** Run `await __cap(60)`, take a screenshot and look: a real frame means you can go on, even if `document.hidden` is true (some browsers still decode background tabs). A black frame, the poster image, or the same frame for different times means the tab is too far in the background — ask the user to bring that tab to the front and press play once. Background tabs also throttle timers, so expect seeks to land up to a few seconds off and contact sheets to take ~5 s per tile. An in-app/embedded browser that can't play the video at all is a dead end; switch method rather than retry.
2. **Locate with the storyboard, not by seeking.** On YouTube, `document.getElementById('movie_player').getPlayerResponse().storyboards.playerStoryboardSpecRenderer.spec` describes thumbnail sprite sheets (`|`-separated levels; each level `w#h#count#cols#rows#intervalMs#name#sigh`; URL = base with `$L` → level index and `$N` → `M<k>`, plus `&sigh=<sigh>`). Drawing those tiles onto a full-page canvas with timestamps gives you the whole video at 10-second resolution in 3–4 screenshots, with no seeking.
3. **Seeking reliably** (YouTube's MSE player): call `player.seekTo(t, true)` to make it buffer, wait until `video.buffered` covers `t`, then set `video.currentTime = t - 0.6`, `play()` until `currentTime >= t`, and `pause()`. A paused seek alone often leaves the old frame on screen.
4. **Ads** replace the `<video>` element's content (`#movie_player.ad-showing`, short `duration`). Wait them out (click a skip button if one appears) before seeking or capturing.
5. **Capture**: draw the video onto a fixed, full-viewport `<canvas>` overlay at `devicePixelRatio` scale (object-fit: contain, black background), then take a screenshot with save-to-disk. Crop the letterbox bars afterwards (macOS: `sips --cropToHeightWidth H W file.jpg`; elsewhere Pillow). Drawing a cross-origin video to canvas for display is fine; you don't need `toDataURL`.
6. **Tool timeouts**: browser JS calls often time out around 45 s. Start long loops without awaiting them (`window.__done=false; run().then(()=>window.__done=true)`), then poll `window.__done` in later calls. Don't start a second loop while one is running — they fight over the same `<video>`.

Helper code is in `assets/browser-capture.js` (defines `__seek`, `__noad`, `__cap`, `__sheetTimes`, `__storyboard` on `window`). Read the file and pass its whole text as the code of one "run JavaScript" call on the video tab; the helpers then stay available for later calls until the page reloads. Re-inject after any navigation.

Saving screenshots: with Claude in Chrome, take `computer` → `screenshot` with `save_to_disk: true`; the image is saved at the viewport size (e.g. 1512×798) and its path appears in the result as `[Image: source: …]`. Copy it into `frames/` and crop the black side bars to 16:9 — width = height × 16 / 9 (798 → 1418): `sips --cropToHeightWidth 798 1418 file.jpg` on macOS, or Pillow elsewhere. The viewport, not the video, limits resolution, so a bigger browser window gives sharper frames.

Typical sequence:
1. Inject `assets/browser-capture.js`, run `await __storyboard(0)` → screenshot; repeat with the returned `next` value to scan the video. For deciding *whether* to capture (SKILL.md step 3), one or two of these screenshots spread over the video are enough.
2. For each interesting segment: `__sheetTimes([t1, t1+2, …])` (background) → poll → screenshot to pick the best second.
3. For each pick: `await __cap(t)` → screenshot with save-to-disk → copy + crop into `frames/`.

## C. Fallback: user screenshots

Give the user a short list: `41:55 — 监管光谱完整版`, `42:57 — 各领袖定位`… and ask them to pause there and screenshot. Put the files they send into `frames/` with the naming convention.

## Never

- Download streams by deciphering signatures, spoofing clients or bypassing bot checks, or strip DRM. If a tool refuses a step on those grounds, don't look for a way around it; fall back to C.
