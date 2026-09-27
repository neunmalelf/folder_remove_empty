# Change log

All notable changes to this project are documented in this file, newest first.
A version is the UTC timestamp of its change, `x.x.YYYYMMDDhhmmss`, the output of
`~/sbin/timestamp`. The user-facing highlights per release, in prose, are in
`NEWS`.

## 1.6.20260927202851 - 2026-09-27

### Added

- `make check-all`: the pre-push set in one command (`final`, `check-gui`,
  `check-313`).
- `tests/folder_remove_empty/window_checks.sh`: the one place that lists the
  window test modules, used by `make check-gui`, by the policy wrapper and by the
  display guard's private re-run. `--assert-private` refuses a session display,
  `--list` prints the modules.
- `docs/checks.md`: every check target, script and hook module, the environment
  variables that skip them, and what to do when one fails.

### Changed

- `make check-gui` is one line: `--wrap-sh` runs `window_checks.sh
  --assert-private`, so neither the Makefile nor the hook names a test module.
- the window tests close the window the way the program does (`_close_window`),
  stopping a run in flight and cancelling the pending `after` callbacks before
  the root goes away. Collecting a tkinter `Variable` after Tcl is gone used to
  report "Exception ignored ... main thread is not in main loop" on most runs;
  four consecutive private runs are clean now, and the teardown exercises the
  real close path.
- `gui_display.py` lost the re-exports nothing reads (`XVFB_RUN`,
  `SESSION_WANTED`, `POLICY`, `PRIVATE_MARKER`, `DISPLAY_MARKER`, `REFUSAL`,
  `NO_WINDOW`, `window_refusal`); the policy module is the one public home, and
  `test_script_display_policy.py` now also watches `window_checks.sh`.

## 1.5.20260927201516 - 2026-09-27

### Added

- `python3 -m remove_empty_folder_display --wrap-sh SNIPPET` runs a snippet
  through `sh -c` on a private display, which is the form for a pipeline.
- `./_check_pins --update` rewrites `requirements-dev.txt` to the versions that
  are installed (comment header and order stay), so a verified environment can be
  pinned in one step; `--strict` still fails a drifted one.

### Changed

- `make check-gui`, `make check-313` and `assets/make_screenshots.sh` go through
  `--wrap`, so the xvfb flags live in `remove_empty_folder_display.py` only.
- `make check-gui` honours `FOLDER_REMOVE_EMPTY_GUI_DISPLAY=session` (the policy
  module decides; the Makefile no longer hard-codes `xvfb-run`), and the
  pre-commit `gui` module lost its own display branch: it calls the target.
- the private run now records the session display, so the assertion that the
  window never went there really runs (`make check-gui`: 39 passed, 1 skipped
  instead of 38 and 2).
- `assets/make_screenshots.sh` refuses any display that is not private, because
  a capture needs a clean desktop; the window geometry of the private server is
  the policy module's.
- corrected a wrong note from 1.4: `xvfb-run` does **not** re-split the command
  it is given. Arguments, quotes, spaces and stdin survive the wrapper (verified
  with an inline program, a quoted argument list, a pipeline and a heredoc); the
  suite pins the inline and pipeline forms.

## 1.4.20260927194352 - 2026-09-27

### Added

- `python3 -m remove_empty_folder_display --wrap CMD...` runs a command on a
  private display (xvfb-run, the markers, its exit status) and
  `--wrap --print CMD...` prints that command line; a shell script no longer has
  to spell the xvfb invocation itself.
- `make pins` (`./_check_pins --strict`) and `make final` now runs it, so a
  release cannot be cut in an environment that drifts from the pins CI installs.

### Changed

- the pre-commit `gui` module delegates to `make check-gui` instead of driving
  the guard test itself, so a commit and the manual target check the same thing;
  with `FOLDER_REMOVE_EMPTY_GUI_DISPLAY=session` it runs the three window modules
  on the session display (before, that mode checked nothing).
- `CONTRIBUTING.md` and the workflow explain why `make check-313` stays a local
  target: CI runs natively on the same 3.13, so a nested container in a job would
  only test the same interpreter twice.
- `docs/window-display.md` documents `--wrap` and the trap that `xvfb-run`
  re-splits the command string, so an inline `python3 -c "..."` loses its
  quoting — pass a script file.

