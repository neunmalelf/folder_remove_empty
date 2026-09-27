# Window tests and your screen

This page is the long form of the *Window tests and your screen* section of
`README.md`; the policy itself lives in `remove_empty_folder_display.py`.

## Why

Opening a tkinter window on the display you are sitting in front of takes the
keyboard focus away from your work and makes the whole desktop flash while the
window paints. A test suite that does that on every run is unusable, and a
pre-commit hook that does it interrupts you in the middle of a commit. The
window is a test subject, so it belongs on a display of its own.

## The rule

One contract, spoken by every piece of automation:

| where | what happens |
| --- | --- |
| `tests/folder_remove_empty/test_gui.py`, `test_gui_reference.py` | open their windows on a private Xvfb display |
| `test_private_display.py` | is the guard: it re-runs those two modules under `xvfb-run` and asserts the session display was left alone |
| `test_script_display_policy.py` | keeps the repository scripts and the `Makefile` on the same rule |
| `hooks/pre-commit` (`gui` module) | drives the guard, so a commit never flashes the screen |
| `make check-gui` | runs the window checks on a private display by hand |
| `make check-313` | the same, plus the whole suite, on Python 3.13 in a container |
| `assets/make_screenshots.sh` | captures the documentation shots on a private display and refuses to run anywhere else |

Only these places may open the real window: `make run`, `_run`, and `_menu`'s
`r` entry — a human being asked for them.

## What a normal run looks like

```text
$ make test
39 skipped in the parent run            ("the window tests run on a private display")
 1 passed                               (the guard re-ran them under xvfb-run, display :99)
```

The skips are not a gap: the guard test runs the same modules inside a fresh
Xvfb server, and the inner run asserts that its `DISPLAY` differs from the
session display recorded by the guard. A window can therefore only ever appear
on the private server.

## Environment

| variable | meaning |
| --- | --- |
| `FOLDER_REMOVE_EMPTY_GUI_DISPLAY=session` | opt in: run the window tests on the screen you are working on (watch them) |
| `FOLDER_REMOVE_EMPTY_PRIVATE_DISPLAY=1` | set by a wrapper: this run is already private, do not start a second server |
| `FOLDER_REMOVE_EMPTY_PRIVATE_DISPLAY_NAME` | the display the private run was given |
| `FOLDER_REMOVE_EMPTY_SESSION_DISPLAY` | the display the session had, recorded so a caller can prove the window never went there |
| `SKIP_GUI=1` | skip the hook's `gui` module for one commit |

## For a new script

A script that wants to open the window for a check must wrap the command:

```bash
xvfb-run -a --server-args="-screen 0 1280x1024x24" \
    env FOLDER_REMOVE_EMPTY_PRIVATE_DISPLAY=1 python3 your_check.py
```

and it can refuse to run outside a private display:

```bash
python3 -m remove_empty_folder_display --check your_script.sh
```

`--print` reports where the current process would open a window, `--check` exits
1 with the reason when that would be the session display, and `--wrap CMD...`
runs the command on a private display, inheriting the markers and returning its
exit status (`--wrap --print CMD...` prints that command line instead).

One trap: `xvfb-run` re-splits the command it is given, so an inline program
loses its quoting — `python3 -c "print('x')"` arrives as `print(x)`. Pass a
script file (or `--wrap` a file), not a command with quoted arguments. `test_script_display_policy.py`
fails the suite when a new script runs the program without one of the two.

## Without `xvfb-run`

The tests fall back to the session display and say so, or skip when there is no
display at all. Without a display *and* without `xvfb-run` nothing can be
checked: that is the one case where the window tests contribute skips instead of
a result.

`xvfb-run` is Debian's `xvfb` package (`dnf install xorg-x11-server-Xvfb` on
Fedora); the CI installs it for every run.
