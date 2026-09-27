# Goal — FOLDER_REMOVE_EMPTY, Python + tkinter port

Implementation plan for the Python rewrite of the Go program that lives in
`~/projects/_folder_remove_empty`. The behavioral contract is
`project_specs.md` (identical in both trees); it wins over every
implementation detail in the Go sources. The Go code was read only to learn
what the spec states in prose: the exact message shapes, the keep-list
matching, the order of the run phases, the dry-run output and the window
layout.

Status: **all phases are implemented, released and green** — packaging, version identity,
engine, command line, terminal front end, generated man/tldr pages, the tkinter
window and the persisted settings file, with the captured Go reference pinning
the port byte for byte (colourless and coloured) and the exit codes. What
remains is upkeep: keep `./_tests`, `./_check_version` and `./_skill_sync
--check` green, extend `ChangeLog.md`/`NEWS` with every phase, and re-read this
plan when a behaviour changes.

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
`dataclasses`). The dev extra carries `pytest`, `ruff`, `mypy` and `nuitka`.

## 2. Decisions taken

| Topic | Decision | Why |
|---|---|---|
| GUI toolkit | `tkinter` (stdlib) | user request |
| Module style | flat `remove_empty_folder_*.py` modules plus the entry point in the project root | direct ask (`remove_empty_folder_core.py`); a single-program tool needs no package nesting, and the flat modules are importable from anywhere |
| Core purity | `remove_empty_folder_core.py` imports **no** `tkinter`, no `argparse`, no `sys` | the engine is reusable by other projects and unit-testable headless |
| Symlinks | `os.scandir` + `entry.is_dir(follow_symlinks=False)` | Go's `ReadDir` is Lstat-based; a link to a folder is a link and blocks its parent (spec §2.2). `pathlib.Path.is_dir()` follows links and would be wrong |
| Start path | `os.path.abspath`, never `os.path.realpath` | spec §2.1: resolved like `cd PATH && pwd`, links stay visible |
| Removal | `os.rmdir` | rmdir semantics, refuses a non-empty folder (spec §2.3) |
| Threading | one `threading.Thread` per run, updates over a `queue.Queue`, drained by `root.after` | the only thread-safe way to drive tkinter; replaces the Go `post` + lock + invalidate pattern |
| Pause/stop | `threading.Condition` in `RunControl` | direct port of the Go `runControl` |
| Standard folder dialog | `tkinter.filedialog.askdirectory`, built-in picker as the fallback | **deliberate deviation:** spec §8.1 asks for the desktop's dialog helper, which the Go tree got from `zenity`/`kdialog` (`ui.go:37`). The port uses Tk's own dialog — one fewer external program, and `askdirectory` is the standard dialog a tkinter application offers. The spec sentence and the README wording must say so, and §8.2's fallback now covers "no Tk dialog available" |
| Icons | reuse the 8 PNGs already in `assets/icons/`, set with `iconphoto` (Tk 8.6 PNG), `iconbitmap` as fallback | spec §10, no new assets needed |
| Version | one literal, `__VERSION__ = "x.x.YYYYMMDDhhmmssZ"` in `remove_empty_folder_version.py`, plus the derived `__version__ = __VERSION__.removesuffix("Z")`; `pyproject.toml` has `dynamic = ["version"]` + `[tool.setuptools.dynamic] version = {attr = "remove_empty_folder_version.__version__"}` and **no** literal | the repository stamp needs the trailing `Z` (`shift-version`, `_check_version`: `^\d+\.\d+\.\d{14}Z$`), but PEP 440 forbids it and setuptools refuses the build with `Invalid version: '1.0.20260927111114Z'` (verified). One literal, one derived packaging form, and a test that fails when they drift |
| Python floor | `>=3.13` | user decision; `nuitka` (the standalone build of `_build`) supports only 3.13, so the floor matches the build toolchain. ruff `target-version = "py313"`, classifiers and `mypy python_version` follow |
| Docstrings | what-and-when + `usage:` + `returns:` + `example:`, one blank line before the example and one before the closing quotes | the `skill_docstring_format` convention of this repository. ruff does **not** select `D`, so the format is not fought by pydocstyle |
| Settings file | §5.8: `~/.config/folder_remove_empty/folder_remove_empty.conf`, `configparser` INI, written by the window on close, read by both front ends as the lowest-precedence pre-fill (CLI wins) | phase 7 requirement |
| Window tests on a private display | every window that automation opens (tests, checks, scripts the pre-commit `gui` module) lives on a private Xvfb display (`xvfb-run -a`), never on the session screen; `FOLDER_REMOVE_EMPTY_GUI_DISPLAY=session` opts out | user request 2026-09-27: the windows flashed the working screen and made other work impossible. The policy lives in `remove_empty_folder_display.py` (one contract for tests, `make check-gui`, `make check-313`, the hook and `assets/make_screenshots.sh`), `test_private_display.py` re-runs the window modules privately and asserts the session display was left alone, and `test_script_display_policy.py` fails the suite when a new script runs the program without it. Only `make run`, `_run` and `_menu`'s `r` entry may open the real window |
| Accent colour | the palettes keep `accent` for parity with the Go original, but the window paints **no fill** with it: the indicator box of a checkbutton or radio, the selection of a field and the hover of a control use the theme background or the border grey | user request 2026-09-27: no purple background behind the checkboxes and the selection boxes. `test_gui.py` (`AccentTest`) and `reference/gui_window.txt` assert it, so it cannot slip back in |
| Man page | `man/folder_remove_empty.1`, generated by `--print-man` | user decision |
| `.desktop` launcher | `assets/folder_remove_empty.desktop`, installed by `make install` | user decision; spec §10 installs icons "so launchers … find every size", which needs a launcher file |
| Documentation site | **dropped** — `_docs` and `mkdocs.yml` are deleted | user decision; the man page, the tldr page and `README.md` carry the documentation |
| `docs/` page | one hand-written page, `docs/window-display.md`, added 2026-09-27 | user request: the policy has to be findable in a docs tree. No site, no builder, no nav — the page is linked from `README.md` and `CONTRIBUTING.md` and the documentation stays in `README.md`, the man page and the tldr page |
| Verified environment | `requirements-dev.txt` mirrors the `dev` extra with exact pins (`mypy==2.3.1`, `nuitka==4.2.1`, `pytest==9.1.1`, `ruff==0.16.5`) and CI installs **it** plus the package, not `.[dev]` | CI caught what the local interpreter could not: with `tk.Event[tk.Entry]` evaluated at import the module died on Python 3.13, the declared floor, while 3.14 was fine. `_check_pins` reports drift between the pins and the working interpreter, the pre-commit `pins` module reminds without blocking |
| Moving a command to a private display | `python3 -m remove_empty_folder_display --wrap CMD...` runs the command under `xvfb-run` with the markers and returns its exit status (`--wrap --print` shows the line); `make final` includes `make pins` (`./_check_pins --strict`), and the pre-commit `gui` module calls `make check-gui` | added 2026-09-27 with v1.4: one wrapper for scripts instead of copied xvfb flags, one invocation shared by the hook and the manual target, and a release that cannot start in a drifted environment `--wrap-sh SNIPPET` wraps a pipeline through `sh -c`; `make check-gui`, `make check-313` and `assets/make_screenshots.sh` are built on the wrapper, so no flags live in a Makefile or a script; `make check-gui` reads the `=session` opt-in itself and the hook just calls it. `make final` includes `make pins` (`./_check_pins --strict`, plus `--update` to pin a verified environment) | added 2026-09-27 with v1.4/v1.5: one wrapper for scripts instead of copied xvfb flags, one invocation shared by the hook and the manual target, and a release that cannot start in a drifted environment |
| Python floor check on demand | `make check-313` runs `make final` and `make check-gui` on Python 3.13 in a `python:3.13-slim` container, repository mounted read-only and copied inside | user request: a version-specific break must be found before a push. The container reports a dirty tree as a failure, so it can never silently rewrite the committed pages |
| Repository scripts | keep and adapt `_check_version`, `_skill_sync`, `_tests`, `_build`, `_install`, `_menu`, `_run`, `_git` | user decision; every ddpico assumption (program table, `dd*` paths, unittest, local-time stamp, speech calls) is replaced by this project's, see §3 |
| Tests | `pytest` **and** `unittest` compatible, in `tests/folder_remove_empty/`: `unittest.TestCase` classes, `__init__.py` packages, `python_files = test_*.py` | the repository skill `tests-subfolder` wants one `tests/<unit>/` subtree and working `python3 -m unittest discover -s tests -t .`; `_tests` is the runner, `pythonpath = ["."]` makes the flat modules importable from both runners |

