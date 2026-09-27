# Security policy

`folder_remove_empty` is a local desktop utility: it removes empty folders
below a start folder the user points it at, and it does nothing else. It has
no network code, no daemon, no service, no plugin surface and no elevated
privileges, so most of the usual attack surface simply does not exist here.
What follows is the scope that does, and how to report a problem in it.

## Supported versions

The `1.0.x` line is supported; the current release is
`v1.0.20260927162713Z`. Older builds are not patched — a fix lands in a new
tag, and that tag carries the rebuilt Nuitka binary and its checksums.
Please report against a current tag if you can.

## What the program does with the file system

- It scans the start folder bottom-up and removes only the folders that scan
  rated empty, with remove-empty-folder semantics — the equivalent of
  `rmdir`, which refuses anything that is not empty.
- Content can therefore never be deleted through this tool: no recursive
  delete, no `unlink`, no overwrite of anything that exists.
- The start folder itself is never removed, unreadable folders are treated
  as non-empty, a refused removal also protects its parent, and `--dry-run`
  changes nothing on disk.

These are the safety guarantees of `project_specs.md` §11, and they are the
contract. A removal of anything that is not a rated-empty folder is a
security bug, and so is any write outside the start folder.

## Reporting a vulnerability

Please **prefer a private security advisory**:
<https://github.com/neunmalelf/folder_remove_empty/security/advisories/new>,
also reachable as *Security → Report a vulnerability* on the repository page.
An advisory keeps the report private until a fix is out. If that form is not
reachable for you, the address the repository's commits are authored with —
`neunmalelf@gmail.com` — works as a plain fallback.

Please include:

- the version, from `folder_remove_empty --version` or the release tag;
- the operating system and how the program runs (Nuitka binary, `pipx`, or a
  `make install` launcher);
- the exact command line, start folder included, and the mode (window or
  `--no-gui`);
- a minimal folder tree that reproduces it: the folders, and what each one
  holds (files, symlinks, permissions), trimmed to the smallest shape that
  still shows the problem;
- what happened, and what you expected to happen.

## Out of scope

- Anything that needs a folder to be unreadable or unwritable to be removed.
  The program refuses such a folder by design and reports it; that is the
  documented behaviour, not a vulnerability.
- Anything that needs a folder with content in it to be removed. The tool
  never does that, and no report can make it.
- Symlink following. The scan uses `lstat` semantics: a link to a folder is a
  link, never the folder behind it, and it is left in place.
- A folder that is gone because the user or another program removed it while
  the run was in progress. A removal refused at that point is reported as
  `not removed: <folder> (<reason>)`, which is the honest outcome.

## Response expectations

There is no bug bounty. This is a single-maintainer utility and responses are
best effort: a report is read and, when it holds, fixed and released in the
next tag. Nothing here is a promise of a response or fix time.
