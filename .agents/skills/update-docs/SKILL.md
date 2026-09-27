---
name: update-docs
version: 1.4.20260927131905Z
description: Use after any behaviour, CLI option, message or window change in this project to update usage() in remove_empty_folder_options.py, the generated man and tldr pages, README.md, ChangeLog.md and NEWS. Apply before committing.
load: always
---

# update-docs

## Overview

The help text, the two generated pages, and `README.md` are the user-facing
references to this program; `ChangeLog.md` and `NEWS` are its history. Any
change to a behaviour, a CLI option, a printed message, or a window control MUST
be reflected there before committing. Undocumented behaviour is a bug: the man
page and the tldr page are generated from the program, so a stale page is a
stale program.

## When to use

Always after adding, renaming, or changing a behaviour, a CLI option, a printed
message, or a window control, and before committing. Update the four places
below in this order — the later ones quote the earlier ones.

## Checks (run in order)

### 1. usage() in remove_empty_folder_options.py — the single source of the help text

`usage()` is the one place the help text lives. It is printed by
`python3 -m folder_remove_empty --help` and shown by the window's help dialog,
so both surfaces change with it.

- Every option the program accepts is listed with the same spelling the parser
  accepts, in the order the parser takes them.
- Every option entry keeps the docstring shape (first line = what-and-when,
  `usage:`, `returns:`), because the help text is built from the option
  docstrings — see the `skill_docstring_format` skill.
- A window label, a dialog title, or a printed message that changes is quoted in
  the help text; keep the wording identical.

Verify with:

```bash
python3 -m folder_remove_empty --help
```

### 2. the generated man page and tldr page

`man/folder_remove_empty.1` and `tldr/folder_remove_empty.page.md` are generated
from the program, never edited by hand. Regenerate and commit both; the commands
run the module directly, they do not need the Nuitka build:

```bash
python3 -m folder_remove_empty --print-man > man/folder_remove_empty.1
python3 -m folder_remove_empty --print-tldr > tldr/folder_remove_empty.page.md
```

### 3. README.md — describe the change with examples

Update `README.md` so a reader finds and can use the new behaviour:

- a new or changed CLI option → the usage overview and the examples block,
- a changed message, dialog, or window control → the matching feature section,
- a new module or subsystem → a section describing its role and structure,
- the version line → keep it in sync with the program version.

### 4. ChangeLog.md and NEWS — newest first, in the file's own shape

Add the entry at the top of both files; each keeps its own heading shape, so
never invent a third one.

- `ChangeLog.md`: a `## <version> - <YYYY-MM-DD>` heading, then the per-version
  entries; the version is the UTC timestamp stamp of the change.
- `NEWS`: a `* Version <version> (<YYYY-MM-DD>)` heading with the user-visible
  highlight in prose below it.

## Verification

```bash
python3 -m folder_remove_empty --help   # the help text shows the change
./_tests                                # suite + ruff + mypy stay green
```

## Common mistakes

| Mistake | Fix |
|---|---|
| Changing an option or message and leaving `usage()` untouched | Update `usage()` in `remove_empty_folder_options.py`; the window help dialog reads the same text. |
| Regenerating the man/tldr page but not committing it | Commit both generated files with the code change. |
| Updating the help text but not `README.md` | Add the option, message, or section to `README.md` too. |
| Shipping a user-visible change with no `ChangeLog.md` / `NEWS` entry | Add the entry at the top of both files, newest first. |
| Editing `man/` or `tldr/` by hand | Regenerate with `--print-man` / `--print-tldr`. |
