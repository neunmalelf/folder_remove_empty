# Goal — FOLDER_REMOVE_EMPTY, Python + tkinter port

Implementation plan for the Python rewrite of the Go program that lives in
`~/projects/_folder_remove_empty`. The behavioral contract is
`project_specs.md` (identical in both trees); it wins over every
implementation detail in the Go sources. The Go code was read only to learn
what the spec states in prose: the exact message shapes, the keep-list
matching, the order of the run phases, the dry-run output and the window
layout.

Status: plan only. Nothing is implemented yet.

---

## 1. Goal

Ship a Python 3 program `folder_remove_empty` that

- removes every empty folder below a start folder, deepest first;
- has one shared engine with **two front ends** — a **tkinter window**
  (default) and a **terminal mode** (`--no-gui`);
- is modular: a reusable, GUI-free core module plus thin front-end modules,
  every class and function reusable from other programs;
- ships `README.md`, a man page, a tldr page, `ChangeLog.md`, `NEWS` and
  `pyproject.toml`;
- keeps every rule of `project_specs.md` (§2 engine, §3 kept folders, §4
  message catalog, §5 command line, §6 terminal streams, §7 window, §8
  dialogs, §9 history filters, §11 safety guarantees).

Stdlib only, no third-party runtime dependency: `tkinter` is the window, the
engine is pure stdlib (`os`, `pathlib`, `threading`, `queue`, `enum`,
`dataclasses`).

## 2. Decisions taken

| Topic | Decision | Why |
|---|---|---|
| GUI toolkit | `tkinter` (stdlib) | user request |
| Module style | flat `remove_empty_folder_*.py` modules in the project root | direct ask (`remove_empty_folder_core.py`); a single-program tool needs no package nesting, and the flat modules are importable from anywhere |
| Core purity | `remove_empty_folder_core.py` imports **no** `tkinter`, no `argparse`, no `sys` | the engine is reusable by other projects and unit-testable headless |
| Symlinks | `os.scandir` + `entry.is_dir(follow_symlinks=False)` | Go's `ReadDir` is Lstat-based; a link to a folder is a link and blocks its parent (spec §2.2). `pathlib.Path.is_dir()` follows links and would be wrong |
| Start path | `os.path.abspath`, never `os.path.realpath` | spec §2.1: resolved like `cd PATH && pwd`, links stay visible |
| Removal | `os.rmdir` | rmdir semantics, refuses a non-empty folder (spec §2.3) |
| Threading | one `threading.Thread` per run, updates over a `queue.Queue`, drained by `root.after` | the only thread-safe way to drive tkinter; replaces the Go `post` + lock + invalidate pattern |
| Pause/stop | `threading.Condition` in `RunControl` | direct port of the Go `runControl` |
| Standard folder dialog | `tkinter.filedialog.askdirectory` | that *is* the desktop standard dialog under tkinter (spec §8.1); the built-in picker is the fallback for a missing or failing dialog |
| Icons | reuse the 8 PNGs already in `assets/icons/`, set with `iconphoto` (Tk 8.6 PNG), `iconbitmap` as fallback | spec §10, no new assets needed |
| Version | `x.x.YYYYMMDDhhmmssZ` from `~/sbin/timestamp`, kept in one module and mirrored in `pyproject.toml` | the `shift-version` skill of this repository; `~/sbin/timestamp` currently prints `20260927090253` |
| Python floor | `>=3.10` | `X \| None` unions, `dataclasses(slots=True)`, modern typing without a 3.13-only dependency |
| Docstrings | what-and-when + `usage:` + `returns:` + `example:`, Google style | the `skill_docstring_format` convention of this repository; also feeds mkdocstrings |

## 3. What the project root already carries

The root was seeded from the ddpico template and still describes the Go
program. It is reused, not reinvented:

