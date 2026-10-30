# Style guide: write like a person who watched the video

Readers stop trusting a pack the moment it sounds machine-written. This guide lists the patterns that give AI prose away, in Chinese and English, and how to fix each one without changing what the text says. Use it while writing, then run `scripts/check_style.py` and go through what it flags.

The rules are distilled from three open-source projects (all MIT): [blader/humanizer](https://github.com/blader/humanizer) (English, based on Wikipedia's "Signs of AI writing"), [baibanbao/qu-ai-wei](https://github.com/baibanbao/qu-ai-wei) (Chinese, with corpus-measured rules from humanizer-zh and lieflat-less-ai-tone) and [MrGeDiao/shuorenhua](https://github.com/MrGeDiao/shuorenhua) (Chinese, scope-aware rewriting).

## The first rule: keep every fact

Fixing tone must never change meaning. When you rewrite a sentence:

- add no fact, number, name, date, quote, source or cause that isn't in the video;
- drop no claim, limit, condition, concession or attribution ("Wang 认为…" stays Wang's);
- keep certainty as it was: "可能" does not become "一定", "the host says" does not become a fact;
- leave proper terms alone (端到端加密, scalable oversight), and leave sentences that already read well.

A tone fix that loses a fact is worse than the tell it removed.

## Strong tells — fix every time

| # | Pattern | 中文例子 | English example | Fix |
|---|---|---|---|---|
| 1 | **Knocking down a claim nobody made** | 这不是一个产品问题，而是一个信任问题 / 并非……而是…… | It's not about speed, it's about trust | State the point directly: 这是一个信任问题. If the *speaker* drew the contrast, keep it but state it exactly: "not just X" is 不只是 X, never 不是 X |
| 2 | **Stock openers and fillers** | 值得注意的是、众所周知、事实上、说白了、先说结论、总而言之、综上所述、不可否认、在当今时代 | It's worth noting that, In today's world, In conclusion, Let's dive in | Delete; start with the content |
| 3 | **Inflated words** | 赋能、至关重要、深入探讨、无缝、闭环、底层逻辑、抓手、颠覆、重塑、里程碑式 | delve, pivotal, crucial, seamless, testament, tapestry, landscape, robust, leverage, underscore, showcase, foster, realm | Use the plain word, or the specific thing (至关重要 → 决定了能不能上线) |
| 4 | **Dashes as the all-purpose connector** | 它很快——快得惊人 | It's fast — surprisingly fast | Use a comma, a full stop or brackets. Chinese text from Claude uses about 5× more dashes than human writing |
| 5 | **Dramatic closers and staged reveals** | 而这，才是真正的答案。/ 答案很简单： / 其实就一件事： / 最有意思的是 | And that changes everything. / Here's the thing: | Delete the line, or merge its content into the previous sentence |
| 6 | **Vague summary instead of the number you have** | 下载量大幅增长 (when 500 万 is in the same paragraph) | grew significantly | Put the specific value there if it measures the same thing. If the video gives no number, keep the original wording; never invent one or weaken the claim. (The checker reports this one as weak, because it can't tell what a nearby number measures.) |
| 7 | **Borrowed authority** | 专家指出、业内普遍认为 | Experts say, Studies show | Name who said it in the video, or drop it |
| 8 | **Chat residue** | 希望对你有帮助、以下是…… | Great question! I hope this helps | Delete |
| 9 | **Exclamation marks** | 太厉害了！ | This is huge! | Use a full stop |

## Weaker tells — fix when they pile up

| # | Pattern | Fix |
|---|---|---|
| 10 | **Adjacent sentences with the same skeleton** (same length, same comma count, same order) | Rewrite one of them with a different structure. Parallelism inside one sentence is normal; leave it |
| 11 | **Forced threes / long 、 lists** (三项以上顿号并列, "X, Y, and Z" every paragraph) | Keep a list only when the content really has that many parts; otherwise name the one that matters |
| 12 | **Ordinal headings** (一、二、三… on every h2) | Drop the numbers; let the heading state the idea |
| 13 | **Translationese** (超长前置定语、当……时、这意味着……) | Split the sentence; say the consequence directly |
| 14 | **Noun-ised verbs** (进行了……的调整、完成……工作 / serves as, features, boasts) | Use the verb: 调整了 / is, has |
| 15 | **Personified metaphors** (像一位贴心的管家) | Say what the thing does |
| 16 | **Bold as decoration** | Keep bold for the one phrase a skimmer must see; at most one per paragraph |
| 17 | **Colon lead-ins** (结论是： / The answer: ) | Turn into a normal sentence |
| 18 | **Trailing contrast** (……，而不是…… / 不在……而在……) | Fine when the speaker made that contrast; otherwise it's rule 1 in disguise, so state the point directly |

The checker can't judge everything. Leave these alone even when flagged: a 、 list where the video really names that many items; 「参考答案：」 on a model answer; a colon that introduces the diagram or table right below it.

Do **not** "fix" things that aren't tells: varying sentence length on purpose, splitting paragraphs to look casual, adding filler words or slang. Measured corpora show sentence-length variance doesn't separate human from AI text; forcing it makes prose worse.

## Pack-specific notes

- **Insight titles**: a claim in plain words. "信任比能力更重要" beats "不是能力，而是信任".
- **Mind-map leaves**: fragments are fine; no closers, no exclamation marks.
- **Article**: conclusion first, but say it once. The lede and the last section shouldn't repeat each other.
- **Flashcards**: plain questions and short answers. No "你知道吗？".
- **Captions**: what to notice in the image, in one sentence, without "如图所示".
- **Chinese punctuation**: full-width （，。：；“”）; no exclamation marks; bold close to zero in body text.

## Self-check before building the page

1. Run `python3 scripts/check_style.py <work>/content.json` and fix each strong hit (rules 1–9) using the table above.
2. Look at weak hits (10–17) only where several cluster in one paragraph.
3. Re-read every changed sentence against the transcript: same facts, same attribution, same certainty.
4. Re-run the check. A few remaining weak hits are fine; zero strong hits is the goal.
