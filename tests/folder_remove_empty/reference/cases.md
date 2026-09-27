# Go reference captures — `folder_remove_empty`

Reference behaviour of the **Go** program that this repository ports to Python,
captured once so phase 3 of the port can be compared line for line.

Every case has three files in this directory:

| File | Holds |
|---|---|
| `<case>.out` | stdout, the bytes exactly as written |
| `<case>.err` | stderr, the bytes exactly as written |
| `<case>.rc`  | exit status, one decimal line with a LF (`0` or `1`) |

An empty stream is an empty file, not a missing one. No file of the colourless
capture carries CR bytes or ESC (ANSI) bytes; the `pty_*` captures appended at
the end do carry ESC bytes (and no CR bytes either — see that section).

## Provenance

| Fact | Value |
|---|---|
| Go source | `~/projects/_folder_remove_empty` at `a2f8b9e82c4b6e5ff6a3973e937a0b607f9c4128` (2026-09-23) |
| Source state | worktree dirty, pre-existing and untouched by this capture: `M Makefile README.md cmd/folder_remove_empty/main.go doc.go go.mod go.sum icon.go theme.go ui.go ui_test.go`, `?? folder-remove-svgrepo-com.svg project_specs.md` |
| Toolchain | `go1.27.1` (the `go` in `PATH` is `go1.26.8`, `GOTOOLCHAIN=local`, so the build ran with `GOTOOLCHAIN=auto`) |
| Build command | `cd ~/projects/_folder_remove_empty && GOTOOLCHAIN=auto nice -n 19 ionice -c 3 go build -p 1 -o /tmp/fre-go ./cmd/folder_remove_empty` |
| Binary | `/tmp/fre-go`, ELF 64-bit x86-64, `CGO_ENABLED=1`, sha256 `39f4fe878c35a5f819e96b2e2e77a296c2a4893a335496485b382bbf3453bdde`, module `folder_remove_empty/cmd/folder_remove_empty v0.0.0-20260923194927-a2f8b9e82c4b+dirty`; deleted after the capture |
| Program version | `folder_remove_empty version 0.5.20260923194832` (see `info_version.out`) |
| User | uid 1000 (`fmann`), **not** root — the refused-removal case needs that |
| Scratch root | `/tmp/fre-ref.E6hTEvVG`, created with `mktemp -d`, deleted after the capture |

The build command differs from the plain `go build -o /tmp/fre-go .` in one
point: the **root package of the Go module is a library** (`package
folderremoveempty`, no `main`), so building `.` writes a linkable archive
(`current ar archive`) to the output path instead of a program; the `main`
package sits in `./cmd/folder_remove_empty`. The capture therefore builds that
package. No file was written into the Go source tree.

## How a capture was taken

Each case is one shell statement, with the two streams redirected to separate
regular files and the status read afterwards:

```bash
env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR \
    /tmp/fre-go --no-gui "$T" > "$case.out" 2> "$case.err"
printf '%s\n' "$?" > "$case.rc"
```

`FOLDER_REMOVE_EMPTY_EXCLUDE` and `NO_COLOR` are removed from the environment
for every case that does not set them itself, so the captures do not depend on
the shell that made them. `env -u` on a name that is not set is a no-op.

### Colour

The captures are the **colourless** form. The reporter colours a stream only
when that stream is a character device and `NO_COLOR` is empty; here stdout and
stderr are regular files, so the colour check fails and `paint()` returns every
text unchanged. **The coloured form is not among these cases** — it needs a pty
(`script`, `socat`), which this capture deliberately did not use; it was
captured separately through two ptys and lives in the `pty_*` files of the
section `## Coloured pty captures` at the end. The
`no_color` case (`NO_COLOR=1`) is byte-for-byte the same shape as
`terminal_run` and proves only that the variable changes nothing when the
stream is not a terminal; the ANSI sequence a terminal would see is in the Go
sources (`ansiGreen`, `ansiYellow`, `ansiRed`, `ansiOff` in `reporter.go`).

## Scratch root and per-case trees

Everything lived under the one scratch root `/tmp/fre-ref.E6hTEvVG`, which is
gone now. The trees were built by the builder script below, one fresh copy per
case, because every run that is not a dry run eats its tree.