| Existing | Action in this port |
|---|---|
| `pyproject.toml` | **rewrite** — it is a ddpico copy (`name = "ddpico"`, 16 console scripts, ddpico packages). New: distribution `folder-remove-empty`, one script `folder_remove_empty`, `py-modules` instead of packages, pytest/ruff/mypy config, dev extra |
| `README.md` | **rewrite** — currently a Go/Gio description (mentions `cmd/`, Gio, cgo). New: Python/tkinter documentation |
| `ChangeLog.md`, `NEWS` | **rewrite** — currently the Go release history. New: the first Python release entry describing the port |
| `Makefile` | repoint to the Python targets (it is the Go Makefile) |
| `assets/icons/*.png` (16…512) + `make_icons.sh` | keep as they are; the Go `icons/` folder becomes these |
| `assets/folder-remove-icon.svg` | keep (mkdocs logo) |
| `mkdocs.yml` | **rewrite** — `site_name: ddpico`, ddpico nav. New nav: Home, Install, Usage, Window, Kept folders, Man page, tldr, Development, ChangeLog, NEWS |
| `docs/` (created by `_docs`) | the mkdocstrings API reference of the modules |
| `_build`, `_install`, `_tests`, `_run`, `_docs`, `_git`, `_menu`, `_check_version`, `_skill_sync` | the repository's own infrastructure scripts — reuse them, do not duplicate their job in the Makefile |
| `history/` (`changes`, `goals`, `plans`, `prompts`, `todo`, `ideas`, `tests`) | archive one snapshot per release via the `history-tracker` skill |
| `tests/` (empty), `tldr/` (empty), `notes/`, `scratch/`, `completions/`, `dist/`, `release/` | fill `tests/` and `tldr/`; the rest stay as they are |
| `LICENSE` (MIT), `AGENTS.md`, `.agents/skills/` | unchanged |

`project_specs.md` is the Go tree's copy and is identical here; it stays the
source of truth.

## 4. File layout

New or rewritten files, everything else stays as it is:

```text
folder_remove_empty_pi/
├── pyproject.toml                  # rewritten: name, one script, py-modules, tools
├── README.md                       # rewritten
├── ChangeLog.md                    # rewritten (first entry = the port)
├── NEWS                            # rewritten (first entry = the port)
├── Makefile                        # repointed to the Python targets
├── mkdocs.yml                      # repointed to this project
├── folder_remove_empty.py          # entry point: main(), exit code
├── remove_empty_folder_version.py  # __VERSION__, APP_NAME, version_banner()
├── remove_empty_folder_core.py     # THE ENGINE (no tkinter, no argparse)
├── remove_empty_folder_options.py  # command line, usage text, environment
├── remove_empty_folder_report.py   # terminal reporter + ANSI colors
├── remove_empty_folder_docs.py     # man page + tldr page generators
├── remove_empty_folder_theme.py    # light/dark palettes, importance colors
├── remove_empty_folder_gui.py      # tkinter window, help dialog, folder picker
├── assets/icons/                   # kept as they are (8 PNGs + make_icons.sh)
├── tldr/folder_remove_empty.page.md
└── tests/                          # pytest, one module per source module
```

The Go files are not translated one-to-one; each becomes part of a module:

| Go file | Python home |
|---|---|
| `scan.go`, `execute.go`, `keep.go` | `remove_empty_folder_core.py` |
| `options.go` | `remove_empty_folder_options.py` |
| `reporter.go` | `remove_empty_folder_report.py` |
| `man.go`, `tldr.go` | `remove_empty_folder_docs.py` |
| `theme.go` | `remove_empty_folder_theme.py` |
| `ui.go`, `icon.go` | `remove_empty_folder_gui.py` |
| `run.go`, `version.go` | `folder_remove_empty.py`, `remove_empty_folder_version.py` |
| `*_test.go` | `tests/test_*.py` |

`--print-man` and `--print-tldr` generate `tldr/…` and the man page from the
code, so neither can drift from the behavior (spec §10).

## 5. Module contracts

### 5.1 `remove_empty_folder_core.py` — the engine

No `tkinter`, no `argparse`, no `sys` I/O. Mirrors `scan.go` + `execute.go` +
`keep.go`; this is the module other projects import.

