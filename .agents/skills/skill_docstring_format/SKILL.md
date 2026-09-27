---
name: skill_docstring_format
description: >-
  Enforce the folder_remove_empty docstring format on every function, class, and method: a what-and-when description, a usage: line with <REQUIRED> and [OPTIONAL] parameters, a returns: line, and an example:. Docstrings feed the usage() help text (remove_empty_folder_options.py), the generated man page and tldr page, and README.md.
version: 1.3.20260927131905Z
load: always
---

# skill_docstring_format

## Purpose

Every function, class, and class function (method) in the project's top-level
modules (`folder_remove_empty.py` and `remove_empty_folder_*.py`) carries a
docstring in one fixed format, written for two readers at once:

- **Humans** — a reader sees what a callable does, *when* it does it, how to
  call it, what it returns, and a concrete example, without opening the body.
- **AIs and tooling** — the `usage:`, `returns:`, and `example(s):` lines are
  machine-parsed, so the docstring is the single source of truth for the
  `usage()` help text, the generated man page and tldr page, and the README.

## The Format

```python
def action_error(called_from_function, *msg):
    """report an error and increment the error counter <describe what it does and when it does it>
    usage: action_error <CALLED_FROM_FUNCTION> <MSG1> [MSG2] [MSG3]
    returns: nothing

    example: action_error("my_func", "file not found", "a.txt")

    """
```

The `<describe what it does and when it does it>` placeholder is replaced by a
real one-line description (see rule 1). The trailing blank line before the
closing `"""` is part of the format.

## Line-by-line rules

1. **First line — what and when.** One sentence describing what the callable
   does and *when* it does it (the trigger, condition, or side effect). Start
   with a lowercase verb. Examples:
   - `report an error and increment the error counter`
   - `print the abort banner when errors occurred`
   - `read a .ddconfiguration file when present`
2. **`usage:` line — invocation syntax.** The callable name followed by its
   parameters in UPPERCASE: required parameters in `<ANGLE_BRACKETS>`, optional
   parameters in `[SQUARE_BRACKETS]`, in call order. A callable with no
   parameters lists only its name (`usage: action_running`). Keep the whole
   `usage:` line on one line.
3. **`returns:` line — result contract.** What the callable returns, or
   `nothing` when it returns `None`. Use `never (exits N)` for `NoReturn`
   callables. Mention the failure mode when it matters
   (`True on success, False on error`).
4. **Blank line** — exactly one blank line between `returns:` and the
   `example:` / `examples:` block. `returns:` MUST always come before
   `example:` / `examples:`.
5. **`example:` line — one concrete call.** Real argument values, not
   placeholders. For several examples use `examples:` with one indented
   example per line.
6. **Trailing blank line** — one blank line after the last example line,
   before the closing `"""`.

## Scope

Apply the format to **every** callable in the project's top-level modules
(`folder_remove_empty.py` and `remove_empty_folder_*.py`):

- module-level functions (public and `_`-prefixed internal ones),
- classes,
- class functions (methods), including `__init__`, `@classmethod`,
  `@staticmethod`, and `_`-prefixed helpers,
- dataclasses and enums.

There is no exception for "obvious" or private code — the docstring is the
contract the tooling reads, and the `usage()` help text, the generated man page
and tldr page, and `README.md` quote it.

## Classes and methods

Classes use the same schema; `usage:` shows the constructor call and
`returns:` names the produced object:

```python
@dataclass
class IgnoreConfig:
    """loaded ignorelists: matcher, excluded files, pattern counts
    usage: IgnoreConfig(...)
    returns: config object

    example: IgnoreConfig()"""
```

Methods use the method name in `usage:` (no `self.` prefix):

```python
def verdict(self, rel_path: str, is_dir: bool) -> str:
    """return 'ignore' or 'include' for REL_PATH (last matching rule wins)
    usage: verdict(<REL_PATH>, <IS_DIR>)
    returns: 'ignore' or 'include'

    example: matcher.verdict("a/b.txt", False)"""
```

## Multiple examples

```python
def file_path_clean(path: str) -> str:
    """clean and normalize a file or directory path across all platforms
    usage: file_path_clean <PATH>
    returns: cleaned path

    examples:
      file_path_clean("C:\\Users\\user/.config/folder_remove_empty/logs//repllogs\\test.log")
      file_path_clean("./a//b/../c")"""
```

## Machine-parsing contract (why the format is fixed)

The docstring lines are machine-read, so they are a contract:

| Docstring line | Feeds |
|---|---|
| the first non-keyword line | the description in the `usage()` help text and in `README.md` |
| `usage: ...` | the invocation line in the `usage()` help text |
| `example:` / `examples:` lines | the examples in the `usage()` help text, the generated man page and tldr page |
| `returns: ...` | the result contract stated for the callable in `README.md` |

Consequences — never break these:

- `usage:`, `returns:`, `example:` / `examples:` must start at the line start
  (after indentation) with the exact lowercase prefix and a colon.
- `usage:` and each `example:` must stay on a single line.
- The first non-keyword line is the description, so it must be the first line
  of the docstring body.

## Propagation — the docstring is the base for the docs

Because the docstring lines are machine-read, they are the base for every
user-facing reference. After adding or changing a docstring, apply the
`update-docs` skill, which propagates the change to:

1. **The `usage()` help text** — `remove_empty_folder_options.py`: it is the
   single source of the help text printed by `python3 -m folder_remove_empty
   --help` and shown by the window's help dialog.
2. **The generated man page** — `man/folder_remove_empty.1`, regenerated with
   `python3 -m folder_remove_empty --print-man`.
3. **The generated tldr page** — `tldr/folder_remove_empty.page.md`, regenerated
   with `python3 -m folder_remove_empty --print-tldr`.
4. **The README** — `README.md`: the option reference, examples, and version
   line stay in sync.

Verify with:

```bash
python3 -m folder_remove_empty --help
./_tests
```

## Good vs bad

Good:

```python
def file_copy(source: str, destination: str) -> None:
    """copy a file if it exists
    usage: file_copy <SOURCE> <DESTINATION>
    returns: nothing

    example: file_copy("a.txt", "b.txt")"""
```

Bad — placeholder description, no `when`, missing `returns:`, no blank line
before `example:`:

```python
def file_copy(source: str, destination: str) -> None:
    """copy
    usage: file_copy <SOURCE> <DESTINATION>
    example: file_copy("a.txt", "b.txt")"""
```

## Common mistakes

| Mistake | Fix |
|---|---|
| Description without the "when" (trigger/condition) | Add the condition: `... when X` / `... if X` / `... unless X`. |
| `example:` directly after `returns:` with no blank line | Insert exactly one blank line between them. |
| `example:` before `returns:` | `returns:` MUST come before `example:` / `examples:`. |
| Placeholder values in `example:` (`<FILE>`, `"foo"`) | Use concrete, realistic values. |
| Multi-line `usage:` or `example:` | Keep each on one line — the parser reads line by line. |
| Missing `returns:` for a value-returning function | State the result contract (`True on success, False on error`). |
| Skipping the docstring on `_`-prefixed or "obvious" code | No exceptions — tooling and docs read every callable. |
| Changing a docstring without propagating | Run the `update-docs` skill (`usage()` help text, man page, tldr page, README). |