## 3. What the project root already carries

The root was seeded from the ddpico template. The ddpico-specific pieces are
adapted or deleted; nothing is left as a stub.

| Existing | Action in this port |
|---|---|
| `pyproject.toml` | **done** — was a ddpico copy (`name = "ddpico"`, `version = "4.1.20260926190940Z"`, **12** console scripts, 20 `ddpico*` packages, ddpico `[tool.*]`, and a `[build-system]` pointing at `backend-path = ["_internal"]` while `_internal/` does not exist, so `pip install .` failed). Now: setuptools backend, distribution `folder_remove_empty`, `requires-python = ">=3.13"`, `dependencies = []`, dynamic version from the version module, one console script, `py-modules`, `[tool.pytest.ini_options]` (`testpaths`, `pythonpath`), `[tool.ruff]` (line-length 100, `py313`, E/F/I/UP/B/SIM), `[tool.mypy]`, dev extra `pytest`/`ruff`/`mypy`/`nuitka`. Verified: `pip install .` in a clean venv builds `folder_remove_empty-1.0.<stamp>` (the stamp without the trailing `Z`) and the installed console script prints the banner |
| `README.md` | **done** (phase 1 batch, re-check in phase 6) — was a Go/Gio description (mentioned `cmd/`, Gio, cgo, headless Gio tests). Now: Python/tkinter documentation with a Status block that names phase 1 as done and marks the window/terminal sections as target behaviour |
| `ChangeLog.md`, `NEWS` | **done** (phase 1 batch) — were the Go release history. Now: `## 1.0.20260927131905 - 2026-09-27` / `* Version 1.0.20260927131905 (2026-09-27)`, naming only what exists (packaging, version identity, `--version`, tests skeleton, adapted scripts, the deletions) |
| `Makefile` | **done** (phase 1 batch, re-check in phase 6) — was the Go Makefile (`build`, `vet`, `fmt`, `final: fmt-check vet test build man tldr`). Now the target set of §7, delegating to `_tests` and `_check_version`/`_skill_sync` |
| `assets/icons/*.png` (16…512) + `make_icons.sh` | keep as they are; the Go `icons/` folder becomes these |
| `assets/folder-remove-icon.svg` | keep — with the documentation site gone this is no longer a logo, it stays as the only vector original of the icon set (`make_icons.sh` draws the PNGs from scratch) |
| `mkdocs.yml` | **deleted** — the documentation site is dropped (user decision) |
| `_check_version` | keep — project-agnostic: globs `**/*.py` + `pyproject.toml` and matches `^\d+\.\d+\.\d{14}Z$` |
| `_skill_sync` | keep — project-agnostic: regenerates the skill index between the markers in `AGENTS.md`. The index was stale; it was regenerated (17 skills) and `--check` is green again, so the pre-commit module can run |
| `_tests` | **adapted** (`2.0.20260927111114Z`) — three steps: `python3 -m pytest tests/folder_remove_empty`, `python3 -m ruff check .`, `python3 -m mypy`; `--quick` runs the tests only. The `[PROGRAM]` argument, the `tests/<program>` scoping and the `_export_sync --check` step are gone |
| `_build` | **adapted** (`3.0.20260927111114Z`) — one target (`folder_remove_empty.py`), no program registry, no `ddpico speech` calls, no forced `--include-module` list (every import is static, Nuitka follows them); default one compiler job with `--lto=no` per the repository's build-parallelism rule, plus `--enable-plugin=tk-inter` so the frozen binary carries the window toolkit; `nice -n 19`/`ionice -c 3`, the musl path (container installs `python3-tkinter`) and the release/packaging machinery stay |
| `_install` | **adapted** (`3.0.20260927111114Z`) — `python3 -m pip install -e ".[dev]"`, verification imports the version module (exit 1 on failure) and reports whether `folder_remove_empty` is on PATH |
| `_menu` | **adapted** (`2.0.20260927111114Z`) — install / test / build / git / git push / run `python3 -m folder_remove_empty`; the `_symlinks`, `_bak` and `ddfart` entries are gone |
| `_run` | **adapted** (`2.0.20260927111114Z`) — `cd` to its own directory and `exec python3 -m folder_remove_empty "$@"`; the applet `case` block is gone |
| `_git` | **adapted** (`1.0.20260927111114Z`) — `__VERSION__` (was lowercase), UTC timestamp from `~/sbin/timestamp` with a `date -u` fallback (was local time), bare-timestamp commit message (the repository convention), new `-y|--yes` for non-interactive use, new `--message=MSG`; the `[Y]es/[e]dit/[n]o` loop stays the default |
| `_docs` | **deleted** — the MkDocs builder of the dropped documentation site |
| `hooks/pre-commit`, `hooks/install.sh` | **adapted** (`3.0…`/`1.4…`) — modules `version`, `skill_sync`, `ruff`, `mypy`, `tests`, `build`, `directory_hooks`; the commands are this project's (`python3 -m ruff check .`, `python3 -m mypy`, `./_tests --quick`); the `export_sync` module and every `ddpico` path are gone. `--list-modules`, `--version` and `bash -n` verified |
| `history/` (`changes`, `goals`, `plans`, `prompts`, `todo`, `ideas`, `tests`) | archive one snapshot per release via the `history-tracker` skill |
| `remove_empty_folder_display.py`, `docs/window-display.md`, `_check_pins`, `requirements-dev.txt`, `.github/workflows/checks.yml` | added 2026-09-27 (v1.2/v1.3) — the display policy every script and the tests speak, its long-form page, the dev-tool pin check (also a warn-only hook module `pins`), the pinned tool list and the CI that installs it (pytest, ruff, mypy on Python 3.13 with `python3-tk` and `xvfb`) |
| `tests/` (was empty), `tldr/` (was empty), `notes/`, `scratch/`, `completions/`, `dist/`, `release/` | `tests/folder_remove_empty/` holds the 13 test modules, the Go reference and its builder; `tldr/folder_remove_empty.page.md` and `man/folder_remove_empty.1` are generated by `make tldr` / `make man`; the rest stay as they are |
| `LICENSE` (MIT), `AGENTS.md`, `.agents/skills/` | the skill tree was pruned: `dd-module-topics` and `ddtoolbox-fart` are deleted, and `tests-subfolder`, `skill_docstring_format`, `update-docs`, `update-pyproject`, `update-tests` were retargeted from the ddpico package layout to this project's flat modules, `tests/folder_remove_empty/` and Makefile targets — 15 skills left, no `always` rule contradicts the layout, and the generated index in `AGENTS.md` is regenerated by `./_skill_sync` (`--check` green). The Go tree's own `Makefile`/`README.md`/`doc.go` were left untouched |

