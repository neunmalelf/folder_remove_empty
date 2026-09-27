---
name: tests-subfolder
version: 1.5.20260911231450Z
description: >
  Guarantees that all test scripts and test modules for this project live in the
  appropriate tests/ subfolder: tests/<standalone_program>/ for every program in
  ddpico.programs, or tests/dd<topic>/ for topic-module tests (dd-prefixed,
  matching the ddpico module, e.g. tests/ddfiles/ for ddpico/files.py).
---

# Tests-subfolder skill

## Rule

All test files and test suites for this project MUST live in the `tests/` tree,
organized one subdirectory per namespace unit: `tests/<standalone_program>/` for
every program registered in `ddpico.programs`, or `tests/dd<topic>/` for
topic-module tests (named after the `ddpico/<topic>.py` module, e.g.
`tests/ddfiles/` for `ddpico/files.py`). Every `tests/` subdirectory therefore
maps 1:1 to a program or a module. Never place test modules in the project root.

authoritative test directories:
- `tests/ddpico/`: Core ddpico functions, REPL, crawler, programs registry
- `tests/ddfiles/`: File manipulation, copy/move/rename operations, and path resolution tests (topic module `ddpico/files.py`)
- `tests/ddfart/`: Find and Replace Text (ddfart / pyfart) tests, match, walk, rulefile, pdf/ebook
- `tests/ddbusybox/`: Multi-call BusyBox dispatcher and applet tests
- `tests/ddbak/`: Directory backup utility tests
- `tests/ddmediadownloader/`: Media downloader tests
- `tests/ddpico_lsp/`: Language Server Protocol tests
- `tests/ddznumber/`: Base-26 bijective numeration standalone program tests
- `tests/ddcrawl/`: Directory crawler standalone program tests
- `tests/ddversion_get_from_filepath/`: Version extractor standalone program tests
- `tests/ddtts/`: Kokoro TTS file-synthesis standalone program tests

## When to apply

- When you write a new test file or test suite.
- When you add a new standalone program to `ddpico.programs`.
- When you update or relocate existing tests.

## Conventions for test scripts and modules

1. Place Python test modules in `tests/<standalone_program>/test_<name>.py`.
2. Ensure test cases inherit from `unittest.TestCase` or `testutil.TmpDirTestCase`.
3. Support running either the complete suite:
   ```bash
   ./_tests
   python3 -m unittest discover -s tests -t .
   ```
   or testing a single standalone program:
   ```bash
   ./_tests <standalone_program>
   python3 -m unittest discover -s tests/<standalone_program> -t .
   ```
4. For bash test suites, name them `tests/_test_<name>` with `__VERSION__` in
   standard `Major.Minor.YYYYMMDDhhmmssZ` format (UTC timestamp, trailing Z).

## Verification checklist

- [ ] Test module lives in `tests/<standalone_program>/`.
- [ ] `./_tests <standalone_program>` runs green.
- [ ] `./_tests` full suite runs green.
