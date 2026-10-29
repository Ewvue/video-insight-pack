---
name: video-insight-pack
description: Turn a video (YouTube link, other online video, or a local video/subtitle file) into a shareable study pack — key insights, a mind map, a long-form article with the video's own key frames inserted as figures, flashcards for memorizing, and a figure gallery — all built into one HTML page. Use this whenever someone shares a video link and asks what it is about, wants a summary, notes, 思维导图, 文章, 读后感, 记忆卡片/flashcards, 截图/关键画面, or wants to "learn", "digest" or "share" a talk, interview, podcast, lecture or course video — even if they only ask for one of these pieces, or say things like "这个视频讲了什么", "帮我整理成文章", "把视频做成笔记". 视频总结、视频转文章、视频笔记、视频思维导图、视频截图配图、视频记忆卡片。
---

# Video Insight Pack

Turn one video into a pack people can actually learn from and pass on:

1. **Key insights** — 3–6 non-obvious takeaways, not a table of contents.
2. **Mind map** — the whole video as root → branches (one per chapter/theme) → leaves, each branch with its timestamp.
3. **Article** — a readable long-form piece in the user's language, with the video's own key frames as figures where they explain something.
4. **Flashcards** — question/answer cards for remembering the ideas.
5. **Key frames gallery** — the charts, diagrams and slides from the video, captioned and timestamped, saved as image files.

Everything ends up in one HTML page with tabs, built from a single `content.json` by `scripts/build_page.py`. Writing the content is your job; the script only handles layout, so every pack looks consistent and you don't spend effort on HTML.

Write all output in the user's language (if they write Chinese, everything is in Chinese, including captions and cards). Keep proper names and short key terms in the original language where that helps (e.g. "Deception（欺骗）").

## Workflow

### 1. Get the transcript and metadata

- **YouTube**: `python3 scripts/fetch_transcript.py <url-or-id> --out <work>/transcript.md` (installs nothing itself; needs `pip install youtube-transcript-api`). It writes timestamped ~60-second paragraphs. Use `--lang zh-Hans,en` to choose languages.
- **Local subtitle file** (.srt / .vtt): `python3 scripts/fetch_transcript.py path/to/file.srt --out <work>/transcript.md`.
- **Local video without subtitles**: ask whether the user has a subtitle file; otherwise transcribe with a local tool they already have (e.g. whisper) — say what you're running before you run it.
- Also collect title, channel/author, length, publish date and the chapter list (YouTube puts chapters in the description; in a browser, `ytInitialPlayerResponse.videoDetails` has title, author, lengthSeconds and shortDescription).

Read the whole transcript before writing. Long videos: read it in parts, but read all of it — the best material is often in the last third.

### 2. Understand before writing

Work out: the speaker(s) and their stake, the central question, the structure (use the chapters), the claims with evidence, the claims without evidence, and what the video avoids answering. That last part is what turns a summary into insight — include a short, fair "critical reading" in the article.

Auto-generated transcripts have no speaker labels. With two or more guests, check who said what from context (names, "my daughter", who was asked the question) before attributing a story or opinion; misattribution is the most common factual error in these packs.

### 3. Decide whether frames are worth capturing (1–2 minutes)

Capturing frames is the slowest step, and it only pays off when the video *shows* something: charts, diagrams, framework cards ("Level 1 / 2 / 3"), slides, headline or report screenshots, product UI, data tables. Decide before spending time on it:

1. **Transcript cues** — lines like "as you can see", "this chart", "here's a slide", "I have some visuals", "these are the logs" point at graphics. None at all in a long conversation is a strong sign there are none.
2. **Format** — lectures, explainers, product launches, documentaries and edited YouTube essays usually have graphics; podcasts, panel talks and sit-down interviews usually don't.
3. **One quick look** — for an online video, one or two storyboard overview screenshots (see `references/frame-capture.md`); for a local file, one contact sheet. If everything is people talking, stop here.