## 1.3.20260927191420 - 2026-09-27

### Added

- `remove_empty_folder_display.py`: the one private-display contract every piece
  of automation speaks (the window tests, `make check-gui`, `make check-313`,
  the pre-commit `gui` module and `assets/make_screenshots.sh`), with
  `python3 -m remove_empty_folder_display --check|--print` for shell scripts.
- `tests/folder_remove_empty/test_script_display_policy.py`: fails the suite when
  a repository script runs the program without `xvfb-run` or the policy check;
  the only session openers are `_run`, `_menu`'s `r` entry and `make run`.
- `make check-gui`: the window checks on a private display by hand.
- `make check-313`: `make final` plus `make check-gui` on Python 3.13 in a
  `python:3.13-slim` container, repository mounted read-only and copied inside,
  a leftover diff failing the target.
- `_check_pins` and the warn-only pre-commit module `pins`: report dev tools that
  drift from `requirements-dev.txt` (what CI installs).
- `docs/window-display.md`: the long form of the display policy, linked from
  `README.md` and `CONTRIBUTING.md`.
- `.github/workflows/checks.yml` with the `checks` badge in the README, and
  `checks` is a required status context on `master`.

### Changed

- CI installs `requirements-dev.txt` plus the package instead of the unpinned
  `.[dev]` extra, so the checked environment is the pinned one.
- `assets/make_screenshots.sh` refuses to run outside a private display.
- the earlier notes for this batch (badge, required context, pinned CI install,
  `make check-gui`, the README display section) are backfilled here; they were
  committed after 1.2 was cut.

## 1.2.20260927181430 - 2026-09-27

### Added

- Continuous integration (`.github/workflows/checks.yml`): pytest, ruff and mypy
  on Python 3.13 with `python3-tk` and `xvfb`, on every push and pull request.
- `requirements-dev.txt` pins the tool versions this release was verified with.
- the README gained a link section and a note that the window images come from
  `make screenshots`.

### Fixed

- The window module could not be imported on Python 3.13, the floor this project
  declares: the annotations `tk.Event[tk.Entry]` and `tk.Event[tk.Frame]` are
  evaluated at import time and tkinter's `Event` only became subscriptable in
  3.14, so collection died with `TypeError: type 'Event' is not subscriptable`.
  The module now imports its annotations lazily (`from __future__ import
  annotations`), which keeps the precise types. The new CI found this on its
  first run; the local interpreter is 3.14 and never noticed.

## 1.1.20260927180137 - 2026-09-27

### Added — since the 1.0 cut

- `assets/make_screenshots.sh` and the `make screenshots` target: both window
  screenshots are drawn on a private Xvfb display from a fixed scratch root, so
  the committed PNGs are reproducible.
- `CONTRIBUTING.md`: the working setup, the check commands, the pre-commit
  modules and their requirements, the conventions, the release pointer.
- a `gui` module in the pre-commit hook: it opens the window (session display or
  `xvfb-run`) and fails when the structure drifts or a widget is filled with the
  palette accent.
- `SECURITY.md` and the issue templates under `.github/ISSUE_TEMPLATE/`.
- branch protection on `master` (force pushes and deletions disabled).

### Fixed

- the README drift: the option aliases (`-d`/`--dryrun`/`--dry-run`,
  `-v`/`--verbose`) and the window's `would remove:` line are documented; no
  option of `usage()` is missing any more.

### The port, phase by phase

The plan is `todo/goal.md`, the behaviour contract `project_specs.md`.

### Added — phase 1, packaging and tooling

- The setuptools packaging: distribution `folder_remove_empty`, one console
  script, `py-modules`, the pytest and tool configuration and the dev extra.
  The `[build-system]` points at `setuptools.build_meta`, so `pip install .`
  works again.
- `remove_empty_folder_version.py`: `__VERSION__` holds the repository stamp
  (the UTC timestamp with the trailing `Z`) once, and the derived PEP 440
  `__version__` is what the packaging layer reads through
  `[tool.setuptools.dynamic]`, because setuptools refuses the stamped form.
- `.gitignore` for the Python build and cache output.
- The repository scripts adapted to this project: `_tests` (pytest, ruff,
  mypy), `_build` (Nuitka, one compiler job, `--enable-plugin=tk-inter`),
  `_install`, `_menu`, `_run`, `_git` (UTC stamp, `-y`, `--message=`) and
  `hooks/pre-commit`.