`project_specs.md` is the Go tree's copy and is identical here; it stays the
source of truth, with the one addition of §12 (settings file) listed in §9.

## 4. File layout

New or rewritten files, everything else stays as it is:

```text
folder_remove_empty_pi/
├── pyproject.toml                        # done: name, one script, py-modules, tools
├── README.md                             # done: Python/tkinter documentation
├── ChangeLog.md                          # done: first entry = the port
├── NEWS                                  # done: first entry = the port
├── Makefile                              # done: help/test/test-quick/run/man/tldr/icons/install/uninstall/clean/final
├── .gitignore                            # done
├── folder_remove_empty.py                # done: main(), run_terminal(), run_window()
├── remove_empty_folder_version.py        # done: __VERSION__, __version__, APP_NAME, version_banner()
├── remove_empty_folder_core.py           # done: THE ENGINE (no tkinter, no argparse)
├── remove_empty_folder_options.py        # done: command line, usage text, environment
├── remove_empty_folder_report.py         # done: terminal reporter + ANSI colors
├── remove_empty_folder_docs.py           # done: man page + tldr page generators
├── remove_empty_folder_theme.py          # done: light/dark palettes, importance colors
├── remove_empty_folder_gui.py            # done: tkinter window, help dialog, folder picker
├── remove_empty_folder_config.py         # done: settings file (§5.8)
├── assets/icons/                         # kept as they are (8 PNGs + make_icons.sh)
├── assets/folder_remove_empty.desktop    # done: launcher for `make install`
├── man/folder_remove_empty.1             # done: generated by `make man`
├── tldr/folder_remove_empty.page.md      # done: generated by `make tldr`
└── tests/                                # pytest + unittest tree
    ├── __init__.py
    └── folder_remove_empty/              # one package per namespace unit
        ├── __init__.py
        ├── testhelpers.py                # tmp_tree(), capture(), remove_tree(), FakeObserver
        ├── test_version.py               # done
        ├── test_core_scan.py             # done      (phase 2)
        ├── test_core_keep.py             # done      (phase 2)
        ├── test_core_mark.py             # done      (phase 2)
        ├── test_execute.py               # done      (phase 2)
        ├── test_run_control.py           # done      (phase 2)
        ├── test_reference.py             # done      (phases 2-3: engine, reporter and main())
        ├── test_options.py               # done      (phase 3)
        ├── test_report.py                # done      (phase 3)
        ├── test_docs.py                  # done      (phase 4)
        ├── test_theme.py                 # done      (phase 5)
        ├── test_gui.py                   # done      (phase 5)
        ├── test_config.py                # done      (phase 7)
        ├── reference/                    # done      the Go captures (colourless + pty), build_tree.sh, cases.md
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
| — (new in the port) | `remove_empty_folder_config.py`, `tests/folder_remove_empty/test_config.py` |
| `*_test.go` | `tests/folder_remove_empty/test_*.py` |

`--print-man` and `--print-tldr` generate the man page and `tldr/…` from the
code, so neither can drift from the behavior (spec §10).

## 5. Module contracts

### 5.1 `remove_empty_folder_core.py` — the engine

No `tkinter`, no `argparse`, no `sys` I/O. Mirrors `scan.go` + `execute.go` +
`keep.go`; this is the module other projects import.

```python
ENV_EXCLUDES = "FOLDER_REMOVE_EMPTY_EXCLUDE"

class FolderRemoveEmptyError(Exception):
    # the reason behind an "ERROR: …" line
    ...

class Action(IntEnum):
    # members: REMOVED, FAILED, KEPT
    ...

@dataclass
class Options:
    # start_path: str = ""   — "" means the current folder
    # dry_run: bool = False
    # verbose: bool = False
    # excludes: str = ""     — ":" separated extra kept names
    # no_gui: bool = False
    ...

@dataclass(frozen=True)
class Event:
    # folder: str, action: Action, dry_run: bool, err: OSError | None
    ...
    def text(self) -> str: ...
    # "removed: x" | "would remove: x" | "not removed: x (reason)" | "excluded, kept: x"

@dataclass
class Summary:
    # start_path: str, dry_run: bool, folders: int,
    # removed: int, failed: int, stopped: bool
    ...

class Observer(abc.ABC):
    # the one interface both front ends implement
    ...
    def start(self, start_path: str) -> None: ...
    def current(self, folder: str) -> None: ...
    def done(self, event: Event) -> None: ...
    def summary(self, summary: Summary) -> None: ...
    def checkpoint(self) -> bool: ...       # False ends the run

@dataclass
class Scan:
    # root: str, order: list[str], vacant: set[str], kept: set[str]
    ...
    def mark_deletes(self) -> set[str]: ...  # the parent-aware mark set

def resolve_start(path: str) -> str: ...            # raises FolderRemoveEmptyError
def scan_tree(root: str, extras: list[str]) -> Scan: ...
def split_excludes(list_: str) -> list[str]: ...
def excluded_name(name: str, extras: list[str]) -> bool: ...
def execute(options: Options, observer: Observer) -> Summary: ...   # raises on a bad path

class RunControl:
    def checkpoint(self) -> bool: ...
    def pause(self) -> bool: ...
    def stop(self) -> None: ...
```

`mark_deletes` exists **once**, as the `Scan` method (the Go original has it
only there); `execute` calls `scan.mark_deletes()`.

**`resolve_start`** — empty path → `os.getcwd()`; four error messages, as in
`scan.go:34-55`:

- `os.getcwd()` failing → `the current folder cannot be read: {reason}`;
- `OSError` on the given path → `the given path does not exist: {path}`;
- a non-directory → `the given path is not a folder: {path}`;
- `os.path.abspath` failing → `the given path cannot be made absolute: {path} ({reason})`.

The success path returns `os.path.abspath(path)` (cleaned, links visible).

**`scan_tree`** — walks `root` with `os.scandir`, `follow_symlinks=False`. A
folder is **vacant** when it can be read and *every* entry is a directory that
is vacant itself; an unreadable folder raises inside the walk and is therefore
**not** vacant. Every folder below `root` is appended to `Scan.order`
children-first; `root` is never in `order` — the start folder is never removed
(spec §2.1). An unreadable `root` yields an empty scan, as in Go; the caller
has already checked the path.

**`Scan.mark_deletes`** — walks `order` **reversed** (top down), keeping
`deletes: dict[str, bool]` local. A vacant folder is marked when it is not
kept, **or** when its parent is marked: `mark = vacant and (not kept or
deletes[parent])`. A kept folder therefore goes with a parent that is empty
apart from empty kept folders, and stays when only kept folders hold the
parent in place — spec §3.3, exactly like `MarkDeletes` in `scan.go`.

**`execute`** — the five phases of spec §2.4:

1. `resolve_start` → the error propagates to the caller (exit code 1);
2. `observer.start(start)`;
3. `scan_tree(start, split_excludes(options.excludes))` + `mark_deletes`, then
   `summary.folders = len(scan.order)`;
4. loop over `scan.order`, deepest first, with the local `failed: dict[str, bool]`:
   - `observer.checkpoint()` first — `False` → `summary.stopped = True`, break;
   - not marked → verbose and vacant and kept → `current` + `done(KEPT)`;
   - `failed[folder]` (a refused child) → `failed[parent] = True`, skip;
   - **`observer.current(folder)`** — once for every folder that is worked, on
     the dry-run path *and* on the removal path (`execute.go:118`);
   - dry run → `done(REMOVED, dry_run=True)`, `removed += 1`;
   - else `os.rmdir(folder)`: on `OSError` → `done(FAILED, err=…)`,
     `failed += 1`, `failed[parent] = True`, continue; else `done(REMOVED)`,
     `removed += 1`;
5. `observer.summary(summary)`; return the summary.

**`Event.text()` reason** — the refused-removal reason is
`remove <path>: <strerror>` in lowercase, the shape Go's `os.Remove` prints, so
the terminal output can be diffed against the Go reference byte for byte.
`project_specs.md` §4 only fixes `<reason>`, so this is a free choice made for
fidelity; `test_reference.py` pins it.

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

### 5.2 `remove_empty_folder_version.py` — done (phase 1)

```python
__VERSION__ = "1.0.20260927131905Z"          # the repository stamp
__version__ = __VERSION__.removesuffix("Z")  # PEP 440, for setuptools
APP_NAME = "folder_remove_empty"
APP_NAME_VERBOSE = "FOLDER_REMOVE_EMPTY"

