---
name: ddtoolbox-fart
description: Architecture guide for the multi-call ddpico binary, standalone applets, DirectoryCrawler, and safe file operations.
version: 1.2.20260917131535Z
load: always
---

# ddtoolbox-fart

## Multi-Call Architecture (`ddpico`)
The `ddpico` binary provides a single compiled executable or entry point that
acts as multiple utilities via multi-call dispatch:
- `ddpico <applet> [args...]`
- Symlinks to `ddpico` (e.g. `ln -s ddpico ddfart` or `ddpico --install-symlinks <DIR>`) automatically dispatch based on `argv[0]`.
- Built-in applets:
  - `fart`, `ddfart`, `pyfart`: Find And Replace Text across files, directories, PDFs, and eBooks.
  - `bak`, `ddbak`: Backup tool using `.bakignore` filters.
  - `crawler`, `ddcrawl`, `crawl`: Directory crawler with fluent filtering.
  - `datetime`, `dddatetime`: Datetime conversions, arithmetic, and formatting.
  - `znumber`, `ddznumber`: Number conversions (hex, dec, bin, oct, roman, word).
  - `mediadownloader`, `ddmediadownloader`: Media downloader.
  - `tts`, `ddtts`: Text-to-speech utility.
  - `version_get_from_filepath`: Extract version timestamp from file paths.

## FART Subsystem
- Located in `ddpico/fart_*.py` and facade `ddpico/fart.py`.
- Full compatibility with gofart:
  - Text search and replacement with case adaption (`--case-adapt`).
  - Whole-word matching (`--word`).
  - Recursive directory tree walking (`--recurse`).
  - Binary file guards (`--allow-binary`).
  - Dry-run preview (`--dry-run`).
  - Link fixing in PDFs and eBooks (`--fixlinkinpdfandebook`).
  - Rulefile loading (`--rulefile <path>`).
- Scripting integration:
  - Callable in ddpico scripts and formulas via `=fart(...)`.

## DirectoryCrawler
Fluent builder in `ddpico/crawler.py`:
```python
crawler = (
    DirectoryCrawler(root=".")
    .recursive(True)
    .include_wildcards("*.py", "*.md")
    .exclude_wildcards("*.tmp")
    .max_depth(3)
    .min_size(10)
    .max_size(1_000_000)
    .follow_symlinks(False)
)
for path in crawler.walk_files():
    print(path)
```

## Universal Safe File Operations
Located in `ddpico/files.py`:
- `file_copy(source, destination, overwrite=FileOverwriteOption.never, ...)`
- `file_move(source, destination, overwrite=FileOverwriteOption.never, ...)`
- `file_rename(source, destination, overwrite=FileOverwriteOption.never, ...)`
- Overwrite options supported via `FileOverwriteOption` (`never`, `always`, `only_if_destination_file_is_older`, `only_if_destination_file_is_newer`, `only_if_destination_file_is_smaller`, `only_if_destination_file_is_bigger`, `only_if_destination_file_is_different`, `ask_user`).