```python
ENV_EXCLUDES = "FOLDER_REMOVE_EMPTY_EXCLUDE"

class FolderRemoveEmptyError(Exception): ...     # the reason behind "ERROR: …"

@dataclass
class Options:
    start_path: str = ""       # "" = the current folder
    dry_run: bool = False
    verbose: bool = False
    excludes: str = ""         # ":" separated extra kept names
    no_gui: bool = False

class Action(IntEnum):         # REMOVED, FAILED, KEPT

@dataclass(frozen=True)
class Event:                   # folder, action, dry_run, err
    def text(self) -> str:     # "removed: x" | "would remove: x"
                              # | "not removed: x (reason)" | "excluded, kept: x"

@dataclass
class Summary:                 # start_path, dry_run, folders, removed, failed, stopped

class Observer(abc.ABC):       # the one interface both front ends implement
    def start(self, start_path: str) -> None: ...
    def current(self, folder: str) -> None: ...
    def done(self, event: Event) -> None: ...
    def summary(self, summary: Summary) -> None: ...
    def checkpoint(self) -> bool: ...      # False ends the run

@dataclass
class Scan:
    root: str
    order: list[str]            # children before parents
    vacant: set[str]
    kept: set[str]
    def mark_deletes(self) -> set[str]

def resolve_start(path: str) -> str                 # raises FolderRemoveEmptyError
def scan_tree(root: str, extras: list[str]) -> Scan
def mark_deletes(scan: Scan) -> set[str]            # thin wrapper, or the method above
def split_excludes(list_: str) -> list[str]
def excluded_name(name: str, extras: list[str]) -> bool
def execute(options: Options, observer: Observer) -> Summary   # raises on a bad path

class RunControl:
    def checkpoint(self) -> bool
    def pause(self) -> bool
    def stop(self) -> None
```

**`resolve_start`** — empty path → `os.getcwd()`; a given path must exist
(`OSError` → `FolderRemoveEmptyError("the given path does not exist: {path}")`)
and must be a directory (`"the given path is not a folder: {path}"`); returns
`os.path.abspath(path)`.

**`scan_tree`** — walks `root` with `os.scandir`, `follow_symlinks=False`. A
folder is **vacant** when it can be read and *every* entry is a directory that
is vacant itself; an unreadable folder raises inside the walk and is therefore
**not** vacant. Every folder below `root` is appended to `Scan.order`
children-first; `root` is never in `order` — the start folder is never removed
(spec §2.1). An unreadable `root` yields an empty scan, as in Go; the caller
has already checked the path.

**`mark_deletes`** — walks `order` **reversed** (top down). A vacant folder is
marked unless it is kept and its parent is not marked; then it is marked too.
That reproduces spec §3.3 exactly: a kept folder goes with a parent that is
empty apart from empty kept folders, and stays when only kept folders hold the
parent in place.

**`execute`** — the five phases of spec §2.4:

1. `resolve_start` → the error propagates to the caller (exit code 1);
2. `observer.start(start)`;
3. `scan_tree(start, split_excludes(options.excludes))` + `mark_deletes`,
   `summary.folders = len(scan.order)`;
4. loop over `scan.order`, deepest first:
   - `observer.checkpoint()` first — `False` → `summary.stopped = True`, break;
   - not marked → verbose and vacant and kept → `current` + `done(KEPT)`;
   - a refused child (`failed[folder]`) → mark the parent failed, skip;
   - dry run → `current` + `done(REMOVED, dry_run=True)`, `removed += 1`;
   - else `os.rmdir(folder)`: on `OSError` → `done(FAILED, err=...)`,
     `failed += 1`, mark the parent failed, continue; else `done(REMOVED)`;
5. `observer.summary(summary)`; return the summary.

**`split_excludes` / `excluded_name`** — verbatim port of `keep.go`: the fixed
names `.Trash-1000`, `.cache`, `$RECYCLE.BIN`, `.$RECYCLE.BIN`,
`System Volume Information`; the prefix `ZZZZ`; four leading ASCII digits; the
marker `!!! MISSING !!!` in any letter case; plus the extras, where a trailing
`*` makes a prefix rule and anything else an exact name. `split_excludes` drops
empty pieces, so a trailing or doubled `:` adds nothing.