def version_banner() -> str: ...
    # "folder_remove_empty version 1.0.20260927131905Z"
```

`__VERSION__` is the only literal. `pyproject.toml` has

```toml
dynamic = ["version"]

[tool.setuptools.dynamic]
version = {attr = "remove_empty_folder_version.__version__"}
```

so the distribution version is derived, never typed twice. `_check_version`
reads `__VERSION__` (the first match in the file) and passes. The two forms are
pinned by `tests/folder_remove_empty/test_version.py`.

Re-stamp `__VERSION__` with `~/sbin/timestamp` at every release; the helper
prints 14 digits without the trailing `Z`, so the file adds it.

### 5.3 `remove_empty_folder_options.py` — the command line

Port of `options.go`. `getenv` is an injected callable defaulting to
`os.environ.get`, so the tests stay hermetic.

```python
class Command(IntEnum):
    # members: RUN, HELP, VERSION, MAN, TLDR
    ...

class UnknownOptionError(FolderRemoveEmptyError):
    # carries .option
    ...

def new_options(getenv=None) -> Options: ...
def parse_args(args, getenv=None) -> tuple[Options, Command]: ...   # raises
def usage() -> str: ...
    # the Go usage text, verbatim, Tk-safe (no markup)
```

- `-d|--dryrun|--dry-run`, `-v|--verbose`, `--no-gui`, `-h|--help`,
  `--version`, `--print-man`, `--print-tldr`; the four informational options
  return immediately with their command;
- an unknown `-…` → `UnknownOptionError` (the caller prints `ERROR:` **and**
  the usage text);
- a second path → `only one path is allowed, got: {arg}` (the caller prints only
  the error);
- `FOLDER_REMOVE_EMPTY_EXCLUDE` pre-fills `Options.excludes`; **the GUI trims
  surrounding whitespace** of the `Extra excludes` field when a run starts
  (spec §7.3).

`usage()` is the single source of the help text: `--help`, the help dialog and
`README.md` all show it (spec §7.6).

### 5.4 `remove_empty_folder_report.py` — the terminal front end

Port of `reporter.go` including the `paint` / `color_code` helpers.

```python
class TerminalReporter(Observer):
    def __init__(self, options, out=None, err=None, getenv=None): ...
    # out=None → sys.stdout, err=None → sys.stderr, resolved inside the
    # call; a default bound at import time would bypass pytest's capsys
    # and the tests' own capture helper
```

- stdout: `removed: <folder>` (green) and the closing summary;
- stderr: `path exists: <folder>` (only when a path was given), `start folder:`,
  `excluded, kept:`, `not removed: <folder> (<reason>)` (yellow),
  `<n> folder(s) kept` (only when refusals were counted), `ERROR:` (red);
- a dry run prints the **plain path**, one per line, on stdout, and no summary;
- `current()` is a no-op, `checkpoint()` returns `True` — the terminal front
  end cannot pause or stop, so it never prints the `stopped` closing line
  (spec §2.5);
- colors only when the stream is a tty and `NO_COLOR` is empty
  (`"\033[31m"`, `"\033[32m"`, `"\033[33m"`, off `"\033[0m"`).

### 5.5 `remove_empty_folder_docs.py` — generated documentation

Port of `man.go` + `tldr.go`; both pages are built from the same facts as the
usage text.

```python
TLD_EXAMPLES: list[tuple[str, str]] = ...
    # the 8 examples of spec §5.6
def man_page() -> str: ...
    # roff: TH, NAME, SYNOPSIS, DESCRIPTION, OPTIONS, THE WINDOW,
    # KEPT FOLDERS, ENVIRONMENT, EXIT STATUS, EXAMPLES, SEE ALSO
def tldr_page() -> str: ...
    # markdown: the head, then per example "- description",
    # an empty line, "  `command`"
```

The tldr command keeps the backticks and the two-space indent: tealdeer 1.7.3
drops a bare indented line, so the page would show descriptions and no
commands. Keep the Go comment about it.

### 5.6 `remove_empty_folder_theme.py` — the two themes

Port of `theme.go`; tkinter takes `#rrggbb` strings.

```python
@dataclass(frozen=True)
class Theme:
    # the nine fields, in this order:
    # bg, fg, border, accent, success, medium, low, warning, danger
    ...

LIGHT = Theme("#ffffff", "#000000", "#8a8a8a", "#7e57c2",
              "#2e7d32", "#9c6d00", "#757575", "#e65100", "#c62828")
DARK  = Theme("#121212", "#ffffff", "#b0b0b0", "#7e57c2",
              "#81c784", "#ffb74d", "#bdbdbd", "#ff8a65", "#ef5350")

def importance_color(importance: str, dark: bool) -> str: ...
def theme_button_label(dark: bool) -> str: ...     # "Dark mode" / "Light mode"
```

The importance levels map 1:1 onto spec §7.4: removed→success, dry-run
`would remove`→medium, kept→low, refused→warning, error→danger, run
notes→default foreground. The window starts in the **light** theme (§7.1).

### 5.7 `remove_empty_folder_gui.py` — the tkinter window

```python
def run_gui(options: Options, getenv=None) -> int: ...
    # blocks until the window closes

class MainWindow:      # the frame of spec §7.2
    ...
class HelpDialog:      # spec §7.6
    ...
class FolderPicker:    # spec §8.2 fallback
    ...
class GuiObserver(Observer):   # only puts updates into a queue
    ...
@dataclass(frozen=True)
class HistoryItem:     # text: str, importance: str, kind: str
    ...
```

**Start-up values** — every widget takes its initial value from `options`
(spec §1/§5.3: command-line options pre-fill the window) and, for the fields
the settings file covers, from §5.8 with `options` winning:

| Widget | Initial value |
|---|---|
| Start path `Entry` | `options.start_path` or the current folder (which the config never overrides) |
| `Dry run` checkbutton | `options.dry_run` |
| `Verbose` checkbutton | `options.verbose` |
| `Extra excludes` `Entry` | `options.excludes` when given, else the config value |
| `Show in history` radios | the config value, `All` by default |
| Theme | always light at start (spec §7.1) |

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
  line only when the folder cannot be read, an `Up` button, a bordered
  scrollable frame of **one `Button` per subfolder** (alphabetical, directories
  only) whose *press* descends into it, and a bottom row with equal `Select`
  and `Cancel` buttons — the same shape as `ui.go`'s picker, not a `Listbox`;
