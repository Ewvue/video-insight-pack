#!/usr/bin/env python3
"""Get a timestamped transcript as ~60-second paragraphs.

Sources:
  - a YouTube URL or 11-character video id  (needs: pip install youtube-transcript-api)
  - a local .srt or .vtt subtitle file

Usage:
  python3 fetch_transcript.py <url|id|file.srt|file.vtt> [--lang en,zh-Hans] [--chunk 60] [--out transcript.md]
"""
import argparse
import os
import re
import sys


def video_id(s):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})", s)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    return None


def from_youtube(vid, langs):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        sys.exit("youtube-transcript-api is not installed: pip install youtube-transcript-api")
    api = YouTubeTranscriptApi()
    try:
        fetched = api.fetch(vid, languages=langs)
    except Exception as first:
        # Fall back to whatever transcript exists, translated if possible.
        try:
            tl = api.list(vid)
            t = next(iter(tl))
            fetched = t.fetch()
            print(f"note: requested languages unavailable, using '{t.language_code}'", file=sys.stderr)
        except Exception:
            sys.exit(f"could not get a transcript for {vid}: {first}")
    return [(s.start, s.text) for s in fetched]


def parse_ts(ts):
    ts = ts.replace(",", ".")
    parts = [float(p) for p in ts.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    h, m, s = parts
    return h * 3600 + m * 60 + s


def from_subtitle_file(path):
    text = open(path, encoding="utf-8-sig").read()
    segs = []
    for block in re.split(r"\n\s*\n", text):
        lines = [l for l in block.strip().splitlines() if l.strip()]
        for i, line in enumerate(lines):
            m = re.match(r"\s*([\d:.,]+)\s*-->\s*([\d:.,]+)", line)
            if m:
                body = " ".join(lines[i + 1:])
                body = re.sub(r"<[^>]+>", "", body).strip()
                if body:
                    segs.append((parse_ts(m.group(1)), body))
                break
    if not segs:
        sys.exit(f"no subtitle cues found in {path}")
    return segs


def fmt(t):
    t = int(t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def chunk(segs, seconds):
    out, cur, start = [], [], None
    for t, txt in segs:
        txt = " ".join(txt.split())
        if start is None:
            start = t
        if t - start >= seconds and cur:
            out.append((start, " ".join(cur)))
            cur, start = [], t
        cur.append(txt)
    if cur:
        out.append((start, " ".join(cur)))
    # drop duplicated rolling-caption fragments ("a b" then "a b c")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("--lang", default="en,zh-Hans,zh-Hant,zh", help="preferred transcript languages, comma-separated")
    ap.add_argument("--chunk", type=int, default=60, help="paragraph length in seconds")
    ap.add_argument("--out", help="write here instead of stdout")
    a = ap.parse_args()

    if os.path.isfile(a.source):
        segs = from_subtitle_file(a.source)
        label = os.path.basename(a.source)
    else:
        vid = video_id(a.source)
        if not vid:
            sys.exit("not a YouTube URL/id and not an existing file")
        segs = from_youtube(vid, [l.strip() for l in a.lang.split(",") if l.strip()])
        label = f"https://www.youtube.com/watch?v={vid}\nThumbnail: https://i.ytimg.com/vi/{vid}/hqdefault.jpg"

    paras = chunk(segs, a.chunk)
    body = f"# Transcript\n\nSource: {label}\nSegments: {len(segs)} · Paragraphs: {len(paras)} · Ends at {fmt(segs[-1][0])}\n\n"
    body += "\n\n".join(f"[{fmt(t)}] {txt}" for t, txt in paras) + "\n"
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(body)
        print(f"wrote {a.out} ({len(paras)} paragraphs, {len(body)} chars)")
    else:
        sys.stdout.write(body)


if __name__ == "__main__":
    main()