**`RunControl`** — `paused`/`stopped` plus a `Condition`. `checkpoint()` waits
while paused and returns `not stopped`; `pause()` toggles, is a no-op when
stopped and returns the new state; `stop()` sets stopped, clears paused and
notifies.

### 5.2 `remove_empty_folder_version.py`

```python
__VERSION__ = "1.0.20260927090253Z"      # x.x.YYYYMMDDhhmmssZ, ~/sbin/timestamp
APP_NAME = "folder_remove_empty"
APP_NAME_VERBOSE = "FOLDER_REMOVE_EMPTY"
def version_banner() -> str               # "folder_remove_empty version 1.0.…Z"
```

`pyproject.toml` reads it through
`[tool.setuptools.dynamic] version = {attr = "remove_empty_folder_version.__VERSION__"}`
so the two can never disagree; `_check_version` verifies the stamp.

### 5.3 `remove_empty_folder_options.py` — the command line

Port of `options.go`. `getenv` is an injected callable defaulting to
`os.environ.get`, so the tests stay hermetic.

```python
class Command(IntEnum):  # RUN, HELP, VERSION, MAN, TLDR
class UnknownOptionError(FolderRemoveEmptyError):   # carries .option
def new_options(getenv=None) -> Options
def parse_args(args, getenv=None) -> tuple[Options, Command]     # raises
def usage() -> str        # the Go usage text, verbatim, Tk-safe (no markup)
```

- `-d|--dryrun|--dry-run`, `-v|--verbose`, `--no-gui`, `-h|--help`,
  `--version`, `--print-man`, `--print-tldr`; the four informational options
  return immediately with their command;
- an unknown `-…` → `UnknownOptionError` (the caller prints `ERROR:` **and**
  the usage text);
- a second path → `only one path is allowed, got: {arg}` (the caller prints only
  the error);
- `FOLDER_REMOVE_EMPTY_EXCLUDE` pre-fills `Options.excludes`.

`usage()` is the single source of the help text: `--help`, the help dialog and
`README.md` all show it (spec §7.6).

### 5.4 `remove_empty_folder_report.py` — the terminal front end

Port of `reporter.go` including the `paint` / `color_code` helpers.

```python
class TerminalReporter(Observer):
    def __init__(self, options, out=sys.stdout, err=sys.stderr, getenv=None)
```

- stdout: `removed: <folder>` (green) and the closing summary;
- stderr: `path exists: <folder>` (only when a path was given), `start folder:`,
  `excluded, kept:`, `not removed: <folder> (<reason>)` (yellow),
  `<n> folder(s) kept`, `ERROR:` (red);
- a dry run prints the **plain path**, one per line, on stdout, and no summary;
- `current()` is a no-op, `checkpoint()` returns `True`;
- colors only when the stream is a tty and `NO_COLOR` is empty
  (`"\033[31m"`, `"\033[32m"`, `"\033[33m"`, off `"\033[0m"`).

### 5.5 `remove_empty_folder_docs.py` — generated documentation

Port of `man.go` + `tldr.go`; both pages are built from the same facts as the
usage text.

```python
TLD_EXAMPLES: list[tuple[str, str]]    # 8 examples of spec §5.6
def man_page() -> str     # roff: TH, NAME, SYNOPSIS, DESCRIPTION, OPTIONS,
                          # THE WINDOW, KEPT FOLDERS, ENVIRONMENT, EXIT STATUS,
                          # EXAMPLES, SEE ALSO
def tldr_page() -> str    # markdown: the head, then per example
                          # "- description", blank line, "  `command`"
```

The tldr command keeps the backticks and the two-space indent: tealdeer 1.7.3
drops a bare indented line, so the page would show descriptions and no
commands. Keep the Go comment about it.

### 5.6 `remove_empty_folder_theme.py` — the two themes