- `Current folder`: `GuiObserver.current` posts the folder, `_drain` writes it;
  it follows every folder that is rated or removed (not dry-run only) and stays
  on the last folder afterwards (spec §7.3);
- `Start` / `Restart`: a refused path appends a red `ERROR:` history line and
  starts nothing; a valid path stops the run in flight and starts over; the
  label is `Start` when idle and `Restart` while running, and the row returns to
  idle when the run ends;
- `Pause`: disabled while idle, toggles `RunControl.pause()`, the label flips to
  `Resume`, no effect on a stopped run;
- closing lines: `start folder:` first, then one line per outcome, then
  `stopped` when the run was stopped (spec §4), else the counters — all as
  history items with `kind == ""` so every filter shows them;
- `Exit`: stop the control, then `root.destroy()`; the settings file of §5.8 is
  written first, and queue updates after the close are discarded because the
  `after` loop is gone;
- theme toggle: repaint every widget's `background`/`foreground`,
  `activebackground`, the history tags and the button label;
- a filter change re-renders the whole list from the item list; an item with
  `kind == ""` (run notes, closing lines) shows in every filter (spec §9);
- window: `title(f"{APP_NAME_VERBOSE} {__VERSION__}")`, geometry from §5.8 or
  `960x720`, `iconphoto(True, PhotoImage(file=assets/icons/…-512.png))` with a
  `TclError` fallback to the 32 px file;
- `HelpDialog` replaces the main content in the same root: heading, a bordered
  `ScrolledText` of `usage()`, an `OK` button.

### 5.8 `remove_empty_folder_config.py` — the settings file (phase 7)

Stdlib only (`configparser`, `os`).

```python
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "folder_remove_empty")
CONFIG_PATH = os.path.join(CONFIG_DIR, "folder_remove_empty.conf")

@dataclass
class SavedSettings:
    # geometry: tuple[int, int, int, int] | None   — width, height, x, y
    # dry_run: bool = False
    # verbose: bool = False
    # excludes: str = ""
    # history_filter: str = "All"
    # dark: bool = False
    ...

def config_path() -> str: ...
def load(path: str | None = None) -> SavedSettings: ...
    # a missing, unreadable or malformed file yields the defaults; never raises
def save(settings: SavedSettings, path: str | None = None) -> None: ...
    # creates the directory, writes atomically (tmp file + os.replace)
```

- format: INI sections through `configparser` — `[window]` (`width`, `height`,
  `x`, `y`), `[options]` (`dry_run`, `verbose`, `excludes`, `history_filter`,
  `dark`);
- **precedence** CLI option > config value > built-in default;
- the **window** is the only writer, on close (`Exit`, window manager close);
  terminal runs and informational commands (`--help`, `--version`,
  `--print-man`, `--print-tldr`) never write;
- a failed write reports nothing on stdout/stderr and must not abort the close
  (spec §11 spirit: never destroy anything, never block the exit).

## 6. Entry point — `folder_remove_empty.py`

Port of `run.go`; phase 1 ships the version output, phases 2-5 the rest:

```python
def main(argv: list[str] | None = None, out=None, err=None,
         getenv=None) -> int: ...
    # argv=None → sys.argv[1:]; out=None → sys.stdout, err=None → sys.stderr,
    # both resolved inside the call (an import-time default would bypass capture)
```

1. `parse_args` → on `UnknownOptionError`: `ERROR: …` **and** `usage()` → `1`;
   on any other `FolderRemoveEmptyError`: `ERROR: …` → `1`;
2. `HELP` / `VERSION` / `MAN` / `TLDR` → print to stdout, return `0` (never
   read or write the settings file);
3. `options.no_gui` → `execute(options, TerminalReporter(...))`; a
   `FolderRemoveEmptyError` becomes `ERROR: …` + `1`;
4. otherwise `run_gui(options)` and return `0`.

While a step is still open, the entry point raises `NotImplementedError` with
the phase pointer instead of pretending to work.

`if __name__ == "__main__": raise SystemExit(main())`; `pyproject.toml` exposes
it as the console script `folder_remove_empty`.

## 7. Documentation and packaging deliverables

| File | Content |
|---|---|
| `pyproject.toml` | **done** — `[build-system]` setuptools (`requires = ["setuptools>=69"]`, `build-backend = "setuptools.build_meta"`), `name = "folder_remove_empty"`, `requires-python = ">=3.13"`, `dependencies = []`, `dynamic = ["version"]` + `[tool.setuptools.dynamic] version = {attr = "remove_empty_folder_version.__version__"}`, `[project.scripts] folder_remove_empty = "folder_remove_empty:main"`, MIT license, classifiers, `[project.urls]`, `[tool.setuptools] py-modules = [...]`, `[tool.pytest.ini_options]` (`testpaths`, `pythonpath = ["."]`), `[tool.ruff]` (line-length 100, `target-version = "py313"`), `[tool.ruff.lint]` (E, F, I, UP, B, SIM), `[tool.mypy]` (`python_version = "3.13"`, `files`, `ignore_missing_imports`), dev extra `pytest`/`ruff`/`mypy`/`nuitka` |
| `README.md` | what it does, requirements (Python 3.13+, `python3-tk` on Fedora/Debian), install (`pipx install .`, `make install`), the window guide, the terminal guide, the kept-folder list, the environment variables, the settings file, the exit codes, examples, the test command, links to man/tldr/ChangeLog/NEWS. No Gio, no cgo, no `cmd/`; the folder dialog is Tk's own (§2 decision) |
| `assets/folder_remove_empty.desktop` | `Type=Application`, `Name=FOLDER_REMOVE_EMPTY`, `Exec=folder_remove_empty`, `Icon=folder_remove_empty`, `Terminal=false`, `Categories=Utility;FileTools;` |
| `tldr/folder_remove_empty.page.md` | **generated and committed** by `make tldr` (`folder_remove_empty --print-tldr`); byte-identical to the captured Go page |
| `man/folder_remove_empty.1` | **generated and committed** by `make man` (`folder_remove_empty --print-man`); matches the captured Go page apart from the version stamp and the sentence naming this port |
| `assets/folder_remove_empty.desktop` | **done** — `Type=Application`, `Name=FOLDER_REMOVE_EMPTY`, `Exec=folder_remove_empty`, `Icon=folder_remove_empty`, `Terminal=false`, `Categories=Utility;FileTools;`, validated with `desktop-file-validate` when present |
| `ChangeLog.md` | per-version log, newest first, `## x.x.YYYYMMDDhhmmss - YYYY-MM-DD`, `### Added / Changed / Fixed / Removed` |
| `NEWS` | prose highlights per release: `* Version x.x.YYYYMMDDhhmmss (date)`, a bolded headline, an indented paragraph |
| `Makefile` | `help`, `test`, `run`, `man`, `tldr`, `icons`, `install`, `uninstall`, `clean`, `final`; `test` = `python3 -m pytest`, `python3 -m ruff check .`, `python3 -m mypy`; `final` = `test` + `man` + `tldr` + `_check_version` + `_skill_sync --check`; `install` puts the launcher in `~/sbin`, the icons into `~/.local/share/icons/hicolor/<size>x<size>/apps` and the `.desktop` into `~/.local/share/applications/`, with `desktop-file-validate` when present |
| `LICENSE` | unchanged (MIT) |

The first release entry documents the port itself: "rewritten in Python, the
Gio window is a tkinter window, the rules of the Go program are unchanged".

