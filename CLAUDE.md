# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyGOD (pyworship) is a PyQt5 + MongoDB desktop application suite for a Chinese Christian church (CCG) to manage worship services. It ships four apps under a single `ccg` CLI entry point.

## Installation & Launch

```bash
pip install .          # installs the package and registers the `ccg` entry point
ccg --help             # lists available subcommands
ccg reader             # launch Bible reader GUI
ccg scheduler          # launch database/scheduler GUI
ccg ppt 2023-09-03     # generate worship PPT for a date (--v 1|2 for communion song variant)
```

## Building the Executable

```bash
cd pygod/bin
pyinstaller ccg.spec   # output in pygod/bin/dist/ccg/
# After build: manually copy the `pptx` package from site-packages into dist/ccg/
```

## Architecture

### Entry Point
`pygod/bin/app_dispatcher.py` — Click group that registers the three subcommands (`ppt`, `reader`, `scheduler`).

### Apps (`pygod/apps/`)

| App | `ccg` subcommand | Entry script | Purpose |
|---|---|---|---|
| `ppt_worker` | `ppt <date> [--v 1\|2]` | `scripts/ppt_worker.py` | Generates `.pptx` worship slides from text content files; `--v` selects holy communion song variant (1=靠近十架, 2=宝架清影) |
| `bible_reader` | `reader` | `scripts/bible_reader_gui.py` | Chinese/English Bible reader with search (Whoosh + Jieba), media playback |
| `py_scheduler` | `scheduler` | `bin/manager_gui.py` | PyQt5 GUI for MongoDB — schedules worship roles, tracks finances, library, personnel, attendance |
| `bulletin_worker` | *(not wired to `ccg`)* | `scripts/bulletin_worker.py` | Generates monthly church bulletin as a `.docx` Word document |

### PPT Worker Data Flow

Content lives in `pygod/apps/ppt_worker/src/contents/` as dated text files:
- Files are named `{list_type}_{yyyy}-{mm}-{dd}.txt` (e.g., `song_list_2023-09-03.txt`)
- Required list types: `pray_list`, `preach_list`, `song_list`, `scripture_list`, `report_list`, `worker_list`
- Sections within each file are delimited by lines starting with `#`
- `scripture_list` supports a compact reference syntax: `book:chapter[verse_ranges]+...` where ranges can be `1-5`, individual `9`, or `*` for whole chapter

Bible data: `pygod/apps/ppt_worker/src/bible/chinese_bible.json`  
Background slide images: `pygod/apps/ppt_worker/src/bkg_slides/` (subdirs: `others/`, `holy_dinner_option1/`, `holy_dinner_option2/`)

### Scheduler / DB Layer

`pygod/apps/py_scheduler/config/db_matching.yaml` is the schema config that maps MongoDB collections and fields to Qt widget names. All DB modules in `core/db_opts/` read this YAML — adding a new DB field means updating both the YAML and the corresponding `.ui` file.

`core/db_opts/` contains one module per MongoDB database type (`db_opts_entry.py`, `db_opts_bulletin.py`, `db_opts_book.py`, `db_opts_finance.py`, `db_opts_hymn.py`, `db_opts_personal.py`, `db_opts_ppt.py`, `db_opts_task.py`). `common_db_opts.py` holds shared Pandas/table-view helpers used by all of them.

MongoDB Atlas credentials are handled at login time; the app requires a live Atlas connection to function.

### UI Files

PyQt5 `.ui` files live in `pygod/apps/py_scheduler/ui/`. Load via `uic.loadUi(ui_path, self)` in `manager_gui.py`. Widget names in `.ui` files must match the string keys in `db_matching.yaml`.

## Key Dependencies

`PyQt5`, `pyqtgraph`, `pyqtchart`, `pymongo`, `python-pptx`, `python-docx`, `jieba`, `whoosh`, `yt-dlp`, `pypinyin`, `qdarkstyle`, `bcrypt`, `python-dotenv`, `pandas`, `numpy`, `dnspython`, `click`, `pyyaml`, `qrcode`
