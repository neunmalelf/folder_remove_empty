# Change log

All notable changes to this project are documented in this file, newest first.
A version is the UTC timestamp of its change, `x.x.YYYYMMDDhhmmss`, the output of
`~/sbin/timestamp`. The user-facing highlights per release, in prose, are in
`NEWS`.

## 1.0.20260927131905 - 2026-09-27

### Added

- The setuptools packaging of the Python port: distribution
  `folder_remove_empty`, a single console script
  (`folder_remove_empty = folder_remove_empty:main`), `py-modules`, the pytest
  and tool configuration, and the dev extra. The `[build-system]` now points at
  `setuptools.build_meta`, so `pip install .` works again.
- `remove_empty_folder_version.py`: `__VERSION__` holds the repository stamp
  (the UTC timestamp with the trailing `Z`) once, and the derived PEP 440
  `__version__` is what the packaging layer reads through
  `[tool.setuptools.dynamic]`, because setuptools refuses the stamped form.
- `folder_remove_empty.py`: the entry point of the program. This first release
  answers `--version` with the version banner; the rest of the command line
  follows in its phases.
- `.gitignore` for the Python build and cache output.
- `tests/folder_remove_empty/`: the test skeleton with the `__init__.py`
  packages, `testhelpers.py` and `test_version.py`, runnable by pytest and by
  `python3 -m unittest discover`.
- The repository scripts adapted to this project: `_tests` (pytest, ruff,
  mypy), `_build`, `_install`, `_menu`, `_run`, `_git` and `hooks/pre-commit`
  now call this project's commands and paths.

### Changed

- `_tests` is the check runner of this project: pytest on
  `tests/folder_remove_empty`, then `python3 -m ruff check .` and
  `python3 -m mypy`, with `--quick` for the test suite alone.
- `hooks/pre-commit` runs the modules `version`, `skill_sync`, `ruff`, `mypy`,
  `tests`, `build` and `directory_hooks` with this project's commands.

### Removed

- `_docs` and `mkdocs.yml`: the documentation site is dropped, the man page, the
  tldr page and `README.md` carry the documentation.
- The console scripts and the `[tool.*]` sections the `pyproject.toml` had
  inherited from the ddpico template skeleton; the `_internal` build backend is
  gone with them.