## 8. Test plan

`pytest` in `tests/folder_remove_empty/` (they are `unittest.TestCase`
classes, so `python3 -m unittest discover -s tests -t .` runs them as well).
`tests/testhelpers.py` provides `tmp_tree()` (builds a folder tree from a
dict), `capture()` (captures stdout/stderr), `remove_tree()` and the
`FakeObserver`.

The engine is split into its natural units, so the suite has 13 modules while
the source has 9 and the Go suite has 9 `*_test.go`.

| Test module | Covers |
|---|---|
| `test_version.py` | **done** — stamp format, banner shape, `__version__ == __VERSION__ - "Z"`, pyproject derives the version from the module, names |
| `test_reference.py` | **done** — `ReferenceFidelityTest` rebuilds the reference tree and compares `TerminalReporter`'s two streams with the colourless *and* the coloured pty captures; `MainFidelityTest` re-runs every recorded command through `main()` and asserts its streams and exit codes (four run cases, four refusals, `--version`, `--help`, `--print-man`, `--print-tldr`); skips for root |
| `test_core_scan.py` | **done** — a chain of nested empty folders in one `order`; a file blocks its folder; a symlink to a folder blocks its parent; an unreadable folder is not vacant; `root` is never in `order`; the order is children-first |
| `test_core_keep.py` | **done** — every fixed name, `ZZZZ`, four-digit dates, `!!! MISSING !!!` in any case, the extras, `keep-*` prefixes, `split_excludes` dropping empty pieces |
| `test_core_mark.py` | **done** — a kept folder stays; a kept folder goes with a removed parent; a kept folder stays when only kept folders hold the parent |
| `test_execute.py` | **done** — the phase order of spec §2.4; `current()` once per worked folder on the dry-run **and** the removal path; a dry run removes nothing but counts; a refused removal reports the reason and skips the parent; `checkpoint()` returning `False` ends the run with `stopped`; the exact observer call sequence |
| `test_run_control.py` |**done** —  pause blocks, resume releases, stop ends it, pause after stop is a no-op |
| `test_options.py` |**done** —  every option, both path errors, the environment pre-fill, the `usage()` shape |
| `test_report.py` |**done** —  the stdout/stderr split, every message shape, plain paths in a dry run, no colors off a tty, `NO_COLOR`, `<n> folder(s) kept` only with refusals |
| `test_docs.py` |**done** —  the man page sections are present; the tldr page has the backticked indented command per example; every command names the program and stays on one line |
| `test_config.py` |**done** —  a missing file yields the defaults; a round-trip keeps geometry and options; a malformed file yields the defaults instead of raising; an unwritable directory makes `save` fail quietly; the config pre-fill loses against a CLI option |
| `test_gui.py` |**done** —  builds the window, checks the widget order, the start-up values from `options`, the status line, the `Current folder` updates on a real removal, the `stopped` closing line, the history filter, the theme toggle, the pause/restart/exit labels, the drop of late updates, one `Button` per subfolder in the picker |

tkinter needs a window, and that window must never land on the screen the user is
working on (it steals the focus and flashes the whole desktop, user request
2026-09-27). The policy lives in `remove_empty_folder_display.py`;
`tests/folder_remove_empty/gui_display.py` wraps it for the suite and adds the
tkinter probe: `test_private_display.py` re-runs the two window modules under
`xvfb-run`, the window classes skip themselves in the parent run, and the private
run asserts that its display is not the session one. `test_script_display_policy.py`
extends the same rule to the repository scripts: a script that runs the program
must go through `xvfb-run` or the policy's `--check`, and the only session
openers are `_run`, `_menu`'s `r` entry and `make run` (which spells the program
as `$(PYTHON) -m $(APP)`, so the textual discovery does not see it).
`FOLDER_REMOVE_EMPTY_GUI_DISPLAY=session` opts into the session screen; without a
display and without `xvfb-run` the window tests skip.

## 9. Tasks

### Phase 1 — skeleton and packaging (done)

- [x] rewrite `pyproject.toml`: distribution `folder_remove_empty`, one console
      script, `py-modules`, dynamic version, pytest/ruff/mypy, dev extra,
      setuptools build system (the `_internal` backend is gone)
- [x] adapt the repository scripts to this project and delete `_docs` +
      `mkdocs.yml`: `_tests` (pytest/ruff/mypy), `_install` (`.[dev]`),
      `_menu`, `_run`, `_git` (UTC stamp, `-y`, `--message=`),
      `hooks/pre-commit` + `hooks/install.sh` (modules `version`, `skill_sync`,
      `ruff`, `mypy`, `tests`, `build`, `directory_hooks`)
- [x] `remove_empty_folder_version.py` with the `~/sbin/timestamp` stamp and
      the derived PEP 440 `__version__`
- [x] `folder_remove_empty.py` with `main()` that prints the version banner and
      raises `NotImplementedError` for the rest, so the package installs
- [x] `.gitignore`
- [x] `tests/folder_remove_empty/` with `__init__.py` files, `testhelpers.py`
      and `test_version.py`; pytest, ruff, mypy and
      `python3 -m unittest discover -s tests -t .` green; `./_tests` green;
      `pip install .` in a clean venv green
- [x] `_build` adapted to the single entry module (default `--jobs=1`,
      `--lto=no`, `--enable-plugin=tk-inter` so the frozen binary carries Tk,
      no `ddpico` program registry, no speech calls)
- [x] regenerate the `AGENTS.md` skill index with `./_skill_sync` and keep
      `./_skill_sync --check` green (the index was stale; the hook's
      `skill_sync` module is green again)
- [x] prune the ddpico-only skills: `dd-module-topics` and `ddtoolbox-fart`
      deleted, `tests-subfolder`, `skill_docstring_format`, `update-docs`,
      `update-pyproject`, `update-tests` retargeted to this project (15 skills
      left, `_skill_sync --check` green)
- [x] install the pre-commit hook (`bash hooks/install.sh`), so every commit
      runs `version`, `skill_sync`, `ruff`, `mypy` and `tests`
- [x] capture the Go reference (`tests/folder_remove_empty/reference/`:
      `cases.md`, `build_tree.sh`, 13 case triples) — the one fixed point the
      port can be diffed against

### Phase 2 — the engine (done)

- [x] `FolderRemoveEmptyError`, `Options`, `Action`, `Event.text()`, `Summary`
- [x] `resolve_start()` and its four error messages
- [x] `split_excludes()`, `excluded_name()`
- [x] `Scan` + `scan_tree()` (Lstat semantics, unreadable = not vacant)
- [x] `Scan.mark_deletes()` (single definition, no wrapper function)
- [x] the `Observer` ABC and `execute()` in the five phases, `current()` on
      both the dry-run and the removal path
- [x] `RunControl` on a `Condition`
- [x] the engine tests are green (`_tests` runs pytest + ruff + mypy): 47 tests
      in `test_core_scan.py`, `test_core_keep.py`, `test_core_mark.py`,
      `test_execute.py`, `test_run_control.py`
- [x] `Event.text()`'s refused-removal reason matches the Go wording
      (`remove <path>: <strerror>`, lowercase), so the terminal output can be
      compared line for line with the Go reference
- [x] the captured Go reference (`tests/folder_remove_empty/reference/`) is
      reproduced by `test_reference.py` byte for byte on all four run cases

### Phase 3 — command line and terminal front end (done)

- [x] `remove_empty_folder_options.py`: `Command`, `UnknownOptionError`,
      `new_options()`, `parse_args()`, `usage()` — `usage()` is byte-identical
      to the captured Go help text