| Case | Tree (below the scratch root) | Mutated by its own run |
|---|---|---|
| `terminal_run` | `terminal_run/tree` | yes — 13 folders removed, 1 refused |
| `terminal_dry_run` | `terminal_dry_run/tree` | no — verified: listing before and after are identical |
| `terminal_verbose` | `terminal_verbose/tree` | yes — same tree as `terminal_run` |
| `env_excludes` | `env_excludes/tree` | yes — 12 folders removed, `keep-me` kept |
| `no_color` | `no_color/tree` | yes — same tree as `terminal_run` |
| `not_a_folder` | `not_a_folder/tree/withfile/note.txt` (a file) | no — the run is refused at the path check |
| `two_paths` | `two_paths/a` and `two_paths/b`, two empty siblings | no — refused at the command line |
| `unknown_option`, `missing_path`, `info_*` | none | no |

`not_a_folder` gets its own tree so the file it names is independent of any
mutated case; the path check refuses the file before anything is scanned.

## The scratch tree shape

```text
tree/
├── a/b/c/                        three empty folders in a chain
├── withfile/
│   ├── note.txt                  a file, content "reference tree: a file blocks its folder\n"
│   └── empty_sub/                an empty folder next to a file
├── symlink_holder/
│   ├── target/                   a real, empty folder
│   └── link_to_target -> target  a symlink to a folder
├── .cache/
│   └── inner/                    an empty subfolder of a kept folder
├── ZZZZ-old/
│   └── inner/
├── 2026-09-23_backup/
│   └── inner/
├── data !!! missing !!! here/
│   └── inner/
├── keep-me/
│   └── inner/
├── keepboth/
│   └── .cache/                   a kept folder whose parent is vacant
└── readonly/                     mode 0555, no write permission
    └── inner/
```

| Entry below `tree/` | Kind, mode | Intended property | Outcome of a plain `--no-gui` run |
|---|---|---|---|
| `tree` itself | dir 0755 | the start folder | never rated, never removed — its own emptiness does not matter |
| `a`, `a/b`, `a/b/c` | dirs 0755 | a chain of nested empty folders | all three removed, deepest first: `a/b/c`, `a/b`, `a` |
| `withfile` | dir 0755 | holds a file and an empty folder | never vacant, stays |
| `withfile/note.txt` | file 0644 | a file blocks its folder | never removed, never rated as a folder |
| `withfile/empty_sub` | dir 0755 | empty folder inside a folder that also holds a file | removed, `withfile` stays |
| `symlink_holder` | dir 0755 | holds a real folder and a symlink | stays: the link blocks it, so it is not vacant |
| `symlink_holder/target` | dir 0755 | the real empty folder the link points at | removed — it is a plain folder below the root |
| `symlink_holder/link_to_target` | symlink → `target` | a link to a folder is a link: neither followed nor removed | never removed; dangles once `target` is gone |
| `.cache` | dir 0755 | a name of the fixed keep list | kept (its parent, the tree root, is never removed) |
| `.cache/inner` | dir 0755 | empty subfolder of a kept folder | removed — a kept folder still loses its empty subfolders |
| `ZZZZ-old`, `ZZZZ-old/inner` | dirs 0755 | name starting with `ZZZZ` | `inner` removed, `ZZZZ-old` kept |
| `2026-09-23_backup`, `…/inner` | dirs 0755 | name starting with four digits | `inner` removed, the dated folder kept |
| `data !!! missing !!! here`, `…/inner` | dirs 0755 | name holding `!!! MISSING !!!` in **lower** case | `inner` removed, the folder kept |
| `keep-me`, `keep-me/inner` | dirs 0755 | kept only by `FOLDER_REMOVE_EMPTY_EXCLUDE='keep-*'` | `inner` removed; `keep-me` itself removed in every run that does not set the variable |
| `keepboth` | dir 0755 | a vacant folder holding nothing but a kept child | removed, and it drags the kept child with it |
| `keepboth/.cache` | dir 0755 | a keep-list name inside a removed parent | removed too |
| `readonly` | dir **0555** | a parent without write permission | its child cannot be removed; the parent is then skipped silently and stays |
| `readonly/inner` | dir 0755 | the removal that is refused | `not removed: … (remove …: permission denied)` on stderr; the exit status stays 0 |

The exact builder, byte for byte what produced the trees above:

