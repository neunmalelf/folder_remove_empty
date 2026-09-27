# Project Specification — folder_remove_empty (FOLDER_REMOVE_EMPTY)

Language-agnostic functional specification of the utility: what it does, how
the engine works, how the terminal front end behaves, and how the desktop
window is laid out and behaves. No implementation-language details.

---

## 1. Overview

`folder_remove_empty` removes every empty folder below a start folder,
deepest first. The start folder itself is never removed, only the folders
below it.

- One run removes whole chains of nested empty folders: a folder counts as
  empty as soon as its last empty subfolder is gone, so the deepest folder
  goes first and its parent follows in the same run.
- The program is a port of the shell script `_folder_remove_empty`; the
  rules of the script are unchanged.
- It has two front ends over one shared engine:
  - a **desktop window** (default), and
  - a **terminal mode** selected with `--no-gui`.
- Command-line options given at startup pre-fill the window; in terminal
  mode they run unchanged.

---

## 2. Core concepts and engine rules

### 2.1 Start folder

- At most one path argument is accepted.
- No path means the current working folder.
- A given path must exist and must be a folder; otherwise the job is
  refused before anything runs.
- The start folder is resolved to an absolute, cleaned path (symbolic
  links stay visible, i.e. resolved the way `cd PATH && pwd` resolves).
- The resolved folder is what reports and histories name in full.
- The start folder itself is never removed, even when it ends up empty.

### 2.2 What "empty" means

A folder is empty when **all** of the following hold:

- it can be read (its entries can be listed);
- every entry it holds is a folder that is itself empty.

Consequences:

- A file, a symbolic link (including a link pointing at a folder), a
  socket, or any other non-folder entry blocks the folder: nothing but
  folders is ever lost.
- A folder whose content cannot be read is never treated as empty — what
  cannot be read cannot be proven empty.
- Folders are rated bottom-up (children before parents), so chains of
  nested empty folders all fall in one run.

### 2.3 Removal

- Folders are worked deepest first.
- Removal uses remove-empty-folder semantics (equivalent of `rmdir`): it
  refuses anything that is not empty, so only rated-empty folders can go.
- A folder rated empty whose removal is refused is reported
  (`not removed: <folder> (<reason>)`) and its parent is skipped as well,
  because the refusal below is the reason the parent would fail next.
- Removals are counted; refusals are counted separately.

### 2.4 Run phases

1. **Resolve** the start folder (refuse on bad path).
2. **Scan** every folder below it, bottom-up, marking vacant and
   kept folders.
3. **Mark** which folders go (see kept-folder rule below).
4. **Work** the marked folders deepest first; in verbose mode, vacant
   kept folders left in place are additionally reported.
5. **Summarize** with closing counters (removed / refused / stopped /
   dry-run, see message catalog).

### 2.5 Pause / stop (window only)

- Before every folder the run asks a checkpoint: while paused it waits in
  front of the next folder; when stopped it ends before the next folder.
- A stopped run still reports its closing counters, flagged as stopped.
- The terminal front end has no pause/stop; its checkpoint always lets
  the run continue.

---

## 3. Kept folders (never removed on their own)

### 3.1 Fixed keep list

Never removed on their own:

- `.Trash-1000`, `.cache`, `System Volume Information`, `$RECYCLE.BIN`
  (with or without the leading dot);
- every name starting with `ZZZZ`;
- every name starting with four ASCII digits (e.g. `2026-09-23_backup`);
- every name containing `!!! MISSING !!!` in any letter case (marks a
  folder whose content is known to be missing — an empty one is a hole,
  not a leftover).

Matching is by folder base name (not by path).

### 3.2 Extra kept names

- Additional names come from the `Extra excludes` field / the
  `FOLDER_REMOVE_EMPTY_EXCLUDE` environment variable, `:` separated.
- Empty pieces are ignored, so a trailing or doubled separator adds
  nothing.
- A name ending with `*` keeps every name starting with that prefix
  (e.g. `keep-*` keeps `keep-me`); otherwise the name must match exactly.

### 3.3 Kept-folder semantics

- The empty subfolders of a kept folder are still removed.
- The kept folder itself stays, even when it is empty afterwards —
  **unless** its parent is removed as well: a kept folder goes with a
  parent that is empty apart from empty kept folders, but stays when only
  kept folders hold the parent in place.

---

## 4. Outcomes and message catalog

One folder produces at most one outcome line:

| Outcome | Line shape |
|---|---|
| Removed | `removed: <folder>` |
| Dry run (would remove) | `would remove: <folder>` |
| Refused removal | `not removed: <folder> (<reason>)` |
| Kept (verbose only) | `excluded, kept: <folder>` |

Run notes (always shown, in every history filter):

- `start folder: <folder>` — the resolved folder a run begins in.
- `path exists: <folder>` — the path check (terminal: only when a path
  was given; window: live status line, see §7).
- `ERROR: <reason>` — refused path or failed start.

Closing lines:

- Stopped run: `stopped`.
- Dry run: `dry run: <removed> of <rated> folder(s) would be removed`.
- Normal run, none removed: `no empty folder found`.
- Normal run: `<n> empty folder(s) removed`.
- Refusals: `<n> folder(s) kept`.

