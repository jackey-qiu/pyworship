# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`pyworship` generates PowerPoint files for Sunday worship services at a Chinese Christian church (汉堡华人基督教会). Given a date, it reads content text files and background images, then produces a fully laid-out `.pptx`.

## Running

```bash
pip install python-pptx lxml

# Interactive (prompts for date)
python ppt_worker.py

# Pass date directly
python ppt_worker.py 2023-09-03
```

The script validates that all six content files exist for the given date before proceeding; it prints the missing files and exits if any are absent.

Output is saved as `<date>.pptx` in the project root.

## Content files

All content lives in `content/` as UTF-8 text files named `<type>_<yyyy-mm-dd>.txt`. The six required types are:

| File prefix | Content |
|-------------|---------|
| `pray_list_` | Prayer items (代祷事项) |
| `preach_list_` | Sermon outline (证道) |
| `song_list_` | Worship + response songs (诗歌) |
| `scripture_list_` | Three scripture sections (宣召, 启应经文, 读经) |
| `report_list_` | Announcements (报告) |
| `worker_list_` | Service roster for this week and next (服事人员) |

### Content file format

Sections inside each file are delimited by a line starting with `#`. Everything between one `#` line and the next belongs to that section. The `#` line itself is not content — it is only used as a separator/marker. Example:

```
#1
First section line 1
First section line 2
#2
Second section line 1
```

`_prepare_content_list()` builds a list-of-lists from this structure.

### Scripture shorthand (scripture_list)

Sections 1 (宣召) and 3 (读经) accept a compact reference format when `use_json_for_extracting_scripture = True` (the default). The JSON Bible at `src/bible/chinese_bible.json` is used to expand them. Format:

```
书名:章[起-止,单个,*]
```

Multiple references are joined by `+`. Examples:
- `诗篇:136[1-9,23-26]` — Psalm 136 verses 1–9, 23–26
- `约翰一书:3[*]` — all verses of 1 John 3
- `创世记:1[1-3]+约翰福音:3[16]` — two separate passages

Section 2 (启应经文) is always raw text (no shorthand).

### Song list format

Each song occupies one `#N` section. Line 1 = song title, line 2 = album/source subtitle, remaining lines = lyrics. Verse sections within a song are separated by a blank line; this drives the per-page layout in `prepare_slides_for_one_song`. The last `#` section is the response song (回应诗歌).

## Architecture

All logic is in a single class `MakeWorkshipPpt` in `ppt_worker.py`.

**Initialisation** (`__init__`): sets paths, detects whether the date falls in the first week of the month (`holy_dinner`, day ≤ 7), then calls `prepare_slide_contents()` to load all text data into instance attributes (`self.pray_list`, `self.song_list`, etc.).

**Slide generation** (`prepare_workship_slides`): calls section methods in worship-service order:

```
pray → worker → begin slides → 宣召 → songs → 启应经文 → main pray
  → scripture reading → preaching → response song → offering
  → report → new friends → worker (next week) → end slides
```

**`make_one_slide(blocks, ...)`**: the core rendering primitive. Each `block` dict specifies:
- `cont` — list of text lines
- `textbox` — `[left, top, width, height]` as `Cm(...)` expression strings (evaluated with `eval`)
- `font_global` / `font_run` — `'FontName+SizePt+Bold'` strings parsed with `rsplit('+')`
- `alignment` — `'ALIGN+line_spacing+space_before+space_after+level'` parsed with `rsplit('+')`

A `+` character in a text line splits it into two runs with different font sizes (used for superscript verse numbers in scripture slides via `superscript_first_char=True`).

**Holy dinner**: if `holy_dinner` is `True`, `prepare_end_slides` uses `src/holy_dinner/end_1.jpg` … `end_22.jpg` instead of the regular seven ending slides.

## Known manual post-processing

After generation, the following must be done manually in PowerPoint:
- Numbered lists in pray (代祷事项) and sermon (证道) slides need list formatting reapplied.
- All slide animations must be added manually.
- Some title text may need minor adjustments.