```bash
#!/bin/bash
# Builds the reference scratch tree of tests/folder_remove_empty/reference/.
#
# Usage: build_tree.sh TREE      (TREE must not exist yet)
# Every folder and file it creates is listed in cases.md with its intent.
set -u

T=${1:?usage: build_tree.sh TREE}
if [ -e "$T" ]; then
	printf 'build_tree.sh: %s already exists\n' "$T" >&2
	exit 1
fi
umask 022

# 1) a chain of nested empty folders: c under b under a, all three are removed
mkdir -p "$T/a/b/c"

# 2) a folder that holds a file: the file blocks it, the folder stays
mkdir -p "$T/withfile"
printf 'reference tree: a file blocks its folder\n' > "$T/withfile/note.txt"

# 3) an empty folder inside a folder that also holds a file: removed, parent stays
mkdir -p "$T/withfile/empty_sub"

# 4) a symlink to a folder: the link is neither followed nor removed, it blocks
#    symlink_holder, while the real folder it points at is a plain empty folder
#    below the root and goes
mkdir -p "$T/symlink_holder/target"
ln -s target "$T/symlink_holder/link_to_target"

# 5) a name of the keep list, with an empty subfolder: the subfolder goes, the
#    kept folder stays because the tree root is never removed
mkdir -p "$T/.cache/inner"

# 6) a name starting with ZZZZ: kept, its empty subfolder goes
mkdir -p "$T/ZZZZ-old/inner"

# 7) a name starting with four digits (a dated folder): kept, its empty subfolder goes
mkdir -p "$T/2026-09-23_backup/inner"

# 8) a name holding "!!! MISSING !!!" in lower case: kept, its empty subfolder goes
mkdir -p "$T/data !!! missing !!! here/inner"

# 9) a name kept only by FOLDER_REMOVE_EMPTY_EXCLUDE='keep-*' (case env_excludes);
#    without that variable the folder is an ordinary empty folder and goes
mkdir -p "$T/keep-me/inner"

# 10) a vacant parent holding nothing but a kept child: the parent goes and drags
#     the kept child with it
mkdir -p "$T/keepboth/.cache"

# 11) a removal that is refused: the parent takes no write permission, so rmdir of
#     the child fails and the parent is skipped as well
mkdir -p "$T/readonly/inner"
chmod 0555 "$T/readonly"

printf 'built %s\n' "$T"
```

## The cases

`SCRATCH` below is `/tmp/fre-ref.E6hTEvVG`; `$T` is the tree of that row. The
binary was `/tmp/fre-go` and the working directory of every call was the
scratch root.

| Case | Exact command | rc | Output files |
|---|---|---|---|
| `terminal_run` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go --no-gui "$SCRATCH/terminal_run/tree"` | 0 | `terminal_run.out`, `.err`, `.rc` |
| `terminal_dry_run` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go --no-gui --dry-run "$SCRATCH/terminal_dry_run/tree"` | 0 | `terminal_dry_run.out`, `.err`, `.rc` |
| `terminal_verbose` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go --no-gui --verbose "$SCRATCH/terminal_verbose/tree"` | 0 | `terminal_verbose.out`, `.err`, `.rc` |
| `unknown_option` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go --no-gui --bogus` | 1 | `unknown_option.out` (empty), `.err`, `.rc` |
| `two_paths` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go --no-gui "$SCRATCH/two_paths/a" "$SCRATCH/two_paths/b"` | 1 | `two_paths.out` (empty), `.err`, `.rc` |
| `missing_path` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go --no-gui /tmp/does-not-exist` | 1 | `missing_path.out` (empty), `.err`, `.rc` |
| `not_a_folder` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go --no-gui "$SCRATCH/not_a_folder/tree/withfile/note.txt"` | 1 | `not_a_folder.out` (empty), `.err`, `.rc` |
| `env_excludes` | `env -u NO_COLOR FOLDER_REMOVE_EMPTY_EXCLUDE='keep-*' /tmp/fre-go --no-gui "$SCRATCH/env_excludes/tree"` | 0 | `env_excludes.out`, `.err`, `.rc` |
| `no_color` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE NO_COLOR=1 /tmp/fre-go --no-gui "$SCRATCH/no_color/tree"` | 0 | `no_color.out`, `.err`, `.rc` |
| `info_version` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go --version` | 0 | `info_version.out`, `.err` (empty), `.rc` |
| `info_help` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go --help` | 0 | `info_help.out`, `.err` (empty), `.rc` |
| `info_print_man` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go --print-man` | 0 | `info_print_man.out`, `.err` (empty), `.rc` |
| `info_print_tldr` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go --print-tldr` | 0 | `info_print_tldr.out`, `.err` (empty), `.rc` |

