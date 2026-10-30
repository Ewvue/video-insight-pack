# content.json schema

`scripts/build_page.py` reads this file. All text fields are plain text; the only markup allowed is `**bold**` (rendered as an emphasized phrase). Do not put HTML in fields — it is escaped.

```jsonc
{
  "lang": "zh-CN",                       // "zh-CN", "en", ... — sets tab labels and <html lang>
  "page_title": "Muse 与信任的三层",       // browser-tab name: 2–6 words, a name, not a sentence
  "title": "Muse：当 AI 开始替你打电话，我们该怎么信任它",   // big headline on the page
  "eyebrow": "HUGE* Conversations · Cleo Abram × Alexandr Wang · 68 分钟",  // small line above the title
  "summary": "一两句话说明这是什么视频、谈了什么。",
  "source": {
    "title": "The Biggest Launch Since ChatGPT (Muse)",
    "url": "https://www.youtube.com/watch?v=1LRvMRC_pfY",
    "channel": "Cleo Abram",
    "duration": "1:08:21",
    "published": "2026-10",              // optional; only if known
    "thumbnail": "https://i.ytimg.com/vi/1LRvMRC_pfY/hqdefault.jpg"  // optional; build_page downloads it as the page cover
  },

  "insights": [                           // 3–6
    { "title": "智能体普及的瓶颈是“包装”，不是模型", "body": "一到三句解释与证据。" }
  ],

  "mindmap": {
    "root": "Muse：从聊天机器人到智能体",
    "root_sub": "Alexandr Wang 访谈",      // optional
    "branches": [                         // 6–10
      {
        "title": "为什么爆发",
        "time": "3:04",                   // optional, chapter start
        "leaves": ["**22 天 500 万下载**（视频引用的新闻）", "..."]
      }
    ]
  },

  "article": {
    "title": "把钥匙交给 AI 之前：从 Muse 看智能体时代的三层信任",
    "blocks": [                           // rendered in order
      { "type": "lede", "text": "开头导语，结论先行。" },
      { "type": "h2", "text": "一、……" },
      { "type": "p", "text": "段落。可以用 **加粗**。" },
      { "type": "figure", "ids": ["levels-all"], "caption": "可选；省略时用 figures 里的 caption" },
      { "type": "figure", "ids": ["hf-diagram-2", "hf-report"], "caption": "两张并排" },
      { "type": "list", "ordered": true, "items": ["**可扩展监督**：……", "……"] },
      { "type": "quote", "text": "补充说明或原话（短）。" },
      { "type": "diagram", "style": "layers",            // flow = steps left→right · layers = stacked levels · compare = side-by-side columns
        "items": [ { "title": "隐私", "text": "数据给谁" }, { "title": "分寸", "text": "别用你不想要的方式完成" }, { "title": "欺骗", "text": "明知越界还瞒着你" } ],
        "caption": "信任的三层，越往上越难" },
      { "type": "table", "columns": ["行业", "何时检查", "例子"],
        "rows": [ ["核电", "事前 + 持续", "NRC 驻场"], ["保健品", "事后", "出事再追责"] ],
        "caption": "现有监管方式对比" }
    ],
    "source_note": "来源与说明：依据视频英文字幕整理……数字均为视频中的说法，未经独立核实。"
  },

  "flashcards": [                         // 12–25
    { "q": "Cleo 把 AI 智能体的信任分成哪三层？", "a": "隐私、分寸、欺骗。", "time": "34:47", "tag": "框架" }
  ],

  "figures": [                            // one per captured frame
    {
      "id": "spectrum-leaders",           // ASCII, used by article figure blocks
      "file": "42-57_spectrum-leaders.jpg",  // file name inside --frames folder
      "time": "42:57",
      "group": "监管光谱",                 // gallery section; groups appear in first-seen order
      "caption": "最终定位：……（说明看点）",
      "alt": "监管光谱上各 AI 领袖的位置",   // optional, defaults to caption
      "featured": true                    // optional: show full-width at top of its group
    }
  ],
  "figure_notes": "截图来自原视频，版权归原作者所有。"   // optional footer for the gallery
}
```

Generated visuals (`diagram`, `table`) are drawn by the page itself, so they work with or without captured frames. Use `flow` for processes and timelines (3–6 items), `layers` for hierarchies and levels (bottom item = first), `compare` for 2–4 options side by side; keep `text` to one short line. Tables: 2–5 columns, up to ~8 rows.

Before building, run `scripts/check_style.py content.json` (see `style-guide.md`).

Rules the script enforces (it exits with a clear message otherwise):
- every `figure` block id exists in `figures`;
- every `figures[].file` exists in the `--frames` folder;
- `insights`, `mindmap.branches`, `article.blocks` are non-empty.

`flashcards` and `figures` may be empty; their tabs are then hidden.