---

## 5. Command line

### 5.1 Synopsis

```text
folder_remove_empty [OPTIONS] [PATH]
```

### 5.2 Options

| Option | Meaning |
|---|---|
| `-d`, `--dryrun`, `--dry-run` | Print the folders that would be removed and remove nothing |
| `-v`, `--verbose` | Report every kept folder that was left in place |
| `--no-gui` | Work on the terminal instead of opening the window |
| `--print-man` | Print the man page (roff) and exit |
| `--print-tldr` | Print the tldr page (markdown) and exit |
| `--version` | Print the program version and exit |
| `-h`, `--help` | Print the usage text and exit |

### 5.3 Path argument

- Zero or one path; two paths are refused with
  `ERROR: only one path is allowed, got: <arg>` (no usage text).
- An unknown `-` option is refused with `ERROR: unknown option: <opt>`
  followed by the usage text.
- Without `--no-gui`, options and path only pre-set the window.

### 5.4 Environment variables

| Variable | Meaning |
|---|---|
| `FOLDER_REMOVE_EMPTY_EXCLUDE` | Extra kept names, `:` separated; trailing `*` = prefix rule. Pre-fills `Extra excludes`. |
| `NO_COLOR` | Non-empty value switches the terminal colors off. |

### 5.5 Exit codes

- `0` — the job ran to its end (folders removed or listed), or an
  informational output (`--help`, `--version`, `--print-man`,
  `--print-tldr`) was produced.
- `1` — the given path does not exist, is not a folder, or an option is
  unknown (also: more than one path).

### 5.6 Informational outputs

- `--help` prints the usage text (synopsis, options, window guide, kept
  list, environment, exit codes).
- `--version` prints `<app> version <stamp>`.
- `--print-man` prints a roff man page (name, synopsis, description,
  options, window, kept folders, environment, exit status, examples).
- `--print-tldr` prints a `tldr`-style page (one-line summary plus
  example commands: window run, terminal run, dry run, verbose, extra
  excludes, help, version, exit-code check).

### 5.7 Examples

```text
folder_remove_empty /data/archive                  # in the window
folder_remove_empty --no-gui /data/archive         # on the terminal
folder_remove_empty --dry-run --verbose /data/archive   # look first
FOLDER_REMOVE_EMPTY_EXCLUDE='keep-*:downloads*' \
    folder_remove_empty --no-gui /data/archive    # extra kept names
```

---

## 6. Terminal mode (`--no-gui`)

- Removed folders go to **stdout**, everything else to **stderr**:
  - stdout: `removed: <folder>` lines (green on a color terminal) and
    the closing summary (`<n> empty folder(s) removed` /
    `no empty folder found`).
  - stderr: `path exists:` (only when a path was given), `start
    folder:`, kept lines (`excluded, kept:`), refused lines
    (`not removed:`, yellow), `<n> folder(s) kept`, and `ERROR:` lines
    (red).
- Colors (green removed / yellow not-removed / red error) appear only on
  a terminal and are disabled by a non-empty `NO_COLOR`.
- Dry run prints the plain folder paths (one per line) on stdout and
  removes nothing; it prints no closing summary.
- Errors print as `ERROR: <reason>` on stderr with exit code 1.

---

## 7. Desktop window

### 7.1 Window frame

- Title: `<app> <version>`; default size 960×720.
- Carries the app icon (purple rectangle with the white letters "fr",
  provided in 16–512 px for the window manager and desktop installation).
- Always starts in the light theme; switchable to dark (see Help/theme
  row). (Note: older user documents say it follows the desktop variant —
  the implementation starts light.)

### 7.2 Main layout (top to bottom)

1. **Start path row** — label `Start path`, a single-line text field,
   and a `Browse…` button behind it.
   - The field is pre-filled with the startup path, or the current
     folder when none was given, so it always names the folder a run
     would work in.
   - Placeholder: `folder to scan (default: the current folder)`.
   - Light-grey bordered box around the field and around the button;
     borders follow the theme switch.
2. **Status line** — below the field, updated live as you type:
   - usable: `path exists: <absolute folder>` (green);
   - unusable: `ERROR: <reason>` (red).
3. **Option checkboxes** — side by side:
   - `Dry run - print the folders that would be removed and remove nothing`
   - `Verbose - report every kept folder that was left in place`
4. **Extra excludes row** — label `Extra excludes` plus a single-line
   field (placeholder: names that are never removed, `:` separated,
   `*` at the end keeps every name starting with it).
5. **History filter row** — label `Show in history` plus four radio
   options: `All`, `Removed`, `Kept`, `Not removed` (default `All`).
6. **Button row** — five equally weighted buttons with 8-unit gaps, in
   this order: `Help`, theme toggle, `Exit`, `Pause`, `Start`.
7. **Current folder row** — label `Current folder` plus a read-only
   single-line field (placeholder `no folder yet`) showing the folder
   rated or removed right now.
8. **`History` heading** — bold label.
9. **History list** — fills the remaining space; bordered, scrollable,
   auto-scrolled to the bottom as lines arrive. One line per outcome
   (see §7.4).