- [x] `remove_empty_folder_report.py`: `TerminalReporter`, `color_code()` /
      `paint()`, tty and `NO_COLOR` handling, no `sys.stdout` default bound at
      definition time
- [x] `folder_remove_empty.py`: `main()`, `run_terminal()` and the exit codes
      of spec §5.5 (`run_window()` arrived with phase 5)
- [x] the options, report and reference tests are green (`test_options.py`,
      `test_report.py`; `main()` is pinned by `test_reference.py`'s
      `MainFidelityTest`, so no separate `test_run.py` is needed)
- [x] `test_reference.py` renders through `TerminalReporter` and `main()` and
      asserts the captured `.rc` exit codes as well: all four colourless run
      cases, all five coloured pty cases, the four refusals, `--version`,
      `--help`, `--print-tldr` byte-identical, `--print-man` identical apart
      from the two intended lines
- [x] a manual smoke run against a scratch tree, in both modes, compared with
      the Go binary line for line — the four run cases match byte for byte, and
      a real run removed the nested chain deepest first while the file holder
      and the kept names stayed (see `reference/cases.md`)

### Phase 4 — generated documentation (done)

- [x] `remove_empty_folder_docs.py`: `man_page()`, `tldr_page()`, the 8 examples
- [x] `--print-man` and `--print-tldr` produce the files — the tldr page is
      byte-identical to the captured Go page, the man page matches it line for
      line except the version stamp (the Python one carries the `Z`) and the
      sentence that names this port
- [x] `man/folder_remove_empty.1` and `tldr/folder_remove_empty.page.md`
      generated by `make man` / `make tldr` and committed
- [x] the doc tests are green (`test_docs.py`)

### Phase 5 — the tkinter window (done)

- [x] `remove_empty_folder_theme.py`: the two palettes, the importance colors,
      the button label
- [x] the window skeleton: title, 960×720, the icon, the nine rows, light theme
- [x] the start-up values from `options` for path, dry run, verbose, excludes
- [x] the path field, the live status line, `check_path()`
- [x] the dry run, verbose and extra excludes widgets (whitespace trimmed when
      a run starts)
- [x] the history filter radio group and the re-render
- [x] `GuiObserver` + queue + `_drain` + the run token (with a fake run, no
      thread yet), the `stopped` closing line included
- [x] the `Current folder` row follows every rated or removed folder
- [x] the worker thread, `RunControl`, pause/resume/restart/exit
- [x] `HelpDialog` over `usage()`
- [x] `filedialog.askdirectory` and the `FolderPicker` fallback (one button per
      subfolder)
- [x] the theme toggle repaints everything
- [x] `test_gui.py` is green (or skipped headless)

### Phase 6 — documentation and release (done)

- [x] prune or rewrite the ddpico-only skills in `.agents/skills/`
      (`dd-module-topics` and `ddtoolbox-fart` deleted, five skills retargeted);
      `./_skill_sync --check` green — **done early, in the phase 1 batch**
- [x] `README.md` reviewed for Python/tkinter, with the settings file and the
      Tk dialog deviation — written in the phase 1 batch, re-read against the
      finished program in phase 5
- [x] `ChangeLog.md` and `NEWS` with the port release — **written in the
      phase 1 batch** (entry `1.0.20260927131905`); extend with each phase
- [x] `Makefile` rewritten (`help`, `test`, `test-quick`, `run`, `man`,
      `tldr`, `icons`, `install`, `uninstall`, `clean`, `final`); `make final`
      is green except the phases 4/5 generators — **written in the phase 1
      batch**
- [x] `pip install .` in a clean venv, then `folder_remove_empty --help`
      (byte-identical to the Go capture), `--version` (prints the banner),
      `--print-tldr` (byte-identical) and `--print-man`
- [x] the installed binary checked against a scratch tree in both modes: the
      terminal run removed the nested chain deepest first and left the file
      holder and the kept names; the window run stayed open until the timeout
      killed it (exit 124), with no output on either stream
- [x] `make final` green (tests, man, tldr, `_check_version`, `_skill_sync
      --check`)
- [x] the version bumped with `~/sbin/timestamp` (`1.0.20260927131905Z`),
      `_check_version --all` green, a git commit, the `history-tracker` archive
      (prompts, changes, goal snapshot under `history/`)

### Phase 7 — persisted settings (done)

- [x] `project_specs.md` §12 describes the settings file (path, keys,
      precedence, write-on-close, never-abort)
- [x] `remove_empty_folder_config.py`: `SavedSettings`, `config_path()`,
      `load()`, `save()` — defaults on any bad input, atomic write, never raises
- [x] `pyproject.toml` `py-modules`/mypy coverage (all nine modules listed)
- [x] the window saves geometry, options and theme on close and restores them
      at start, with `options` winning over the file
- [x] `test_config.py` is green, plus the manual check: a window probe opened
      the real window, closed it and found the geometry, the options and the
      theme in the file

## 10. Resolved open questions (Q → decision)

**Q. Which distribution name?** → `folder_remove_empty` everywhere
(`pyproject.toml` `name`, the module names, the launcher, `make install`). The
earlier `folder-remove-empty` spelling is dropped; setuptools normalizes the
distribution name for the wheel anyway.

**Q. Rewrite the ddpico/Go copies of `pyproject.toml`, `README.md`,
`ChangeLog.md`, `NEWS`, `Makefile` in place?** → Yes, in place. Every ddpico
console script and every ddpico `[tool.*]` section goes away. `pyproject.toml`
is done (phase 1); `README.md`, `ChangeLog.md`, `NEWS` and the `Makefile`
follow in phase 6.

**Q. Keep a literal `version` in `pyproject.toml` or derive it?** → Derive it.
A literal cannot satisfy both demands: `_check_version` requires the repository
stamp `x.y.<14 digits>Z`, and setuptools rejects that string — verified,
`packaging.version.InvalidVersion: Invalid version: '1.0.20260927111114Z'`.
So the module holds `__VERSION__` (with the `Z`) plus the derived
`__version__` (PEP 440, without it) and `pyproject.toml` reads the latter
through `[tool.setuptools.dynamic]`. `pip install .` in a clean venv installs
`folder_remove_empty-1.0.20260927111114`, the console script prints the
banner, and `test_version.py` pins the pair.

**Q. Python floor: 3.10 or 3.13?** → `>=3.13`. The floor now matches the build
toolchain (`nuitka` supports only 3.13), and `dataclasses(slots=True)` plus
`X | None` need no older floor anyway. ruff targets `py313`, the classifiers
name 3.13, `mypy` pins `python_version = "3.13"`.