Port of `theme.go`; tkinter takes `#rrggbb` strings.

```python
@dataclass(frozen=True)
class Theme:   # bg, fg, border, accent, success, medium, low, warning, danger

LIGHT = Theme("#ffffff", "#000000", "#8a8a8a", "#7e57c2",
              "#2e7d32", "#9c6d00", "#757575", "#e65100", "#c62828")
DARK  = Theme("#121212", "#ffffff", "#b0b0b0", "#7e57c2",
              "#81c784", "#ffb74d", "#bdbdbd", "#ff8a65", "#ef5350")

def importance_color(importance: str, dark: bool) -> str
def theme_button_label(dark: bool) -> str      # "Dark mode" / "Light mode"
```

The importance levels map 1:1 onto spec §7.4: removed→success, dry-run
`would remove`→medium, kept→low, refused→warning, error→danger, run
notes→default foreground. The window starts in the **light** theme (§7.1).

### 5.7 `remove_empty_folder_gui.py` — the tkinter window

```python
def run_gui(options: Options, getenv=None) -> int      # blocks until the window closes

class MainWindow:        # the frame of spec §7.2
class HelpDialog:        # spec §7.6
class FolderPicker:      # spec §8.2 fallback
class GuiObserver(Observer):    # only puts updates into a queue
class HistoryItem:       # text, importance, kind
```

**Layout**, top to bottom, exactly spec §7.2 — `grid` on the root frame, the
history taking the leftover weight:

| Row | Widgets |
|---|---|
| 1 | `Start path` label, `Entry` (pre-filled), `Browse…` `Button` |
| 2 | status `Label` — green `path exists: <absolute folder>` or red `ERROR: <reason>` |
| 3 | `Dry run` and `Verbose` `Checkbutton`s side by side |
| 4 | `Extra excludes` label + `Entry` |
| 5 | `Show in history` label + 4 `Radiobutton`s: All, Removed, Kept, Not removed |
| 6 | five equally weighted buttons with 8-unit gaps: `Help`, theme toggle, `Exit`, `Pause`, `Start` |
| 7 | `Current folder` label + read-only `Entry` (placeholder `no folder yet`) |
| 8 | bold `History` label |
| 9 | `ScrolledText` history — bordered, scrollable, auto-scrolled to the end |

**Threading** — the engine is GUI-free and blocking, so:

- `Start` validates the path, spawns one `threading.Thread(target=job)` and
  hands the observer a `RunControl` and a `queue.Queue`;
- `GuiObserver` only `put`s `(kind, payload)` tuples, it never touches a widget;
- `MainWindow` drains the queue in `after(50, self._drain)`, applies the update
  and re-arms — this replaces the Go `post`/lock/invalidate pattern;
- a per-run **token** (a monotonically increasing generation counter) makes the
  newest run the only owner of the window: updates of an older run are dropped,
  which is how "Restart replaces the live run" and "closing drops late updates"
  are realized (spec §7.5);
- an exception inside the worker is caught and posted as
  `ERROR: internal failure: <reason>`, the window stays open (spec §7.5).

**Behavior wiring**

- path `Entry` → a debounced `after` → `check_path()` → the status line;
- `Browse…` → `filedialog.askdirectory(initialdir=<field or cwd>)`; the result
  is inserted into the field and re-checked; a `TclError` or a missing dialog
  opens the built-in `FolderPicker`;
- `FolderPicker` (§8.2): heading `Choose folder`, the listed folder, a red error
  line only when the folder cannot be read, an `Up` button, a bordered `Listbox`
  of subfolders (alphabetical, directories only), and a bottom row with equal
  `Select` and `Cancel` buttons;
- `Start` / `Restart`: a refused path appends a red `ERROR:` history line and
  starts nothing; a valid path stops the run in flight and starts over; the
  label is `Start` when idle and `Restart` while running, and the row returns to
  idle when the run ends;
- `Pause`: disabled while idle, toggles `RunControl.pause()`, the label flips to
  `Resume`, no effect on a stopped run;