### Added — phase 2, the engine

- `remove_empty_folder_core.py`: `Options`, `Action`, `Event`, `Summary`,
  `Observer`, `resolve_start()`, `scan_tree()`, `split_excludes()`,
  `excluded_name()`, `Scan.mark_deletes()`, `execute()` and `RunControl` on a
  condition — the shared engine both front ends watch.
- The captured reference behaviour of the original Go program
  (`tests/folder_remove_empty/reference/`): 13 colourless cases, later six
  coloured pty cases, `cases.md` and the tree builder; the refused-removal
  reason follows the Go wording so the comparison can be byte for byte.

### Added — phase 3, command line and terminal front end

- `remove_empty_folder_options.py`: `Command`, `UnknownOptionError`,
  `new_options()`, `parse_args()` and the `usage()` text, which is
  byte-identical to the original help text.
- `remove_empty_folder_report.py`: `TerminalReporter`, the ANSI colours,
  `paint()` and the tty/`NO_COLOR` handling; removed folders on stdout,
  everything else on stderr, plain paths in a dry run.
- `folder_remove_empty.py`: `main()`, `run_terminal()` and the exit codes of
  the original.

### Added — phase 4, generated documentation

- `remove_empty_folder_docs.py`: `man_page()` and `tldr_page()` with the eight
  examples; `man/folder_remove_empty.1` and `tldr/folder_remove_empty.page.md`
  are generated by `make man` / `make tldr` and committed. The tldr page is
  byte-identical to the original, the man page matches it apart from the version
  stamp and the sentence that names this port.

### Added — phase 5, the window

- `remove_empty_folder_theme.py`: the light and dark palettes, the importance
  colours and the theme button label.
- `remove_empty_folder_gui.py`: the tkinter window of spec §7 — the nine rows,
  the live status line, dry run and verbose, the extra kept names, the history
  filters, pause, restart, exit, the help dialog, the built-in folder picker
  (one button per subfolder) and the theme switch, driven by a queue from a
  worker thread with a per-run generation token.

### Added — phase 6, release plumbing

- `Makefile` with `help`, `test`, `test-quick`, `run`, `man`, `tldr`, `icons`,
  `install`, `uninstall`, `clean` and `final`.
- `assets/folder_remove_empty.desktop`, installed by `make install` together
  with the launcher script and the eight icon sizes.
- `README.md` (requirements, install, the window and terminal guides, the kept
  names, the environment, the settings file, the exit codes) and this changelog
  with `NEWS`.

### Added — phase 7, persisted settings

- `remove_empty_folder_config.py`: the settings file, INI through
  `configparser`, written by the window on close and read as the
  lowest-precedence pre-fill; `project_specs.md` §12 documents it.

### Added — tests

- `tests/folder_remove_empty/`: 13 test modules (142 tests, 107 subtests),
  including the reference fidelity groups — the four colourless run cases, the
  five coloured pty cases, the four refusals and the informational outputs
  through `main()`, all compared byte for byte and exit code for exit code —
  and the structural capture of the window.

### Fixed

- The window paints no purple fill any more (user request 2026-09-27): the
  checkbutton and radio indicator boxes and the selection of a field take the
  theme background and the border grey instead of the accent, and only a button
  still gets a hover tint, in the border grey. `test_gui.py` and the structural
  window capture assert that no widget is filled with the accent.

### Changed

- `_tests` is the check runner of this project: pytest on
  `tests/folder_remove_empty`, then `python3 -m ruff check .` and
  `python3 -m mypy`, with `--quick` for the test suite alone.
- `hooks/pre-commit` runs the modules `version`, `skill_sync`, `ruff`, `mypy`,
  `tests`, `build` and `directory_hooks` with this project's commands.
- `AGENTS.md`'s generated skill index and the skill tree are this project's: the
  two ddpico architecture skills are gone and five skills were retargeted.

### Removed

- `_docs` and `mkdocs.yml`: the documentation site is dropped, the man page, the
  tldr page and `README.md` carry the documentation.
- The console scripts and the `[tool.*]` sections the `pyproject.toml` had
  inherited from the ddpico template skeleton; the `_internal` build backend is
  gone with them.