### 7.3 Controls and their behavior

- **Start path field** — free text; every change re-runs the check and
  its status line. A picked folder (see §8) is inserted and re-checked.
- **Browse…** — opens the folder dialog (§8).
- **Dry run / Verbose** — checkboxes; read when a run starts.
- **Extra excludes** — free text; read when a run starts (surrounding
  whitespace trimmed).
- **Show in history** — radio group; re-filters the list immediately.
  Run notes (start folder, closing lines) are shown in every setting.
- **Help** — opens the help dialog (§7.6).
- **Theme toggle** — labeled `Dark mode` in the light theme and
  `Light mode` in the dark theme; switches foreground, background,
  control borders, and history colors.
- **Exit** — stops a run in flight and closes the window; updates
  arriving afterwards are dropped.
- **Pause** — disabled while idle. During a run it holds the job in
  front of the next folder and turns into `Resume`; pressing again lets
  the run continue. Has no effect without a running job or on a stopped
  one.
- **Start** — labeled `Start` idle, `Restart` during a run.
  - Refused path: re-checks, appends a red `ERROR:` history line, starts
    nothing.
  - Valid path: stops a run in flight first (it ends in front of the
    next folder), then starts over with the current field settings.
  - After the run the window returns to idle (`Start`, pause disabled).
- **Current folder** — read-only; follows the run, stays on the last
  folder afterwards.
- **History** — every folder worked on this session plus run notes and
  closing lines; newest last.

### 7.4 History colors (per theme variant)

- removed → green;
- dry-run `would remove` → amber/brown;
- kept (`excluded, kept`) → grey;
- refused (`not removed`) → orange;
- errors → red;
- run notes / closing lines → default foreground.

### 7.5 Run lifecycle in the window

- Start validates the path field first; an invalid path produces an
  error history line and no run.
- `Start folder:` note, per-folder `Current` updates, one history line
  per outcome, then the closing lines — all appearing live as the run
  proceeds.
- Pause holds the run before the next folder; Restart replaces the live
  run (only the newest run owns the window); Exit stops the run and
  closes; closing drops late updates.
- An internal worker failure is shown as a red
  `ERROR: internal failure: <reason>` history line instead of closing
  the window.

### 7.6 Help dialog

Replaces the main content while open:

- heading `Help`;
- the usage text (same text as `--help`), one line per row, in a
  bordered scrollable list filling the dialog;
- an `OK` button below the list that closes the dialog.

### 7.7 Themes

- Light: white background, black foreground, medium-grey control
  borders.
- Dark: near-black background, white foreground, light-grey control
  borders, adjusted accent color.
- The toggle button always names the theme it switches *to*.

---

## 8. Folder selection dialog

### 8.1 Standard dialog (primary)

- The `Browse…` button first opens the **standard folder dialog of the
  desktop** (provided by the desktop's dialog helper).
- It starts in the folder currently in the path field, or the current
  working folder when that field cannot be used.
- Confirming puts the chosen folder into the path field and re-runs the
  check line; cancelling keeps the field untouched.
- The dialog blocks interaction while open but never freezes the run
  state behind it (it runs off the UI flow and hands the choice over).

### 8.2 Built-in picker (fallback)

When the desktop answers no standard dialog, a built-in picker replaces
the main content instead. Layout, top to bottom:

1. heading `Choose folder`;
2. the folder currently listed (full path);
3. an error line (`ERROR: <reason>`, red) only when the folder cannot
   be read;
4. an `Up` button moving to the parent folder;
5. a bordered scrollable list filling the dialog, one button per
   subfolder (alphabetical); pressing one descends into it;
6. a bottom row with two equal buttons: `Select` and `Cancel`.

Behavior:

- `Select` puts the listed folder into the path field, re-checks it,
  and closes the picker.
- `Cancel` closes the picker without touching the path field.
- Only folders are listed; files never appear.

---

## 9. History filter semantics

- `All` shows every line.
- `Removed` shows `removed:` / `would remove:` lines.
- `Kept` shows `excluded, kept:` lines.
- `Not removed` shows `not removed:` and `ERROR:` lines.
- Lines without a kind (run start note, closing counters) pass every
  filter.

---

## 10. Installation and desktop integration

- The program installs as a single executable (`folder_remove_empty`).
- The icon set (16, 24, 32, 48, 64, 128, 256, 512 px) installs into the
  desktop icon folders so launchers, window lists, and task bars find
  every size; the largest embedded icon serves the window manager.
- Generated documentation (man page, tldr page) is produced from the
  program itself so it cannot drift from the behavior above.

---

## 11. Safety guarantees

- The start folder is never removed.
- Only folders rated empty by the bottom-up scan are removed, using
  remove-empty-folder semantics — content (files, links, sockets, …)
  can never be deleted through this tool.
- Unreadable folders are treated as non-empty.
- Refused removals protect their parents.
- Kept names (fixed list, prefixes, digit dates, missing markers, extra
  patterns) are never removed on their own.
- Dry run changes nothing on disk.
- Closing the window stops a running job; no updates leak after close.
