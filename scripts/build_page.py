#!/usr/bin/env python3
"""Build the study-pack HTML page from content.json and a folder of frames.

  python3 build_page.py content.json --frames frames/ --out site/ [--inline]

Writes site/index.html and copies each figure to site/img/<id>.<ext> (ASCII names,
safe to publish anywhere). With --inline, images are embedded as data URIs and only
index.html is needed. See references/content-schema.md for the content format.
"""
import argparse
import base64
import json
import mimetypes
import os
import shutil
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "template.html")


def fail(msg):
    sys.exit(f"build_page: {msg}")


def validate(d, frames):
    for key in ("title", "insights", "mindmap", "article"):
        if not d.get(key):
            fail(f"'{key}' is missing or empty")
    if not d["mindmap"].get("branches"):
        fail("mindmap.branches is empty")
    if not d["article"].get("blocks"):
        fail("article.blocks is empty")
    ids = set()
    for f in d.get("figures", []):
        for k in ("id", "file", "caption"):
            if not f.get(k):
                fail(f"a figure is missing '{k}': {f}")
        if f["id"] in ids:
            fail(f"duplicate figure id '{f['id']}'")
        ids.add(f["id"])
        if not os.path.isfile(os.path.join(frames or "", f["file"])):
            fail(f"figure file not found: {os.path.join(frames or '', f['file'])}")
    for b in d["article"]["blocks"]:
        if b.get("type") == "figure":
            for i in b.get("ids", []):
                if i not in ids:
                    fail(f"article figure block uses unknown id '{i}'")
        elif b.get("type") == "diagram":
            if b.get("style", "flow") not in ("flow", "layers", "compare"):
                fail(f"diagram style must be flow, layers or compare, got '{b.get('style')}'")
            if not b.get("items") or not all(i.get("title") for i in b["items"]):
                fail("a diagram needs 'items', each with a 'title'")
        elif b.get("type") == "table":
            cols = b.get("columns") or []
            if not cols or not b.get("rows"):
                fail("a table needs 'columns' and 'rows'")
            for r in b["rows"]:
                if len(r) != len(cols):
                    fail(f"table row has {len(r)} cells but there are {len(cols)} columns: {r}")
        elif b.get("type") not in ("lede", "h2", "p", "quote", "list"):
            fail(f"unknown article block type '{b.get('type')}'")
    for c in d.get("flashcards", []):
        if not c.get("q") or not c.get("a"):
            fail(f"a flashcard needs 'q' and 'a': {c}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("content")
    ap.add_argument("--frames", default="", help="folder containing the figure files")
    ap.add_argument("--out", default="site")
    ap.add_argument("--inline", action="store_true", help="embed images in the HTML")
    ap.add_argument("--fragment", action="store_true",
                    help="omit doctype/html/head/body wrappers (for hosts such as Claude Artifacts that add their own)")
    a = ap.parse_args()

    d = json.load(open(a.content, encoding="utf-8"))
    validate(d, a.frames)

    os.makedirs(a.out, exist_ok=True)
    if d.get("figures") and not a.inline:
        os.makedirs(os.path.join(a.out, "img"), exist_ok=True)
    for f in d.get("figures", []):
        path = os.path.join(a.frames, f["file"])
        ext = os.path.splitext(f["file"])[1].lower() or ".jpg"
        if a.inline:
            mime = mimetypes.guess_type(path)[0] or "image/jpeg"
            f["src"] = f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()
        else:
            f["out"] = f"{f['id']}{ext}"
            shutil.copyfile(path, os.path.join(a.out, "img", f["out"]))

    thumb = (d.get("source") or {}).get("thumbnail")
    if thumb:
        try:
            req = urllib.request.Request(thumb, headers={"User-Agent": "video-insight-pack"})
            raw = urllib.request.urlopen(req, timeout=15).read()
            if a.inline:
                d["cover"] = "data:image/jpeg;base64," + base64.b64encode(raw).decode()
            else:
                os.makedirs(os.path.join(a.out, "img"), exist_ok=True)
                open(os.path.join(a.out, "img", "cover.jpg"), "wb").write(raw)
                d["cover"] = "img/cover.jpg"
        except Exception as e:
            print(f"note: cover thumbnail not downloaded ({e}); the page is built without it", file=sys.stderr)

    html = open(TEMPLATE, encoding="utf-8").read()
    data = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
    page_title = d.get("page_title") or d["title"]
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = (html.replace("__LANG__", esc(d.get("lang", "en")))
                .replace("__PAGE_TITLE__", esc(page_title))
                .replace("__DATA__", data))
    if a.fragment:
        # Hosts that wrap pages in their own skeleton (e.g. Claude Artifacts) want no doctype/html/head/body tags.
        head = html.split("<head>", 1)[1].split("</head>", 1)[0]
        head = "\n".join(l for l in head.splitlines() if "charset=" not in l and 'name="viewport"' not in l)
        body = html.split("<body>", 1)[1].split("</body>", 1)[0]
        html = head.strip() + "\n" + body.strip() + "\n"
    out = os.path.join(a.out, "index.html")
    open(out, "w", encoding="utf-8").write(html)
    size_kb = os.path.getsize(out) // 1024

    # soft limits from SKILL.md / article-writing.md: warn, don't fail
    h2 = sum(1 for b in d["article"]["blocks"] if b.get("type") == "h2")
    for label, n, lo, hi in (("insights", len(d["insights"]), 3, 6), ("mind-map branches", len(d["mindmap"]["branches"]), 6, 10),
                             ("article h2 sections", h2, 5, 9), ("flashcards", len(d.get("flashcards", [])), 12, 25)):
        if n and not lo <= n <= hi:
            print(f"warning: {n} {label} (guide: {lo}-{hi}); consider merging or trimming", file=sys.stderr)
    figs = len(d.get("figures", []))
    print(f"wrote {out} ({size_kb} KB) · {len(d['insights'])} insights · "
          f"{len(d['mindmap']['branches'])} branches · {len(d['article']['blocks'])} article blocks · "
          f"{len(d.get('flashcards', []))} cards · {figs} figures" + (" · cover" if d.get("cover") else "") + ("" if a.inline or not figs else f" in {os.path.join(a.out, 'img')}"))


if __name__ == "__main__":
    main()