### What each capture shows

- **`terminal_run`** — 13 `removed: <abs>` lines on stdout (deepest first,
  folder names in `os.ReadDir` order per directory), the closing
  `13 empty folder(s) removed`; `path exists: …` and `start folder: …` first on
  stderr, then the single `not removed: …/readonly/inner (remove …: permission
  denied)` and the closing `1 folder(s) kept`. The refused folder also stops its
  parent from being tried, so `readonly` never shows up in either stream.
- **`terminal_dry_run`** — stdout lists **15** bare absolute paths, one per
  line, with no `removed:` prefix and no closing counter; the two extra lines
  are `readonly/inner` and `readonly`, which a dry run never tries to remove.
  stderr stops after `start folder: …`. The tree is unchanged afterwards.
- **`terminal_verbose`** — stdout is identical in shape to `terminal_run`;
  stderr gains one `excluded, kept: <abs>` line per kept folder that is vacant
  and left in place: `.cache`, `2026-09-23_backup`, `ZZZZ-old`,
  `data !!! missing !!! here`. `keepboth/.cache` gets no such line because its
  parent was removed and it went with it; `readonly` gets none because it is
  not kept, only skipped.
- **`env_excludes`** — `keep-me/inner` is still removed, `keep-me` is not
  (12 removals instead of 13); without `--verbose` no line names it, so the
  difference shows in the counter and in the residual tree. `keepboth/.cache`
  still goes, so the extra pattern does not rescue a kept folder inside a
  removed parent.
- **`no_color`** — same shapes as `terminal_run`; with a non-terminal stream
  the uncoloured form is written whether or not `NO_COLOR` is set.
- **`unknown_option`** — stderr holds `ERROR: unknown option: --bogus` followed
  by the whole usage text and nothing else; stdout is empty.
- **`two_paths`** — stderr holds only
  `ERROR: only one path is allowed, got: <second path>`; no usage text.
- **`missing_path`** — stderr holds only
  `ERROR: the given path does not exist: /tmp/does-not-exist`. `/tmp/does-not-exist`
  must really be absent for this capture to mean anything.
- **`not_a_folder`** — stderr holds only `ERROR: the given path is not a folder: <the file>`.
- **`info_version`** — one line, `folder_remove_empty version 0.5.20260923194832`.
- **`info_help`** — the usage text, byte for byte the same text
  `unknown_option` appends after its error line.
- **`info_print_man`** — the roff man page; the version string appears in its
  `.TH` line, so it moves with the version of the binary that printed it.
- **`info_print_tldr`** — the markdown tldr page.

## Residual trees

Real listings (modes, types, paths relative to the tree root) of each case tree
after its own run, taken by rerunning the same command on a fresh copy:

`terminal_run`, `terminal_verbose`, `no_color` leave:

```text
-rw-r--r-- f withfile/note.txt
dr-xr-xr-x d readonly
drwxr-xr-x d .cache
drwxr-xr-x d 2026-09-23_backup
drwxr-xr-x d ZZZZ-old
drwxr-xr-x d data !!! missing !!! here
drwxr-xr-x d readonly/inner
drwxr-xr-x d symlink_holder
drwxr-xr-x d withfile
lrwxrwxrwx l symlink_holder/link_to_target
link symlink_holder/link_to_target -> target
```

`env_excludes` leaves the same plus `drwxr-xr-x d keep-me`. `terminal_dry_run`
leaves the full builder tree, unchanged.

## Comparing a Python run against these files

The captures embed the scratch path `/tmp/fre-ref.E6hTEvVG`. Two ways to use
them:

1. Rebuild the tree of the case at exactly
   `/tmp/fre-ref.E6hTEvVG/<case>/tree` with the builder script above, run the
   Python port with the command of the row, and `diff` the three files — the
   bytes then match except for the removal counter of a run that behaves
   differently.
2. Or let both sides work in their own scratch and normalise the prefix before
   the diff:

   ```bash
   sed 's|/tmp/fre-ref.E6hTEvVG|@SCRATCH@|g' <capture> > <normalised>
   ```