- `Exit`: stop the control, then `root.destroy()`; queue updates after the close
  are discarded because the `after` loop is gone;
- theme toggle: repaint every widget's `background`/`foreground`,
  `activebackground`, the history tags and the button label;
- a filter change re-renders the whole list from the item list; an item with
  `kind == ""` (run notes, closing lines) shows in every filter (spec §9);
- window: `title(f"{APP_NAME_VERBOSE} {__VERSION__}")`, `geometry("960x720")`,
  `iconphoto(True, PhotoImage(file=assets/icons/…-512.png))` with a
  `TclError` fallback to the 32 px file;
- `HelpDialog` replaces the main content in the same root: heading, a bordered
  `ScrolledText` of `usage()`, an `OK` button.

## 6. Entry point — `folder_remove_empty.py`

Port of `run.go`:

```python
def main(argv: list[str] | None = None, out=sys.stdout, err=sys.stderr,
         getenv=None) -> int
```

1. `parse_args` → on `UnknownOptionError`: `ERROR: …` **and** `usage()` → `1`;
   on any other `FolderRemoveEmptyError`: `ERROR: …` → `1`;
2. `HELP` / `VERSION` / `MAN` / `TLDR` → print to stdout, return `0`;
3. `options.no_gui` → `execute(options, TerminalReporter(...))`; an
   `FolderRemoveEmptyError` becomes `ERROR: …` + `1`;
4. otherwise `run_gui(options)` and return `0`.

`if __name__ == "__main__": raise SystemExit(main())`; `pyproject.toml` exposes
it as the console script `folder_remove_empty`.

## 7. Documentation and packaging deliverables

| File | Content |
|---|---|
| `pyproject.toml` | setuptools backend, `name = "folder_remove_empty"`, `dynamic = ["version"]` from `remove_empty_folder_version.__VERSION__`, `requires-python = ">=3.10"`, `dependencies = []`, `[project.scripts] folder_remove_empty = "folder_remove_empty:main"`, MIT license, classifiers, `[project.urls]`, `[tool.setuptools] py-modules = [...]`, `[tool.pytest.ini_options]`, `[tool.ruff]` (line-length 100), `[tool.mypy]`, dev extra `pytest`/`ruff`/`mypy` |
| `README.md` | what it does, requirements (Python 3.10+, `python3-tk` on Fedora/Debian), install (`pipx install .`, `make install`), the window guide, the terminal guide, the kept-folder list, the environment variables, the exit codes, examples, the test command, links to man/tldr/ChangeLog/NEWS. No Gio, no cgo, no `zenity`, no `cmd/` |
| `tldr/folder_remove_empty.page.md` | generated by `folder_remove_empty --print-tldr` |
| man page | `man/folder_remove_empty.1`, generated by `folder_remove_empty --print-man` (the Go tree kept it in `man/`; here `man/` is created or the page is written to `docs/`) |
| `docs/` (mkdocs, via `_docs`) | the mkdocstrings API reference of the seven modules |
| `ChangeLog.md` | per-version log, newest first, `## x.x.YYYYMMDDhhmmss - YYYY-MM-DD`, `### Added / Changed / Fixed / Removed` |
| `NEWS` | prose highlights per release: `* Version x.x.YYYYMMDDhhmmss (date)`, a bolded headline, an indented paragraph |
| `Makefile` | `help`, `test`, `run`, `man`, `tldr`, `icons`, `install`, `uninstall`, `clean`, `final`; `install` puts the launcher in `~/sbin` and the icons into `~/.local/share/icons/hicolor/<size>x<size>/apps`; delegate the heavy lifting to `_build`, `_tests`, `_install`, `_docs`, `_check_version` |
| `mkdocs.yml` | `site_name: folder_remove_empty`, a favicon and logo from `assets/`, a nav for this project |
| `LICENSE` | unchanged (MIT) |

The first release entry documents the port itself: "rewritten in Python, the
Gio window is a tkinter window, the rules of the Go program are unchanged".