**If there are no useful visuals**, skip capturing entirely and say so in one sentence ("这期是对谈，画面里没有图表，所以没有截图"). Instead:
- add a **cover**: set `source.thumbnail` to the video's thumbnail URL (YouTube: `https://i.ytimg.com/vi/<id>/hqdefault.jpg`); `build_page.py` downloads it as the page cover;
- explain structure with **generated visuals** in the article: `diagram` blocks (flow / layers / compare) for frameworks, processes and timelines, and `table` blocks for comparisons (see `references/content-schema.md`). These often explain better than a screenshot would.

If the user explicitly asked for images from a video that has none, tell them that, use the cover and generated diagrams, and capture at most one or two scene shots for context.

### 4. Capture key frames (only when step 3 says yes)

Pick the method that fits — read **`references/frame-capture.md`** for the details of each:

| Source | Method |
|---|---|
| Local video file | `scripts/extract_frames.py` (bundled ffmpeg via `imageio-ffmpeg`): contact sheets to locate, then exact frames |
| Online video, browser available | Play it in the user's browser and capture frames from the page (storyboard to locate, canvas + screenshot to save). Ask before using the user's own browser, unless they already agreed |
| Neither works | Give the user exact timestamps and ask them to screenshot (⌘⇧4 / Win+Shift+S); you organize the files |

Do not download or decrypt streams by getting around a platform's protections (signature deciphering, bot-check workarounds, DRM). If the only route left is that, stop and use the screenshot fallback.

Save frames as `<work>/frames/MM-SS_short-description.jpg` (`H-MM-SS_…` past one hour; crop black letterbox bars) and keep a list: time, file, one-line description. When a frame you wanted can't be captured, say so in the final message with its timestamp.

### 5. Write `content.json`

Follow **`references/content-schema.md`** exactly (it has a complete example). Guidance for each part:

- **Insights**: each is a claim plus why it matters. "Trust beats capability for consumer AI" is an insight; "They discussed trust" is not.
- **Mind map**: one branch per chapter or theme (6–10 branches), 3–6 leaves each, leaves are facts/claims with specifics (numbers, names, examples). Bold the key phrase of a leaf with `**…**`.
- **Article**: read **`references/article-writing.md`**. Conclusion first, then the argument; one idea per section; figures placed right after the paragraph they illustrate. Use `diagram` and `table` blocks wherever a framework, process, timeline or comparison is easier to see than to read — with or without captured frames.
- **Flashcards**: read **`references/flashcards.md`**. 12–25 cards, atomic, answerable from the video.
- **Figures**: every captured frame gets an entry with a caption that says what the viewer should notice, not just what is shown.

**Sourcing rule (important).** Numbers, dates and rankings in the video ("5M downloads in 22 days", "faster than ChatGPT") are claims by the video, not facts you verified. Attribute them in the text ("据视频引用的新闻…", "the host says…"), and never add a date or figure the video doesn't give — if you infer something (e.g. a launch season from the upload date), say it's an inference. Readers will ask "where does this number come from?"; the article should already answer.

**Quoting**: paraphrase. Keep direct quotes short (a sentence at most) and few.

### 6. Build the page

```bash
python3 scripts/build_page.py <work>/content.json --frames <work>/frames --out <work>/site
```

This writes `site/index.html` plus `site/img/` (frames copied under ASCII names). Add `--inline` to embed the images into a single self-contained HTML file (bigger, but one file to send). The page has four tabs — 洞察与导图 / 文章 / 记忆卡片 / 关键画面 (labels follow `lang`) — and works in light and dark mode and on phones.

### 7. Deliver

- If an Artifact/publish tool is available, build with `--fragment` (the host adds its own page skeleton) and publish `site/index.html` with each `img/*` file as a supporting file, so the user gets a link they can share.
- Otherwise open or send `site/index.html`.
- Also leave the frames folder and an index (`frames/INDEX.md`: time | file | description) so the images are usable on their own.

In the final message: one paragraph on what the video is about, what's in the pack, whether frames were captured (and if not, why not — e.g. a talk with no graphics), and which numbers are unverified claims from the video.

## Copyright and courtesy

Frames and transcripts belong to the video's creator. The page credits the source (title, channel, link) — `build_page.py` adds this from `source` — and is meant for personal study and sharing with attribution. If the user wants to publish the pack commercially, tell them they need the creator's permission.
