---
name: update-pyproject
description: Use after any code change or addition in the ddpico project to check pyproject.toml and update it when out of sync (version bump, package coverage, tool config). Apply before committing.
version: 1.10.20260911223255Z
load: always
---

# update-pyproject

## Overview

After any change or addition to the ddpico code, verify `pyproject.toml` still
matches the sources and update it when it is out of sync. The file declares the
package version, the shipped packages, the CLI entry point, and the tool
configuration (ruff, mypy) — a code change can silently make any of these wrong.

## When to use

Always after modifying, adding, or removing source files under `ddpico/`,
`tests/`, or the helper scripts, and before committing. Run the checks below;
update only the fields that are actually out of sync. Do not touch fields that
are already correct.

## Checks (run in order)

The project has several kinds of version variables. Only the first is the
package version; the others are independent and must NOT be forced to it.

**Package version** — `[project] version` in `pyproject.toml`, `__version__`
in `ddpico/internal.py`, and the `# version:` header in `ddpico/__init__.py`
must be identical. A code change requires bumping them together.

```bash
grep '^version = ' pyproject.toml          # [project] version
grep '^__version__' ddpico/internal.py     # package version
grep '^#   version:' ddpico/__init__.py    # header comment
```

If they differ, update all three to the same value.

**Helper-script `__VERSION__`** — every shell helper carries its own
`__VERSION__` (uppercase) in the same `MAJOR.MINOR.<YYYYMMDDhhmmss>Z` format
(UTC timestamp, trailing Z) but with its own major/minor, independent of the
package version:

```bash
grep -rn '__VERSION__=\|__version__=' _build _docs _install _menu _tests \
    _git _ddpico_logo completions hooks
```

When a helper script changes, bump ITS `__VERSION__` (fresh timestamp, its
own major/minor). Do NOT sync helpers to the package version. Convention is
uppercase `__VERSION__`; `_git` currently deviates with lowercase `__version__`
— normalize it to uppercase when touched.

**Runtime-derived `VERSION`** — `_build` reads the package version live
(`VERSION=$(python -m ddpico --version-only ...)`); never edit it manually.

**`LIB_VERSION`** — `ddpico/internal.py` aliases `__version__`; it follows
the package version automatically, no separate bump.

**Per-file `__version__` — MUST BE ENFORCED** — every source file and every
markdown file in the project carries its own `__version__`, and it MUST be
updated every time the file changes. This is a hard rule, not a suggestion.

- **Format** — PEP 440: `MAJOR.MINOR.MICRO`, where `MICRO` is always the
  UTC timestamp from `~/sbin/timestamp` (captured immediately before writing).
  Example: `1.0.20260831203102Z`.
  - Python source (`ddpico/**/*.py`): module-level `__version__ = "..."` after
    the import block (module-level constant; must not split the import block —
    ruff `I001`).
  - Markdown files: HTML comment as the first line,
    `<!-- __version__: 1.0.20260831203102Z -->`.
  - Shell helpers: `__VERSION__` (uppercase) — see above.
  - `SKILL.md` files: frontmatter `version:` satisfies this rule.
  - Exceptions: `ddpico/internal.py` (package `__version__`, already tracked)
    and `ddpico/__init__.py` (header `# version:`; must not shadow the
    imported package `__version__`).
- **Bump policy** — every change to a file updates its `__version__`:
  `MICRO` always refreshes to a fresh timestamp; `MINOR` for a feature or
  fix; `MAJOR` for a significant rewrite / breaking change.
- **Enforcement** — before committing, no source or markdown file may be
  missing a version:

  ```bash
  grep -rL '__version__\|__VERSION__\|^version:' --include='*.py' \
      --include='*.md' ddpico docs .agents README.md goal.md
  ```

  Empty output = compliant. Any listed file must be versioned before commit.

The package version follows the same rule the `ddpico/version` module enforces:
(Python) PEP 440 compliant version tracking (`Major.Minor.Micro`), where the
the format for `.micro` is different — a UTC timestamp in the format
`YYYYMMDDhhmmss` with a trailing `Z`.

- Format: `MAJOR.MINOR.<YYYYMMDDhhmmssZ>` (PEP 440 — no `-` or `+`).
- **Major** — significant rewrite / breaking change.
- **Minor** — feature addition or fix.
- **Micro (timestamp)** — UTC time of the change, captured
  **immediately before writing** via `~/sbin/timestamp` (it emits
  `YYYYMMDDhhmmssZ`, UTC, trailing Z). Do not reuse an old or pre-planned timestamp.

### 2. Package coverage — update only for new packages

`[tool.setuptools] packages` lists shipped packages. The project is a flat
package:

```toml
[tool.setuptools]
packages = ["ddpico"]
```

New `.py` modules under `ddpico/` are included automatically by `packages =
["ddpico"]` — **do not** add them. Update this list only when a new top-level
package directory was created that must ship.

### 3. CLI entry point — update only when the entry changes

`[project.scripts]` uses `dd`-prefixed console command names and must mirror the
`STANDALONE_PROGRAMS` registry in `ddpico/programs.py` (currently `ddpico`,
`ddtoolbox`, `ddfart`, `ddbak`, `ddmediadownloader`, `ddpico_lsp`, `ddcrawl`,
`ddznumber`, `ddversion_get_from_filepath`). Short/legacy names (`fart`,
`pyfart`, `bak`, `ddpico-bak`, `crawl`, `znumber`, `mediadownloader`,
`version_get_from_filepath`) are NOT console scripts — they exist only as
BusyBox applets in `ddpico/busybox.py::_APPLETS` (reachable via
`ddtoolbox <applet>` or argv[0] symlinks) and, where applicable, as registry
aliases. It changes only if `main()` moves or a new console script is added.
Adding new module functions (e.g. `configuration_*`) does **not** change it.

### 4. Tool config — update only when it must cover new files

- `[tool.mypy] files` — currently `["ddpico"]`. Extend only if new directories
  need type-checking.
- `[tool.ruff]` `select` / `line-length` — change only when a new file needs a
  different lint rule or line length. Do not loosen rules to satisfy new code;
  fix the code instead.

### 5. LSP catalog — regenerate after any command/module/datastructure change

Any change to a command, module, dataclass, or enum must be reflected in the
committed `ddpico/lsp/lsp_catalog.json` (the LSP server's vocabulary). If the
change touches those, regenerate so the committed catalog stays current:

```bash
ddpico lsp generate ddpico/lsp/lsp_catalog.json
```

`tests/test_lsp_catalog_stale.py` fails when the committed catalog is out of
date, so regeneration is enforced, not optional.

## Verification

After updating `pyproject.toml` (or when no update was needed), confirm the
package still works and the checks pass:

```bash
python -c "import ddpico; print(ddpico.__version__)"
ruff check ddpico tests
mypy ddpico
python -m unittest discover -s tests
```

## Common mistakes

| Mistake | Fix |
|---|---|
| Changing a helper script without bumping its `__VERSION__` | Bump the helper's own `__VERSION__` (fresh timestamp). |
| Editing a file without bumping its `__version__` | Refresh the micro timestamp (fresh `~/sbin/timestamp`). |
| Creating a new file without `__version__` | Add it at creation: `1.0.<UTC timestamp>Z`. |
| Syncing helper `__VERSION__` to the package version | Helpers self-version; keep their own major/minor. |
| Adding new `ddpico/*.py` to `packages` | Not needed — `packages = ["ddpico"]` includes them. |
| Reusing an old timestamp in the version | Capture `~/sbin/timestamp` right before writing. |
| Loosening ruff/mypy to pass on new code | Fix the code; the config is for the whole package. |
