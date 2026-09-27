---
name: update-tests
version: 1.1.20260927131905Z
description: Perform a thorough test coverage audit across the entire codebase and output recommendations to tests_suggestions.md without modifying source or test code.
load: always
---

# update-tests

## Overview

Perform a thorough test coverage audit across the whole codebase and write
comprehensive recommendations to `tests_suggestions.md` — never to the source or
the tests.

## When to use

When a coverage audit is asked for, after a bigger feature lands, or before a
release, to see which modules and behaviours still lack tests.

## Audit Requirements

1. **Scope:** inspect every top-level module of the project
   (`folder_remove_empty.py` and `remove_empty_folder_*.py`) — every class,
   dataclass, enum, function, and method in them.
2. **Cross-reference** each component against the test tree under
   `tests/folder_remove_empty/` (`test_<unit>.py` modules, shared helpers in
   `testhelpers.py`).
3. **Evaluate** completeness: uncovered callables, missing edge cases, boundary
   values, and failure states.
4. **Units to cover** — one test module per unit, `unittest.TestCase` style:

   | Unit | Test module |
   |---|---|
   | version (`__VERSION__`, `__version__`, `APP_NAME`, `version_banner()`) | `test_version.py` |
   | core scan / keep / mark | `test_core.py` |
   | execute (deepest-first removal) | `test_execute.py` |
   | run control (pause / start / stop) | `test_run_control.py` |
   | options (parser and `usage()`) | `test_options.py` |
   | report | `test_report.py` |
   | docs (man page and tldr page generation) | `test_docs.py` |
   | config | `test_config.py` |
   | run (terminal front end) | `test_run.py` |
   | gui (tkinter window) | `test_gui.py` |

5. **Runners** — every suggestion names how it is exercised: `./_tests`,
   `./_tests --quick`, `python3 -m pytest`, `python3 -m unittest discover -s
   tests -t .`, or one module with
   `python3 -m pytest tests/folder_remove_empty/test_<unit>.py`.

## Report

Create `tests_suggestions.md` containing:

- **Missing Tests:** callables or behaviours with zero or inadequate coverage.
- **Test Improvements:** existing tests that need expanded assertions or edge
  cases.
- **Proposed Test Cases:** concrete new scenarios (input, expected output,
  failure path).

## Execution Constraints

- **Planning mode only:** write *only* to `tests_suggestions.md`.
- **No implementation:** never modify source code, never edit or create test
  modules; that happens only after review.
- **Notification:** tell the user when `tests_suggestions.md` is complete and
  wait for instructions.