- the gui window size position and the program options and settings must be saved at program end to the config file and reused at program start

## 8. Test plan

`pytest` in `tests/`, one module per source module, mirroring the Go test
files. `tests/testhelpers.py` provides `tmp_tree()` (builds a folder tree from
a dict), `capture()` (captures stdout/stderr) and a `FakeObserver`.

| Test module | Covers |
|---|---|
| `test_core_scan.py` | a chain of nested empty folders in one `order`; a file blocks its folder; a symlink to a folder blocks its parent; an unreadable folder is not vacant; `root` is never in `order`; the order is children-first |
| `test_core_keep.py` | every fixed name, `ZZZZ`, four-digit dates, `!!! MISSING !!!` in any case, the extras, `keep-*` prefixes, `split_excludes` dropping empty pieces |
| `test_core_mark.py` | a kept folder stays; a kept folder goes with a removed parent; a kept folder stays when only kept folders hold the parent |
| `test_execute.py` | the phase order of §2.4; a dry run removes nothing but counts; a refused removal reports the reason and skips the parent; `checkpoint()` returning `False` ends the run with `stopped`; the exact observer call sequence |
| `test_run_control.py` | pause blocks, resume releases, stop ends it, pause after stop is a no-op |
| `test_options.py` | every option, both path errors, the environment pre-fill, the `usage()` shape |
| `test_report.py` | the stdout/stderr split, every message shape, plain paths in a dry run, no colors off a tty, `NO_COLOR` |
| `test_docs.py` | the man page sections are present; the tldr page has the backticked indented command per example; every command names the program and stays on one line |
| `test_version.py` | the banner shape and that the stamp is 14 digits + `Z` |
| `test_run.py` | the `main()` exit code for every informational output and both refusals |
| `test_gui.py` | skipped without `$DISPLAY`; builds the window, checks the widget order, the status line, the history filter, the theme toggle, the pause/restart/exit labels, the drop of late updates |

The Go window tests ran headless because Gio needs no window; tkinter does need
one, so `test_gui.py` uses `xvfb-run` when there is no display, or skips.

## 9. Tasks

### Phase 1 — skeleton and packaging

- [x] rewrite `pyproject.toml`: distribution `folder_remove_empty`, the one
      console script, `py-modules`, pytest/ruff/mypy, dev extra
- [x] `remove_empty_folder_version.py` with the `~/sbin/timestamp` stamp
- [x] `folder_remove_empty.py` with `main()` that raises `NotImplementedError`
      in the GUI branch, so the package installs and `--version` works
- [x] `.gitignore` (`__pycache__/`, `*.pyc`, `build/`, `dist/`, `*.egg-info/`,
      `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`)
- [x] the `tests/` skeleton, `pytest` runs green

### Phase 2 — the engine (no GUI, no message formats)

- [x] `FolderRemoveEmptyError`, `Options`, `Action`, `Event.text()`, `Summary`
- [x] `resolve_start()` and its three error messages
- [x] `split_excludes()`, `excluded_name()`
- [x] `Scan` + `scan_tree()` (Lstat semantics, unreadable = not vacant)
- [x] `mark_deletes()`
- [x] the `Observer` ABC and `execute()` in the five phases
- [x] `RunControl` on a `Condition`
- [x] the engine tests are green

### Phase 3 — command line and terminal front end

- [x] `remove_empty_folder_options.py`: `Command`, `UnknownOptionError`,
      `new_options()`, `parse_args()`, `usage()`
- [x] `remove_empty_folder_report.py`: `TerminalReporter`, the ANSI helpers,
      tty and `NO_COLOR` handling
- [x] `folder_remove_empty.py`: wire `main()`, the exit codes of §5.5
- [x] the options, report and run tests are green
- [x] a manual smoke run against a scratch tree, in both modes, compared with
      the Go binary line for line

### Phase 4 — generated documentation

- [ ] `remove_empty_folder_docs.py`: `man_page()`, `tldr_page()`, the 8 examples
- [ ] `--print-man` and `--print-tldr` produce the files
- [ ] `tldr/folder_remove_empty.page.md` and the man page generated and committed
- [ ] the doc tests are green