Compare stdout and stderr separately; a missing trailing LF or a line moved
between the streams is a difference. The exit status is the one-digit content
of the `.rc` file.

## Result of the Python comparison (2026-09-27)

The tree builder is committed as `reference/build_tree.sh`, and the comparison
runs automatically as
`tests/folder_remove_empty/test_reference.py::ReferenceFidelityTest::test_every_capture_matches`
(it rebuilds each tree, renders the Go reporter's line shapes, and compares both
streams of `terminal_run`, `terminal_dry_run`, `terminal_verbose` and
`env_excludes` byte for byte after normalising the scratch prefix; it skips for
root, because a root user removes the read-only folder and the refusal case
cannot happen).

First run: **every stdout capture matched immediately**; the only difference sat
in the stderr reason of the one refused removal —

```
Go:     not removed: <tree>/readonly/inner (remove <tree>/readonly/inner: permission denied)
Python: not removed: <tree>/readonly/inner (Permission denied)
```

The engine's `_reason()` was then aligned to the Go shape
(`remove <path>: <strerror>`, lowercase), which makes all four cases identical in
both streams. The reason text is not fixed by `project_specs.md` §4 (`<reason>`
only), so this was a free choice made for byte fidelity — the port keeps the
Go wording on purpose.

The `.rc` files are not asserted yet: the exit status belongs to the command
line and the reporter, which arrive in phase 3.

## Coloured pty captures — `pty_*` (2026-09-27)

The colourless capture above was taken with regular-file redirections, so the
program's colour check (a character device) failed and every label came out
plain. The six `pty_*` cases below were taken with a real pty on **each**
stream, which is what makes the colour branch run; they pin the exact ANSI
bytes a terminal sees and are the reference of phase 3's coloured form.

### Provenance

| Fact | Value |
|---|---|
| Go source | `~/projects/_folder_remove_empty` at `a2f8b9e82c4b6e5ff6a3973e937a0b607f9c4128` — the **same revision** as the colourless capture, dirty in exactly the same way (the same `M`/`??` list as above), untouched by this capture |
| Build command | `cd ~/projects/_folder_remove_empty && GOTOOLCHAIN=auto nice -n 19 ionice -c 3 go build -p 1 -o /tmp/fre-go-pty ./cmd/folder_remove_empty` (`go1.27.1`, one build worker) |
| Binary | `/tmp/fre-go-pty`, sha256 `39f4fe878c35a5f819e96b2e2e77a296c2a4893a335496485b382bbf3453bdde` — **the same sha256 as the binary of the colourless capture**, so the two captures come from the same executable bytes and not merely from the same revision; module `folder_remove_empty/cmd/folder_remove_empty v0.0.0-20260923194927-a2f8b9e82c4b+dirty`, program version `0.5.20260923194832` (the string of `info_version.out`); deleted after the capture |
| User | uid 1000 (`fmann`), not root — the refused-removal case needs that, as above |
| Scratch root | `/tmp/fre-pty.GMLIjB`, `mktemp -d`, five trees built by `reference/build_tree.sh`, deleted after the capture |
| Capture environment | the shell that ran this capture had `NO_COLOR=1` set globally; every case that does not set the variable itself ran with `NO_COLOR` **and** `FOLDER_REMOVE_EMPTY_EXCLUDE` removed from the environment (the equivalent of the earlier `env -u`), so the captures do not depend on the shell that made them |

### How a capture was taken

Two masters and two slaves: `pty.openpty()` twice, the two slave fds handed to
the child as `stdout` and `stderr` (`stdin=DEVNULL`), both masters read to EOF;
`subprocess.Popen` runs in the scratch root. The exit status goes to
`<case>.rc` as before.

```python
m_out, s_out = pty.openpty()          # stdout stream
m_err, s_err = pty.openpty()          # stderr stream
for fd in (s_out, s_err):
    attrs = termios.tcgetattr(fd)
    attrs[1] &= ~termios.OPOST        # keep the program's LF bytes as they are
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
proc = subprocess.Popen([BIN, *argv], stdout=s_out, stderr=s_err,
                        stdin=subprocess.DEVNULL, env=env, cwd=SCRATCH)
# then a select() loop reads each master into its own buffer until EOF/EIO,
# and proc.wait() gives the status
```

