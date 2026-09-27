---
name: tests-subfolder
version: 1.6.20260927131905Z
description: >
  Guarantees that all test modules for this project live in the
  tests/folder_remove_empty/ subfolder (the folder_remove_empty namespace unit)
  and never in the project root.
---

# Tests-subfolder skill

## Rule

All test files and test suites for this project MUST live in the `tests/` tree,
organized one subdirectory per namespace unit. This project has exactly one
namespace unit - the flat module set `folder_remove_empty.py` plus
`remove_empty_folder_*.py` - so the authoritative test directory is
`tests/folder_remove_empty/`. Never place test modules in the project root.

authoritative test directory:
- `tests/folder_remove_empty/`: the version module, the option parser, the scan
  and removal core, the report, the man/tldr generators, the configuration, the
  terminal run control, and the tkinter window.

structure:
- `tests/__init__.py` and `tests/folder_remove_empty/__init__.py` keep both
  directories importable, so `python3 -m unittest discover -s tests -t .` finds
  every module.
- one test module per unit, named `test_<unit>.py` (`test_version.py`,
  `test_core.py`, `test_options.py`, ...), each holding `unittest.TestCase`
  classes.
- shared helpers (temporary-directory mixin, fixture builders) live in
  `tests/folder_remove_empty/testhelpers.py`.

## When to apply

- When you write a new test file or test suite.
- When you add a module to the project.
- When you update or relocate existing tests.

## Conventions for test modules

1. Place Python test modules in `tests/folder_remove_empty/test_<unit>.py`.
2. Test cases inherit from `unittest.TestCase` (or from a base class in
   `testhelpers.py`); pytest collects `unittest.TestCase` subclasses, so the
   same modules run under both runners.
3. Both module runners MUST stay green:
   ```bash
   python3 -m pytest
   python3 -m unittest discover -s tests -t .
   ```
4. The project runner wraps the suite and the static checks, and MUST stay
   green too:
   ```bash
   ./_tests            # pytest + ruff + mypy
   ./_tests --quick    # the test suite only
   ```
5. A test module outside `tests/` does not run: `testpaths = ["tests"]` in
   `pyproject.toml` keeps bare pytest inside the tree, and unittest discovery
   starts at `tests/`. Never add one in the project root.

## Verification checklist

- [ ] Test module lives in `tests/folder_remove_empty/`.
- [ ] `python3 -m pytest` runs green.
- [ ] `python3 -m unittest discover -s tests -t .` runs green.
- [ ] `./_tests --quick` runs green.