### Phase 5 — the tkinter window

- [ ] `remove_empty_folder_theme.py`: the two palettes, the importance colors,
      the button label
- [ ] the window skeleton: title, 960×720, the icon, the nine rows, light theme
- [ ] the path field, the live status line, `check_path()`
- [ ] the dry run, verbose and extra excludes widgets
- [ ] the history filter radio group and the re-render
- [ ] `GuiObserver` + queue + `_drain` + the run token (with a fake run, no
      thread yet)
- [ ] the worker thread, `RunControl`, pause/resume/restart/exit
- [ ] `HelpDialog` over `usage()`
- [ ] `filedialog.askdirectory` and the `FolderPicker` fallback
- [ ] the theme toggle repaints everything
- [ ] `test_gui.py` is green (or skipped headless)

### Phase 6 — documentation and release

- [ ] `README.md` rewritten for Python/tkinter
- [ ] `mkdocs.yml` repointed, the docs built through `_docs`
- [ ] `ChangeLog.md` and `NEWS` with the port release
- [ ] `Makefile` repointed, `make final` green
- [ ] `pip install .` in a clean venv, then `folder_remove_empty --help`,
      `--version`, `--print-man`, `--print-tldr`
- [ ] the installed binary checked against a scratch tree in both modes
- [ ] the version bumped with `~/sbin/timestamp`, `_check_version` green, a git
      commit, a `history-tracker` archive

## Phase 7 

A config file in ~/.config/_folder_remove_empty/_folder_remove_empty.config



###  Open questions

**Distribution name.** : folder_remove_empty

**The existing `pyproject.toml`, `README.md`, `ChangeLog.md`, `NEWS`,
`Makefile` and `mkdocs.yml` are ddpico/Go copies.** Rewriting them in place is
assumed. The `ddpico` console scripts and the ddpico `[tool.*]` sections go
away entirely:  
answer: confirmed, the pyproject.toml must contain :



```toml
`[project]
name = "folder_remove_empty"
version = "0.1.202090927121500"
description = "ddpico - a commandline and API-driven tool plus a granular, function-based dd command toolset with a REPL, pipe, scripting, and LSP"
readme = "README.md"
requires-python = ">=3.13"
license = { text = "MIT" }
authors = [
    { name = "neunmalelf" },
]
keywords = ["backup", "bak", "zip", "toolset", "repl", "cli"]
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Topic :: System :: Archiving :: Backup",
]
# ddpico is stdlib-only by design (Nuitka supports only Python 3.13;
# zero third-party runtime dependencies).
dependencies = []

[project.optional-dependencies]
dev = [
    "ruff",
    "mypy",
    "nuitka",
    "mutmut",
]

[project.urls]
Homepage = "https://github.com/neunmalelf/folder_remove_empty"
Repository = "https://github.com/neunmalelf/folder_remove_empty"
Documentation = "https://github.com/neunmalelf/folder_remove_empty/blob/master/README.md"
"Bug Tracker" = "https://github.com/neunmalelf/folder_remove_empty/issues"

tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "F",      # pyflakes
    "I",      # isort
    "UP",     # pyupgrade
    "B",      # bugbear
    "SIM",    # simplify
]

[tool.mutmut]
source_paths = ["ddpico"]
also_copy = ["ddpicolibsec_entry.py"]
only_mutate = [
    "ddpico/formula/engine.py",
    "ddpico/fs/crawler.py",
    "ddpico/ddpicolibsec.py",
]
```



**Man page location.** The Go tree wrote `man/folder_remove_empty.1`. 

answer:  Keep a`man/` folder here

**The `_build`, `_install`, `_tests`, `_run`, `_docs`, `_git`, `_menu`,
`_check_version` scripts** were copied from ddpico and assume its layout.
answer : write this project's own `Makefile` alone?

**`.desktop` file.** The Go project has none, only the icon set. 
answer: add one so `make install` produces a real launcher?