- **One pty per stream, never one for both.** A single pty would merge stdout
  and stderr into one byte stream and lose the split — `script` does exactly
  that, so `script` was not used for the capture itself.
- **`OPOST` is cleared on both slaves.** A tty in its default line discipline
  turns every LF the program writes into CRLF; with `OPOST` off the files hold
  exactly the bytes the program wrote: LF and no CR. Checked by hand on a fresh
  tree: with the default termios the first stdout line reads
  `b'\x1b[32mremoved:\x1b[0m …/.cache/inner\r\n'`, with `OPOST` cleared it reads
  `b'\x1b[32mremoved:\x1b[0m …/.cache/inner\n'`.
- The child still sees a **character device** on both streams, which is the
  only thing the colour check looks at (`colorCode` in `reporter.go`); nothing
  else about the pty matters to the program.
- Both masters hit EOF/EIO only after the child closed its two descriptors, so
  no byte of either stream is cut off.

### The cases

`SCRATCH` below is `/tmp/fre-pty.GMLIjB`; `$T` is the tree of the row; the
binary is `/tmp/fre-go-pty` and the working directory of every call is the
scratch root. `env -u X` on a name that is not set is a no-op, as before.

| Case | Exact command | rc | `.out`/`.err` bytes |
|---|---|---|---|
| `pty_run` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go-pty --no-gui "$SCRATCH/pty_run/tree"` | 0 | 874 / 256 |
| `pty_dry_run` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go-pty --no-gui --dry-run "$SCRATCH/pty_dry_run/tree"` | 0 | 763 / 101 |
| `pty_verbose` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go-pty --no-gui --verbose "$SCRATCH/pty_verbose/tree"` | 0 | 926 / 544 |
| `pty_env_excludes` | `env -u NO_COLOR FOLDER_REMOVE_EMPTY_EXCLUDE='keep-*' /tmp/fre-go-pty --no-gui "$SCRATCH/pty_env_excludes/tree"` | 0 | 923 / 292 |
| `pty_error` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE -u NO_COLOR /tmp/fre-go-pty --no-gui --bogus` | 1 | 0 / 2401 |
| `pty_no_color` | `env -u FOLDER_REMOVE_EMPTY_EXCLUDE NO_COLOR=1 /tmp/fre-go-pty --no-gui "$SCRATCH/pty_no_color/tree"` | 0 | 822 / 267 |

One fresh tree per mutating case, exactly as in the colourless capture:

| Case | Tree (below the scratch root) | Mutated by its own run |
|---|---|---|
| `pty_run`, `pty_verbose`, `pty_env_excludes`, `pty_no_color` | `<case>/tree` | yes — 13 folders removed and 1 refused, except `pty_env_excludes` (12 removed, `keep-me` kept) |
| `pty_dry_run` | `pty_dry_run/tree` | no — verified by comparing a full `path/kind/mode` listing before and after: identical |
| `pty_error` | none | no — refused at the command line |

The residual trees are the ones documented above: `pty_run`, `pty_verbose` and
`pty_no_color` leave the same set as `terminal_run`, `pty_env_excludes` leaves
it plus `keep-me`, and `pty_dry_run` leaves the builder tree untouched.

### The escape bytes, and how to read the files

The `.out`/`.err` files of this group hold **literal ESC bytes (0x1b)** where
the program wrote them — the bytes are raw, nothing is escaped in the file
itself. Human-readable renderings:

