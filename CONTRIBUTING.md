# Contributing

`folder_remove_empty` removes every empty folder below a start folder, deepest
first, from a tkinter window (default) or the terminal (`--no-gui`).

- the behaviour contract is `project_specs.md` — it wins over every
  implementation detail;
- the plan, the phases and the release checklist are in `todo/goal.md`;
- the reference behaviour of the original Go program (its captured output) is in
  `tests/folder_remove_empty/reference/`.

## Setting up

```bash
sudo dnf install python3-tk            # or: sudo apt install python3-tk
python3 -m venv .venv && . .venv/bin/activate
python3 -m pip install -e '.[dev]'     # pytest, ruff, mypy, nuitka
bash hooks/install.sh                  # the pre-commit hook
```

The modules are flat files in the project root (`folder_remove_empty.py` and
`remove_empty_folder_*.py`), the tests live in `tests/folder_remove_empty/` as
`unittest.TestCase` classes and run under pytest. `xvfb-run` and `Xvfb` are
recommended: the window tests always open the window on a private display, so
they never flash the screen you are working on.

## Running the checks

```bash
./_tests                 # pytest + ruff + mypy, the same sequence the hook runs
./_tests --quick         # the test suite alone
python3 -m pytest        # the suite directly
python3 -m ruff check .  # lint (line length 100, target py313)
python3 -m mypy          # types
make final               # checks plus the generated man/tldr pages and the version check
```

The pre-commit hook (`hooks/pre-commit`, installed into `.git/hooks/`) runs the
modules `version`, `skill_sync`, `ruff`, `mypy`, `tests`, `gui`, `docs`,
`build` (gated) and `directory_hooks`. Two of them have requirements worth
knowing:

- **`gui`** opens the window and checks its structure and that no widget is
  filled with the palette accent (a purple checkbutton or radio indicator was
  rejected). The window is opened on a **private Xvfb display** — never on the
  screen you are working on, because that steals the focus and flashes the whole
  desktop. `FOLDER_REMOVE_EMPTY_GUI_DISPLAY=session` asks for the session screen
  instead, `SKIP_GUI=1` bypasses the module, and without a display and without
  `xvfb-run` it skips.
- **`docs`** regenerates the man page and the tldr page and compares them with
  the committed files, so a stale page fails the commit. The man page embeds
  `__VERSION__`: after re-stamping the version, run `make man` and `make tldr`.

Every module can be skipped with `SKIP_<MODULE>=1`, all of them with
`SKIP_HOOKS=1`.

## Conventions

- **Docstrings**: every function, class and method carries the repository format
  — a what-and-when first line, `usage:`, `returns:`, one blank line, `example:`
  (`.agents/skills/skill_docstring_format/SKILL.md`).
- **Versions**: `remove_empty_folder_version.__VERSION__` is the only version
  literal (`Major.Minor.<14-digit UTC>Z` from `~/sbin/timestamp`, with the `Z`);
  `__version__` derives the PEP 440 form setuptools needs. `./_check_version`
  validates the format and refuses a modified file whose version did not move.
- **Commits**: the message is the bare 14-digit UTC timestamp
  (`~/sbin/timestamp`), nothing else.
- **Line endings**: LF only. **Language**: English in code, comments and docs.
- **Tests**: a new behaviour goes to `tests/folder_remove_empty/`, one
  `test_<unit>.py` per unit; the reference captures must stay green, because
  they are what proves the port still behaves like the original.
- **Windows and automation**: any script, test or check that opens the window
  must do it on a private display (`xvfb-run`), never on the session screen —
  see *Window tests and your screen* in `README.md` and `docs/window-display.md`.
  Only `make run`, `_run` and the installed launcher are meant to open the real
  window, and the suite fails when a new script breaks that rule.
- **Builds**: one compiler job at a time (`./_build` defaults to `--jobs=1`
  `--lto=no`, under `nice`/`ionice`); never raise it without being asked, and
  never run two heavy builds at once.

## Releasing

Follow `### Release checklist (repeatable)` in `todo/goal.md` §11: `make final`,
re-stamp and regenerate the pages, `./_build --package`, verify
`build/SHA256SUMS`, commit (the hook must pass), push, tag `v$VERSION`, then
`gh release create` with the binary, the checksums and the manifest.

## Reporting

Bugs and feature requests use the forms under `.github/ISSUE_TEMPLATE/`;
security reports go through a private advisory, see `SECURITY.md`.