**Q. Where does the man page live?** → `man/folder_remove_empty.1`, generated
by `--print-man` (the Go tree's location).

**Q. The `_build`, `_install`, `_tests`, `_run`, `_docs`, `_git`, `_menu`,
`_check_version` scripts were copied from ddpico and assume its layout — reuse
or write our own?** → Keep and adapt them; only `_docs` is deleted. `_tests`
runs pytest + ruff + mypy of this project (three steps, `--quick` for tests
only), `_build` builds the single entry module with one compiler job, `_install`
installs `.[dev]` and verifies the version module, `_menu`/`_run` target
`python3 -m folder_remove_empty`, `_git` uses the UTC stamp and gains `-y`,
`_check_version`/`_skill_sync` stay untouched. Details per script in §3.

**Q. Add a `.desktop` file?** → Yes: `assets/folder_remove_empty.desktop`,
installed into `~/.local/share/applications/` and validated with
`desktop-file-validate` when available.

**Q. Keep the MkDocs documentation site?** → No. `_docs` and `mkdocs.yml` are
deleted; the man page, the tldr page and `README.md` carry the documentation,
and `assets/folder-remove-icon.svg` stays as the vector original of the icon
set.

**Q. Where do the window geometry and the program settings live?** → §5.8:
`~/.config/folder_remove_empty/folder_remove_empty.conf`, INI through
`configparser`, written by the window on close, read as the lowest-precedence
pre-fill.

**Q. What happens to the ddpico-only skills in `.agents/skills/`?** → they are
pruned now, not in phase 6: `dd-module-topics` (a file per callable under
`ddpico/`) and `ddtoolbox-fart` are deleted, and `tests-subfolder`,
`skill_docstring_format`, `update-docs`, `update-pyproject`, `update-tests` are
retargeted to this project's flat modules, `tests/folder_remove_empty/` subtree
and Makefile targets — 15 skills left, `./_skill_sync --check` green. A rule
marked `always` that contradicts the code layout is worse than no rule.

**Q. How is the port proven to behave like the Go program?** → the Go binary
was built once (single compiler job, `go build -p 1 ./cmd/folder_remove_empty`)
and its output captured into `tests/folder_remove_empty/reference/`: 13 cases
with stdout, stderr and exit status, plus `cases.md` documenting the tree shape
and a committed `build_tree.sh`. `test_reference.py` rebuilds that tree, runs
the engine over it and compares both streams byte for byte — all four run cases
match, and every stdout stream matched on the first run. The only initial
difference was the reason text of the one refused removal; the engine was
aligned to the Go shape (`remove <path>: <strerror>`) because
`project_specs.md` §4 leaves the wording open and byte fidelity is the point of
the exercise. The `.rc` codes are asserted once `main()` exists (phase 3).

**Q. How was the finished program verified?** → every layer against a fixed
point, not against its own assumptions: `./_tests` (142 tests, 107 subtests),
`test_reference.py` comparing `TerminalReporter` and `main()` with the Go
captures byte for byte and exit code for exit code, a real terminal run that
removed a nested chain deepest first while the file holder and the kept names
stayed, a `pip install .` into a clean venv whose console script reproduced the
captured `--help`/`--print-tldr` byte for byte, a window probe that opened the
real window, read the nine rows, drove a scripted run through the observer and
the queue, toggled the theme and found the settings written on close, and a
window launch through the installed script that stayed open until the timeout
killed it (exit 124, both streams empty).

**Q. Is the pre-commit hook installed?** → yes, `bash hooks/install.sh` was run,
so every commit here runs `version`, `skill_sync`, `ruff`, `mypy` and `tests`
through `./_tests --quick`.

## 11. Distribution and upkeep (done)

Beyond the phases, the port is wired into the desktop and the release path:

- `_build` builds the standalone binary (Nuitka, one compiler job, `--lto=no`,
  `--enable-plugin=tk-inter`, 14 MB onefile) and writes `build/SHA256SUMS` and
  `build/release_manifest.json` next to it; `--release` tags and publishes
  through `gh`.
- `make install` puts a launcher in `~/sbin`, the eight icon sizes into
  `~/.local/share/icons/hicolor/<size>x<size>/apps/` and
  `assets/folder_remove_empty.desktop` into `~/.local/share/applications/`.
  The entry was launched from the menu: the window came up, `gtk-launch` and
  `gio launch` both resolved `Exec=folder_remove_empty` through `~/sbin`.
- the pre-commit hook gained a `docs` module that fails when the committed
  `man/` or `tldr/` page drifts from the generator — it caught the stale version
  stamp in the man page the first time it ran, which is the point.
- a fourth fidelity group, `reference/gui_window.txt`, dumps the window's widget
  tree row by row (class, text, values, states) and is compared by
  `test_gui_reference.py`; pixel geometry and fonts are left out on purpose.

Upkeep that stays open by nature: extend `ChangeLog.md` and `NEWS` with every
change, re-run `make final` before a commit, and re-stamp `__VERSION__` (and
then `make man`) whenever the version changes, because the man page embeds it.

### The verified environment (added 2026-09-27 with v1.2)

- `.github/workflows/checks.yml` runs the suite, ruff and mypy on Python 3.13
  (`python3-tk` and `xvfb` installed) on every push, pull request and manual
  dispatch; `checks` is a required status context on `master` and the README
  carries the badge. The first run failed and found a real portability bug
  (`tk.Event[tk.Entry]` evaluated at import — 3.14 only), which is the point.
- `requirements-dev.txt` pins the four dev tools exactly and CI installs it plus
  the package, so the checked environment is reproducible. `_check_pins` prints
  the drift between the pins and the working interpreter; the pre-commit `pins`
  module runs it as a reminder and never blocks a commit.
- `make check-313` repeats `make final` and `make check-gui` inside
  `python:3.13-slim` with the repository mounted read-only; a leftover diff from
  the regenerated pages fails it, so the container cannot rewrite the tree.
- `make check-gui` is the hand-run window check on a private display, and
  `docs/window-display.md` is the long form of the display policy.

### Release checklist (repeatable)

The sequence below is the one `v1.3.20260927191420Z` was cut in. Every step
runs from the repository root and is meant to be copy-pasteable as written.

1. `./make final` — the whole pre-commit check in one target: `_tests`
   (pytest, ruff, mypy), `make man` and `make tldr` (both pages regenerated
   from the program itself) and the `_check_version` / `_skill_sync --check`
   validators. `./_check_pins --strict` says whether the working interpreter
   matches the pins, and `make check-313` (podman, read-only mount) repeats the
   whole check on Python 3.13, the interpreter CI uses.
2. `make man` and `make tldr` again after any `__VERSION__` re-stamp: the man
   page embeds the stamp in its `.TH` line, so a bump that lands after step 1
   leaves the committed page stale.
3. `./_build --package` — the Nuitka build (one compiler job unless `--jobs`
   says otherwise) writes `build/folder_remove_empty`, `build/SHA256SUMS` and
   `build/release_manifest.json`.
4. Verify the three artifacts: `cd build && sha256sum -c SHA256SUMS` (every
   line must read `OK`, then `cd ..`), read
   `build/release_manifest.json` against the binary, and run
   `./build/folder_remove_empty --version` and
   `./build/folder_remove_empty --help` to see the packaged front ends come
   up.
5. `git add -A && git commit` — the installed pre-commit hook must pass; it
   is the gate that keeps pages, version strings and the build honest.
6. `git push origin master`.
7. Tag and push the tag:
   `git tag -a "v$VERSION" -m "Release v$VERSION" && git push origin "v$VERSION"`.
8. `make screenshots` and commit the regenerated `assets/window-*.png` when the
   window changed; the script is reproducible, so an unchanged window means
   unchanged bytes.
9. Publish the release with its three assets: `gh release create "v$VERSION" \
   build/folder_remove_empty build/SHA256SUMS build/release_manifest.json \
   --title "v$VERSION" --notes "<what changed>"`. `./_build --release` folds
   steps 7 to 9 into the build step.
10. `gh release view "v$VERSION"` — confirm the binary, `SHA256SUMS` and
    `release_manifest.json` are all attached before calling it done.

Two traps bit us and are worth repeating: a version re-stamp leaves the
committed man page stale until `make man` runs again, and the hook's `docs`
module blocks the commit until it does; and `_build` installs the standalone
binary over `~/sbin/folder_remove_empty`, so re-run `make install` when the
launcher there is wanted again.
