<div align="center">

# 🎬 → 📚 video-insight-pack

**Stop rewatching hour-long videos. Get the ideas, the charts and the flashcards in one page.**

A [Claude Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) that turns any video — a YouTube link, a local file or just subtitles — into a shareable study pack:
key insights · a mind map · a long-form article illustrated with the video's **own key frames** · flashcards · a frame gallery.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Claude Skill](https://img.shields.io/badge/Claude-Skill-d97757)](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](#requirements)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#contributing)

**English** · [简体中文](README.zh-CN.md)

<img src="docs/demo-map.png" alt="Insights and mind map generated from a 68-minute interview" width="88%">

</div>

---

## Why

A one-hour talk usually contains five ideas, three charts and a couple of numbers worth remembering. Summaries throw away the charts. Transcripts bury the ideas. Screenshots end up in your camera roll with no context.

`video-insight-pack` asks Claude to do what a good note-taker does:

- **Reads the whole transcript** before writing — the best part is often in the last third.
- **Finds the frames that explain things** (charts, framework slides, diagrams, headlines) and puts them *next to the paragraph they illustrate*.
- **Doesn't waste time on talking heads.** It checks first whether a video has anything worth capturing; for a podcast or interview it skips screenshots and **draws its own diagrams and tables** from what was said.
- **Separates claims from facts.** "5M downloads in 22 days" becomes *"according to a news clip shown in the video…"*, never an invented statistic.
- **Adds a critical reading** — what the speaker sidestepped, which claims lack evidence.
- **Turns it into flashcards** so you still remember it next week.

## What you get

One HTML page (light/dark, mobile-friendly, no build step) with four tabs:

| Tab | What's inside |
|---|---|
| **Insights & map** | 3–6 non-obvious takeaways + a mind map of the whole video, each branch time-stamped |
| **Article** | A readable long-form piece in *your* language, conclusion first, with key frames, generated diagrams (flow · layers · compare) and tables, plus a source note |
| **Flashcards** | 12–25 flip cards with timestamps, shuffle, "got it / again" tracking, keyboard shortcuts |
| **Key frames** | Every captured chart/slide, grouped by topic, captioned with what to notice |

<div align="center">
<img src="docs/demo-cards.png" alt="Flashcards tab" width="44%">
&nbsp;
<img src="docs/demo-diagram.png" alt="A generated layers diagram inside the article" width="44%">
<br><br>
<img src="docs/demo-article.png" alt="A generated flow diagram and comparison table" width="88%">
</div>

## Quick start

### Claude.ai / Claude desktop app

1. Download [`dist/video-insight-pack.skill`](dist/video-insight-pack.skill).
2. **Settings → Capabilities → Skills → Upload skill**.
3. Paste a video link and ask away.

### Claude Code (plugin, recommended)

```bash
claude plugin marketplace add Ewvue/video-insight-pack
claude plugin install video-insight-pack@ewvue-plugins
pip install youtube-transcript-api imageio-ffmpeg
```

Update later with `claude plugin update video-insight-pack@ewvue-plugins`.

### Claude Code (plain skill folder)

```bash
git clone https://github.com/Ewvue/video-insight-pack ~/.claude/skills/video-insight-pack
pip install youtube-transcript-api imageio-ffmpeg
```

### Then just ask

> https://www.youtube.com/watch?v=… what is this video about? Make me a mind map and an article with the key charts from the video, plus flashcards.

> 把这个视频做成思维导图和文章，配上视频里的关键画面，再做一些记忆卡片

> Turn `lecture-07.mp4` into study notes with flashcards.

The skill triggers on its own whenever you share a video and ask for a summary, notes, an article, a mind map or flashcards.

## How it works

```mermaid
flowchart LR
    A[Video link / file / subtitles] --> B[fetch_transcript.py<br/>timestamped paragraphs]
    B --> C[Claude reads & analyses<br/>insights · structure · claims]
    A --> D{Worth capturing frames?}
    D -- local file --> E[extract_frames.py<br/>contact sheets → exact frames]
    D -- online --> F[browser capture<br/>storyboard → canvas → screenshot]
    D -- no visuals --> G[skip capture<br/>draw diagrams & tables]
    C --> H[content.json]
    E --> H
    F --> H
    G --> H
    H --> I[build_page.py] --> J[index.html + img/]
```

Claude writes the content; a small script does the layout. That split keeps every pack consistent and lets Claude spend its effort on thinking, not HTML.

## Use the scripts without Claude

The three scripts are plain Python and useful on their own:

```bash
# 1. Transcript as ~60 s paragraphs (YouTube, .srt or .vtt)
python3 scripts/fetch_transcript.py "https://youtu.be/VIDEO_ID" --out work/transcript.md

# 2. Key frames from a local video: overview sheets, then exact frames
python3 scripts/extract_frames.py talk.mp4 sheet --every 10 --out work/sheets
python3 scripts/extract_frames.py talk.mp4 grab 12:30 41:55 --out work/frames

# 3. Build the page from your own content.json
python3 scripts/build_page.py examples/muse/content.json --out site
open site/index.html
```

The content format is documented in [`references/content-schema.md`](references/content-schema.md); [`examples/muse/content.json`](examples/muse/content.json) is a complete example (text only).

## Requirements

- Python 3.8+
- `youtube-transcript-api` for YouTube transcripts
- `imageio-ffmpeg` (bundles ffmpeg) or a system `ffmpeg` for local video frames
- For frames from online videos: a browser Claude can drive (e.g. Claude in Chrome). Without one, the skill gives you exact timestamps to screenshot yourself.

## Principles

- **Credit the creator.** Every page links the source video and channel. Frames and transcripts belong to their creators — use packs for personal study and attributed sharing; ask the creator before commercial use.
- **No circumvention.** The skill never deciphers stream signatures, bypasses bot checks or strips DRM. If that's the only way, it falls back to manual screenshots.
- **No invented facts.** Numbers and dates are attributed to the video; inferences are labelled as inferences.

## Repository layout

```
SKILL.md                     the workflow Claude follows
scripts/                     fetch_transcript.py · extract_frames.py · build_page.py
assets/                      template.html (the page) · browser-capture.js
references/                  content schema · article & flashcard writing guides · frame capture
examples/muse/               a full content.json you can build right away
.claude-plugin/              plugin + marketplace manifests for `claude plugin install`
dist/                        packaged .skill for one-click install
```

## Roadmap

- [x] Decide *before* capturing whether a video has visuals worth taking (skip talking-head videos)
- [x] Generated diagrams and comparison tables when a video has no charts of its own
- [x] Video thumbnail as page cover
- [ ] Bilibili and podcast (audio-only) sources; local Whisper transcription
- [ ] Anki export for flashcards

Ideas and PRs welcome — open an issue.

## Contributing

1. Fork and create a branch.
2. Keep `SKILL.md` short; put details in `references/`.
3. Test with at least one real video and include before/after screenshots in the PR.

## License

[MIT](LICENSE) © Ewvue

If this saved you an hour, a ⭐ helps others find it.
