---
name: update-docs
description: Use after any change or addition to the ddpico code or functionality to update the usage function (ddpico/help.py), REPL commands, and README.md. Apply before committing.
version: 1.3.20260830232840Z
load: always
---

# update-docs

## Overview

Every change or addition to the ddpico code, CLI options, REPL commands, and
functionality must be reflected in the two user-facing references: the `usage()`
output (the `ddpico -h` command list, `ddpico --help <COMMAND>`) and `README.md`.
A new or changed function, command, CLI flag, or REPL command that is not listed
there is undocumented. Run the checks below after every code change and update the
references before committing.

## When to use

Always after adding, renaming, or changing a public function, command, module,
CLI flag, or REPL command in the ddpico project, and before committing. Do not
commit a code change that leaves `usage()` or `README.md` stale.

## Checks (run in order)

### 1. usage() & COMMANDS registry — every public function and meta-command must be listed

The `usage()` output is built from `_DOC_SECTIONS` and meta-command registrations
(`_register_repl`, `_register_pipe`, `_register_eval`, `_register_ddtiny`) in `ddpico/help.py`.

- **Topic functions**: Add every new or changed public function to the correct `_DOC_SECTIONS`
  group (e.g. `("FILE", [...])` or `("CONFIGURATION", [...])`).
- **Function docstrings**: Must carry a `usage:` line and optional `examples:` — `_doc_to_entry`
  reads them to build the help entry.
- **Re-exports**: Re-export from `ddpico/__init__.py` (in the `from .<module> import (...)` block).
- **Meta commands & REPL**: If REPL commands or CLI flags change (e.g. `/log_on`, `/log_off`,
  `--repllog_path`, `--configuration_file`), ensure:
  1. The header of `usage()` in `ddpico/help.py` lists the flag and REPL commands.
  2. `COMMANDS["repl"]` in `_register_repl()` contains updated `desc`, `usage`, and `examples`.

Verify with:
```bash
python -c "from ddpico.help import usage; usage()"
```

### 2. README.md — describe the change with examples

Update `README.md` so a reader can find and use the new functionality:

- **New command group / function** → add it to the "Command groups" paragraph or relevant section.
- **New CLI flag or meta command** → add an entry in the CLI usage overview and examples block.
- **REPL commands** → maintain the "REPL Commands & Shortcuts" table and REPL session examples in `README.md`.
- **New module or subsystem** → add a dedicated section describing its structure, rules, and Python/CLI examples.
- **Version line** → keep the `- **version:**` line in sync with the package version.

### 3. LSP catalog — regenerate after command/module/datastructure changes

Any change to a command, module, dataclass, or enum must be reflected in the
committed `ddpico/lsp/lsp_catalog.json` (the LSP server's vocabulary). After
updating `help.py` / module docstrings, regenerate it:

```bash
ddpico lsp generate ddpico/lsp/lsp_catalog.json
```

`tests/test_lsp_catalog_stale.py` fails when the committed catalog diverges
from the live package, so this step is enforced in the suite.

### 4. Verify

```bash
python -c "import ddpico; print(ddpico.__version__)"   # import + version
python -m unittest discover -s tests                    # suite still green
ruff check ddpico tests
mypy ddpico
```

## Common mistakes

| Mistake | Fix |
|---|---|
| Adding a function but not registering it in `_DOC_SECTIONS` | Add it to the matching section in `ddpico/help.py`. |
| Adding a function but not re-exporting it from `__init__.py` | Add it to the `from .<module> import (...)` block in `ddpico/__init__.py`. |
| Adding/changing REPL commands without updating `_register_repl` or `usage()` | Update `_register_repl` and `usage()` header in `ddpico/help.py`. |
| Updating code without updating README.md tables and examples | Add explanations, command tables, and CLI/REPL code snippets to `README.md`. |
| Forgetting the version bump | Apply the `update-pyproject` skill (version sync across `pyproject.toml`, `internal.py`, `__init__.py`, and `README.md`). |
