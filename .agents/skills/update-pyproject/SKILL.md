---
name: update-pyproject
version: 1.11.20260927131905Z
description: Use after any code change or addition in this project to check pyproject.toml and update it when out of sync (module coverage, mypy targets, entry point, version rule, tool config). Apply before committing.
load: always
---

# update-pyproject

## Overview

After any change or addition to the code, verify `pyproject.toml` still matches
the sources and update it when it is out of sync. The file declares how the flat
module set is shipped, what mypy type-checks, the console script, the dynamic
version source, and the ruff configuration — a code change can silently make any
of these wrong.

## When to use

Always after adding, renaming, or removing a top-level `*.py` module, changing
`remove_empty_folder_version.py`, touching the entry point, or changing a helper
script, and before committing. Run the checks below; update only the fields that
are actually out of sync. Do not touch fields that are already correct.

## Checks (run in order)

### 1. Module coverage — every top-level module must be listed

The project is flat (`py-modules`, no package directory), so setuptools does
**not** discover new modules on its own: every top-level module must be named in
`[tool.setuptools] py-modules`, without the `.py` suffix.

```bash
ls *.py                                 # what exists
grep -n 'py-modules' pyproject.toml     # what ships
```

Currently `["folder_remove_empty", "remove_empty_folder_version"]`. Add each new
`remove_empty_folder_*.py` module as it is created; a module missing here is
missing from the installed program.

### 2. Type-check coverage — the same modules plus the tests

`[tool.mypy] files` must cover every top-level module plus the test tree
(currently `["folder_remove_empty.py", "remove_empty_folder_version.py",
"tests"]`). Extend it whenever check 1 grows.

### 3. Console script — the entry point

`[project.scripts]` must name the entry point and its callable:

```toml
[project.scripts]
folder_remove_empty = "folder_remove_empty:main"
```

It changes only when `main()` moves or is renamed.

### 4. Version rule — one literal, one derived, no literal in pyproject.toml

`remove_empty_folder_version.__VERSION__` is the only literal version in the
project: `MAJOR.MINOR.<14-digit UTC timestamp>Z`, captured with
`~/sbin/timestamp` and the trailing `Z` appended.

`__version__` is derived from it by dropping the `Z`
(`__VERSION__.removesuffix("Z")`), because PEP 440 forbids the trailing `Z` and
setuptools rejects the `Z` form.

`pyproject.toml` therefore keeps the version dynamic — no literal `version`:

```toml
[project]
dynamic = ["version"]

[tool.setuptools.dynamic]
version = {attr = "remove_empty_folder_version.__version__"}
```

A literal `version = "..."` would be read by `./_check_version`, which requires
the `...Z` form, and that form is exactly what setuptools rejects — that is why
the literal was removed. Never add one back.

### 5. Helper-script versions — independent of the package version

Every shell helper carries its own uppercase `__VERSION__` with its own
major/minor, in the same `MAJOR.MINOR.<14-digit UTC>Z` shape: `_tests`, `_build`,
`_install`, `_menu`, `_run`, `_git`, `_check_version`, `_skill_sync`,
`hooks/pre-commit`, `hooks/install.sh`.

When a helper changes, bump only that helper's `__VERSION__` with a fresh
timestamp. Do NOT sync a helper to the package version.

```bash
grep -rn '__VERSION__=' _tests _build _install _menu _run _git _check_version \
    _skill_sync hooks
```

### 6. Tool config — change only when the code needs it

- `[tool.ruff]` — `line-length = 100`, `target-version = "py313"`, and the
  selected rule set (`E`, `F`, `I`, `UP`, `B`, `SIM`) change only when the code
  needs it. Never loosen a rule to make bad code pass; fix the code.
- `[tool.mypy]` — besides `files` (check 2), the options change only when the
  code needs them.

## Verification

```bash
python3 -m pytest
python3 -m ruff check .
python3 -m mypy
./_tests
./_check_version --all
```

## Common mistakes

| Mistake | Fix |
|---|---|
| Creating a top-level module and forgetting `py-modules` | Add its name (no `.py`) to `[tool.setuptools] py-modules`. |
| Forgetting to extend `[tool.mypy] files` after adding a module | List the module (with `.py`) plus `tests` in `[tool.mypy] files`. |
| Adding a literal `version = "1.0.20260927111114Z"` to pyproject.toml | Keep it dynamic; the `Z` form setuptools must accept is the derived `__version__`. |
| Syncing a helper's `__VERSION__` to the package version | Helpers self-version; bump only the helper that changed. |
| Reusing an old timestamp in a version | Capture `~/sbin/timestamp` immediately before writing. |
| Loosening ruff or mypy to pass on new code | Fix the code; the config covers the whole project. |
