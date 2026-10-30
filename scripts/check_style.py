#!/usr/bin/env python3
"""Flag AI-sounding patterns in a content.json (Chinese and English).

  python3 check_style.py content.json [--strict] [--quiet]

Each hit names the rule (see references/style-guide.md), where it is, and the
matched text. Strong hits (R1-R5, R7-R9) should be fixed; weak hits (R10-R17) matter
when several cluster in one place. A hit is a prompt to look, not a verdict:
keep a sentence that is accurate and reads well. --strict exits 1 on any
strong hit (useful before building the page).
"""
import argparse
import json
import re
import sys

ZH_OPENERS = ["值得注意的是", "值得一提的是", "众所周知", "事实上", "说白了", "说穿了", "先说结论", "总而言之", "综上所述",
              "不可否认", "在当今时代", "毋庸置疑", "不难发现", "换句话说", "简单来说", "总的来说"]
ZH_INFLATED = ["赋能", "至关重要", "深入探讨", "无缝", "闭环", "底层逻辑", "抓手", "颠覆", "重塑", "里程碑式", "划时代",
               "革命性", "全方位", "多维度", "打造", "助力", "引领", "极致", "完美", "震撼", "令人深思", "不禁让人",
               "意义深远", "前所未有", "深刻地", "淋漓尽致"]
ZH_CLOSERS = ["答案很简单", "这才是真正", "真正的问题是", "说到底", "归根结底", "而这，", "而这正是", "这就是为什么",
              "其实就一件事", "最有意思的是", "最有趣的是", "说得很直接：", "一句话概括：", "有意思的是，"]
ZH_AUTHORITY = ["专家指出", "专家认为", "业内普遍认为", "有研究表明", "研究显示", "数据显示"]
ZH_RESIDUE = ["希望对你有帮助", "希望这能帮到", "以下是", "让我们一起", "让我们来看看"]

EN_OPENERS = ["it's worth noting", "it is worth noting", "in today's", "in conclusion", "let's dive", "let's delve",
              "needless to say", "at the end of the day", "in summary", "to put it simply"]
EN_INFLATED = ["delve", "pivotal", "crucial", "seamless", "testament", "tapestry", "landscape", "robust", "leverage",
               "underscore", "showcase", "foster", "realm", "vibrant", "groundbreaking", "game-changer", "game changer",
               "revolutionize", "unlock", "empower", "intricate", "meticulous", "profound", "paramount", "transformative"]
EN_CLOSERS = ["here's the thing", "and that changes everything", "the answer is simple", "that's the real",
              "and that's exactly why", "this is where"]
EN_AUTHORITY = ["experts say", "experts believe", "studies show", "research shows", "research suggests", "many believe"]
EN_RESIDUE = ["i hope this helps", "great question", "certainly!", "as an ai"]

ORDINAL = re.compile(r"^[一二三四五六七八九十]+、")

RULES = {
    "R1": ("strong", "knocking down a claim nobody made", "state the point directly"),
    "R2": ("strong", "stock opener / filler", "delete it and start with the content"),
    "R3": ("strong", "inflated word", "use the plain word or the specific thing"),
    "R4": ("strong", "dash as connector", "use a comma, full stop or brackets"),
    "R5": ("strong", "dramatic closer / staged reveal", "delete or merge into the previous sentence"),
    "R6": ("weak", "vague summary word near a number", "if that number measures the same thing, use it; otherwise keep the wording"),
    "R7": ("strong", "borrowed authority", "name who said it in the video, or drop it"),
    "R8": ("strong", "chat residue", "delete"),
    "R9": ("strong", "exclamation mark", "use a full stop"),
    "R10": ("weak", "adjacent sentences open the same way", "restructure one of them"),
    "R11": ("weak", "long 、 list in one sentence", "fine if the video really names that many; otherwise keep the ones that matter"),
    "R12": ("weak", "ordinal headings (一、二、三…)", "drop the numbers; let headings state the idea"),
    "R13": ("weak", "translationese", "split the sentence; say the consequence directly"),
    "R14": ("weak", "noun-ised verb", "use the verb (调整了 / is, has)"),
    "R15": ("weak", "personified metaphor", "say what the thing does"),
    "R16": ("weak", "bold used as decoration", "keep at most one bold phrase per paragraph"),
    "R17": ("weak", "colon lead-in", "make it a normal sentence"),
    "R18": ("weak", "trailing contrast (……，而不是 / 不在……而在)", "keep it if the speaker drew this contrast; otherwise state the point directly"),
}