| Renderer | What a painted stdout line looks like |
|---|---|
| `cat -v` | `^[[32mremoved:^[[0m /tmp/fre-pty.GMLIjB/pty_run/tree/.cache/inner` |
| `sed -n l` | `\033[32mremoved:\033[0m …` (long lines are folded with a trailing `\`) |
| `od -An -tx1` | `1b 5b 33 32 6d` before the label, `1b 5b 30 6d` after it |
| `python3 -c "print(repr(open(F,'rb').read()))"` | `b'\x1b[32mremoved:\x1b[0m …\n'` |

| Sequence | Bytes | Paints | Painted text | Stream |
|---|---|---|---|---|
| `ansiGreen` `\033[32m` | `1b 5b 33 32 6d` | green | the `removed:` label | stdout |
| `ansiYellow` `\033[33m` | `1b 5b 33 33 6d` | yellow | the `not removed:` label | stderr |
| `ansiRed` `\033[31m` | `1b 5b 33 31 6d` | red | the `ERROR:` label | stderr |
| `ansiOff` `\033[0m` | `1b 5b 30 6d` | — | closes every coloured run | both |

**The colour wraps only the label, never the whole line and never the path.**
The shape is `\033[32mremoved:\033[0m <absolute path>` — the escape comes
before the label, the `ansiOff` right after it, then a plain space and the
path. The exact first stdout line of `pty_run` is

```text
1b 5b 33 32 6d  "removed:"  1b 5b 30 6d  20  <path>  0a
```

and the exact painted stderr line of `pty_run` is

```text
\033[33mnot removed:\033[0m <tree>/readonly/inner (remove <tree>/readonly/inner: permission denied)\n
```

Lines that carry no label stay plain: `path exists:`, `start folder:`,
`excluded, kept:`, both counters, the bare paths of a dry run and the whole
usage text hold no ESC byte at all.

Counts of ESC bytes (`grep -c $'\x1b'` counts *lines*, the table counts
*bytes*):

| Case | ESC bytes in `.out` | ESC bytes in `.err` | CR bytes |
|---|---|---|---|
| `pty_run` | 26 (13 painted labels × 2) | 2 (1 painted label) | 0 / 0 |
| `pty_dry_run` | **0** | 0 | 0 / 0 |
| `pty_verbose` | 26 | 2 | 0 / 0 |
| `pty_env_excludes` | 24 (12 painted labels × 2) | 2 | 0 / 0 |
| `pty_error` | 0 (stdout empty) | 2 | 0 / 0 |
| `pty_no_color` | **0** | 0 | 0 / 0 |

### What each pty case shows

- **`pty_run`** — the `terminal_run` shapes with the labels painted: 13 green
  `removed:` lines on stdout (only the labels coloured) and the closing
  `13 empty folder(s) removed`; stderr is `path exists:`/`start folder:`, the
  one yellow `not removed: …/readonly/inner (remove …: permission denied)`, and
  `1 folder(s) kept`. Strip the ESC bytes and normalise the scratch prefix and
  this file equals `terminal_run.out`, except that its case directory is called
  `pty_run` instead of `terminal_run` and its scratch path is two bytes shorter.
  That is where the size difference comes from: `874 = 848 − 13·7 + 13·9`, the
  seven byte shorter path on each of the 13 lines against the 9 bytes of escape
  each line gains.
- **`pty_dry_run`** — 15 bare absolute paths on stdout with no label and no
  closing counter, `path exists:`/`start folder:` on stderr, and **not one ESC
  byte in either stream**, because the dry-run branch prints the folder without
  `paint()`. A dry run therefore needs no colour handling at all.
- **`pty_verbose`** — stdout as `pty_run`; stderr gains the four
  `excluded, kept: <abs>` lines of `terminal_verbose`, and these stay **plain**:
  the kept branch has no colour, so the counts of ESC bytes equal `pty_run`'s.
- **`pty_env_excludes`** — 12 green `removed:` lines (no `keep-me` line: it is
  kept by the pattern), so 24 ESC bytes; stderr as `pty_run`.
- **`pty_error`** — stdout is an empty file; stderr starts with
  `\033[31mERROR:\033[0m unknown option: --bogus\n` (the red label, then plain
  text) followed by the whole usage text unpainted; rc 1.
- **`pty_no_color`** — a real tty on both streams and `NO_COLOR=1`: **no ESC
  byte at all** in either stream, while the shapes and the counters are exactly
  `pty_run`'s (`removed:` plain on all 13 lines, `not removed:` plain, rc 0).
  With a tty the variable does change the bytes, which is what this case adds
  to `no_color` above (where the streams were files and the variable changed
  nothing).

### Checking these files without a pty

Both streams can be compared against the colourless captures after removing the
colour: strip `\033[32m`, `\033[33m`, `\033[31m` and `\033[0m` and normalise the
scratch prefix, then only the case directory name differs (`pty_run` against
`terminal_run`).

```bash
sed -e 's|/tmp/fre-pty.GMLIjB|@SCRATCH@|g' -e 's/\x1b\[[0-9;]*m//g' pty_run.out
```

`grep -c $'\x1b' pty_dry_run.out pty_no_color.out` must print `0` for both: the
dry run and the `NO_COLOR` run are the two cases that carry no escapes at all.