def texts(d):
    """Yield (location, text) for every human-readable field."""
    for k in ("title", "summary", "eyebrow"):
        if d.get(k):
            yield k, d[k]
    for i, x in enumerate(d.get("insights", [])):
        yield f"insights[{i}].title", x.get("title", "")
        yield f"insights[{i}].body", x.get("body", "")
    mm = d.get("mindmap", {})
    if mm.get("root"):
        yield "mindmap.root", mm["root"]
    for i, b in enumerate(mm.get("branches", [])):
        yield f"mindmap.branches[{i}].title", b.get("title", "")
        for j, l in enumerate(b.get("leaves", [])):
            yield f"mindmap.branches[{i}].leaves[{j}]", l
    a = d.get("article", {})
    if a.get("title"):
        yield "article.title", a["title"]
    for i, b in enumerate(a.get("blocks", [])):
        loc = f"article.blocks[{i}]({b.get('type')})"
        if b.get("text"):
            yield loc, b["text"]
        for j, it in enumerate(b.get("items", []) or []):
            yield f"{loc}.items[{j}]", it if isinstance(it, str) else " ".join(str(v) for v in it.values())
        for j, row in enumerate(b.get("rows", []) or []):
            yield f"{loc}.rows[{j}]", " | ".join(row)
        if b.get("caption"):
            yield f"{loc}.caption", b["caption"]
    if a.get("source_note"):
        yield "article.source_note", a["source_note"]
    for i, c in enumerate(d.get("flashcards", [])):
        yield f"flashcards[{i}].q", c.get("q", "")
        yield f"flashcards[{i}].a", c.get("a", "")
    for i, f in enumerate(d.get("figures", [])):
        yield f"figures[{i}].caption", f.get("caption", "")


def snippet(t, s, e, pad=14):
    a, b = max(0, s - pad), min(len(t), e + pad)
    return ("…" if a else "") + t[a:b].replace("\n", " ") + ("…" if b < len(t) else "")


def find_words(t, words, rule, hits, loc, ci=False):
    hay = t.lower() if ci else t
    for w in words:
        start = 0
        while True:
            pat = w.lower() if ci else w
            if ci and pat.isalpha():
                m = re.search(r"\b" + re.escape(pat) + r"\w*", hay[start:])
                if not m:
                    break
                s, e = start + m.start(), start + m.end()
            else:
                s = hay.find(pat, start)
                if s < 0:
                    break
                e = s + len(pat)
            hits.append((rule, loc, snippet(t, s, e)))
            start = e


def sentences(t):
    return [s.strip() for s in re.split(r"(?<=[。！？!?.；;])\s*", t) if s.strip()]


def check(d):
    hits = []
    for loc, t in texts(d):
        if not t:
            continue
        # R1 not-X-but-Y
        for m in re.finditer(r"(不是|并非|并不是|不只是|不仅仅是)[^。！？；\n]{1,30}?(而是|更是)", t):
            hits.append(("R1", loc, snippet(t, m.start(), m.end())))
        for m in re.finditer(r"不在(于)?[^。！？；\n]{1,30}?而在|[，,]\s*而(不是|不只是|非)", t):
            hits.append(("R18", loc, snippet(t, m.start(), m.end())))
        for m in re.finditer(r"\b(it'?s|this is|that'?s|isn'?t) not (just |only |about |really )?[^.;!?]{1,40}?[,;—–] *(it'?s|but|rather)\b", t, re.I):
            hits.append(("R1", loc, snippet(t, m.start(), m.end())))
        for m in re.finditer(r"\bnot (just|only|merely) [^.;!?]{1,40}? but\b", t, re.I):
            hits.append(("R1", loc, snippet(t, m.start(), m.end())))
        find_words(t, ZH_OPENERS, "R2", hits, loc)
        find_words(t, EN_OPENERS, "R2", hits, loc, ci=True)
        find_words(t, ZH_INFLATED, "R3", hits, loc)
        find_words(t, EN_INFLATED, "R3", hits, loc, ci=True)
        for m in re.finditer(r"——|—|–| - ", t):
            if m.group(0) == "–" and re.match(r"\d", t[m.end():m.end() + 1] or "x") and re.match(r"\d", t[m.start() - 1:m.start()] or "x"):
                continue  # numeric range such as 500–600
            hits.append(("R4", loc, snippet(t, m.start(), m.end())))
        find_words(t, ZH_CLOSERS, "R5", hits, loc)
        find_words(t, EN_CLOSERS, "R5", hits, loc, ci=True)
        for m in re.finditer(r"(大幅|显著|极大地|大大)(增长|提升|提高|下降|减少|改善)|\b(significantly|dramatically|substantially)\b", t, re.I):
            if re.search(r"\d", t):  # a concrete number is available nearby
                hits.append(("R6", loc, snippet(t, m.start(), m.end())))
        find_words(t, ZH_AUTHORITY, "R7", hits, loc)
        find_words(t, EN_AUTHORITY, "R7", hits, loc, ci=True)
        find_words(t, ZH_RESIDUE, "R8", hits, loc)
        find_words(t, EN_RESIDUE, "R8", hits, loc, ci=True)
        for m in re.finditer(r"[！!](?![=\w])", t):
            hits.append(("R9", loc, snippet(t, m.start(), m.end())))
        # weak
        ss = sentences(t)
        plain = [re.sub(r"^[*“\"「（(\s]+", "", x) for x in ss]
        for a, b in zip(plain, plain[1:]):
            ka = re.match(r"[A-Za-z]+|\S{2}", a)
            kb = re.match(r"[A-Za-z]+|\S{2}", b)
            if ka and kb and ka.group(0).lower() == kb.group(0).lower() and ka.group(0).lower() not in ("the", "a", "an"):
                hits.append(("R10", loc, snippet(b, 0, min(len(b), 12), 0)))
        for s in ss:
            if s.count("、") >= 3:
                hits.append(("R11", loc, snippet(s, 0, min(len(s), 24), 0)))
        for m in re.finditer(r"这意味着|(^|[。，])当[^。，]{2,25}时，|\bthis means that\b", t, re.I):
            hits.append(("R13", loc, snippet(t, m.start(), m.end())))
        for m in re.finditer(r"(进行|完成)了?[^。，]{0,10}(的)?(调整|优化|分析|讨论|研究|工作)|\b(serves as|boasts|stands as)\b", t, re.I):
            hits.append(("R14", loc, snippet(t, m.start(), m.end())))
        for m in re.finditer(r"像一位|宛如一位|仿佛一位|就像一个贴心", t):
            hits.append(("R15", loc, snippet(t, m.start(), m.end())))
        if t.count("**") >= 4:
            hits.append(("R16", loc, f"{t.count('**') // 2} bold phrases"))
        for m in re.finditer(r"(?<!参考)(结论|答案|关键|重点|核心)(是|就是|在于)?[：:]", t):
            hits.append(("R17", loc, snippet(t, m.start(), m.end())))
    for i, b in enumerate(d.get("article", {}).get("blocks", [])):
        items = [x for x in (b.get("items") or []) if isinstance(x, str)]
        labelled = [x for x in items if re.match(r"^\*\*[^*]{1,16}\*\*[：:]", x)]
        if len(items) >= 3 and len(labelled) == len(items):
            hits.append(("R16", f"article.blocks[{i}](list)", "every item starts with a bold label and colon"))
    heads = [b.get("text", "") for b in d.get("article", {}).get("blocks", []) if b.get("type") == "h2"]
    numbered = [h for h in heads if ORDINAL.match(h)]
    if len(numbered) >= 3:
        hits.append(("R12", "article (h2)", f"{len(numbered)} headings start with 一、二、三…"))
    return hits


def char_count(d):
    return sum(len(t) for _, t in texts(d))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("content")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any strong hit remains")
    ap.add_argument("--quiet", action="store_true", help="print the summary only")
    a = ap.parse_args()
    d = json.load(open(a.content, encoding="utf-8"))
    hits = check(d)
    strong = [h for h in hits if RULES[h[0]][0] == "strong"]
    weak = [h for h in hits if RULES[h[0]][0] == "weak"]
    if not a.quiet:
        for level, group in (("STRONG", strong), ("weak", weak)):
            for rule, loc, snip in sorted(group, key=lambda h: (int(h[0][1:]), h[1])):
                name, fix = RULES[rule][1], RULES[rule][2]
                print(f"[{level}] {rule} {name} · {loc}\n    “{snip}”  → {fix}")
    n = char_count(d)
    per = lambda k: f"{k * 1000 / max(n, 1):.1f}"
    by = {}
    for r, _, _ in hits:
        by[r] = by.get(r, 0) + 1
    print(f"\n{n} chars checked · {len(strong)} strong ({per(len(strong))}/1000 chars) · {len(weak)} weak ({per(len(weak))}/1000 chars)")
    if by:
        print("by rule: " + ", ".join(f"{r}×{c}" for r, c in sorted(by.items(), key=lambda kv: int(kv[0][1:]))))
    if a.strict and strong:
        sys.exit(1)


if __name__ == "__main__":
    main()
