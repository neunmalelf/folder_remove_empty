# The check machinery

What runs where, and what to run before a push. The display rule that sits under
all of it is in [`window-display.md`](window-display.md).

## One command before a push

```bash
make check-all      # final + check-gui + check-313  (the slow set)
```

| target | what it does | needs |
| --- | --- | --- |
| `make test` | `./_tests`: pytest, then ruff, then mypy | — |
| `make test-quick` | pytest only | — |
| `make final` | `test`, `man`, `tldr`, `pins` — the release check | — |
| `make pins` | `./_check_pins --strict`: fail when the installed dev tools drift from `requirements-dev.txt` | — |
| `make check-gui` | the window checks on a private display (`window_checks.sh --assert-private` through the policy wrapper) | `xvfb-run` for a private display |
| `make check-313` | `final` plus `check-gui` on Python 3.13 in `python:3.13-slim` | podman, network on the first run |
| `make check-all` | `final` + `check-gui` + `check-313` | all of the above |

`make check-gui` honours `FOLDER_REMOVE_EMPTY_GUI_DISPLAY=session`: with it the
window checks run on your own screen instead of a private Xvfb display, which is
how you watch them once (see `window-display.md`).

## The scripts behind the targets

| script | role |
| --- | --- |
| `_tests` | pytest + ruff + mypy, `--quick` for the tests alone |
| `_build` | the Nuitka standalone build, `--package` for the release artifacts, `--release` to also tag and publish |
| `_check_version` | every `__VERSION__` stamp has the `Major.Minor.YYYYMMDDhhmmssZ` shape and was re-stamped by a change |
| `_skill_sync` | the skill index between the markers in `AGENTS.md` |
| `_check_pins` | the dev tools against `requirements-dev.txt` (`--strict` fails, `--update` pins what is installed, `--quiet` says nothing when it matches) |
| `tests/folder_remove_empty/window_checks.sh` | the window test modules, the one place that lists them (`--assert-private` refuses a session display) |

## The pre-commit hook

`hooks/pre-commit` runs the same scripts as modules, plus the window checks:

| module | what it runs | skip with |
| --- | --- | --- |
| `version` | `_check_version` | `SKIP_VERSION=1` |
| `skill_sync` | `_skill_sync --check` | `SKIP_SKILL_SYNC=1` |
| `ruff` | `python3 -m ruff check .` | `SKIP_RUFF=1` |
| `mypy` | `python3 -m mypy` | `SKIP_MYPY=1` |
| `tests` | `./_tests --quick` | `SKIP_TESTS=1` |
| `gui` | `make check-gui` | `SKIP_GUI=1` |
| `docs` | the committed man page and tldr page against the generators | `SKIP_DOCS=1` |
| `pins` | `_check_pins` (warns, never blocks) | `SKIP_PINS=1` |
| `build` | `_build`, only with `PRE_COMMIT_BUILD=1` | `SKIP_BUILD=1` |
| `directory_hooks` | `hooks/pre-commit.d/*.sh` | — |

`SKIP_HOOKS=1` or `git commit --no-verify` bypasses the whole hook. A single
module runs with `hooks/pre-commit --run=<module>`.

## Continuous integration

`.github/workflows/checks.yml` installs the pinned tools from
`requirements-dev.txt` plus the package, with `python3-tk` and `xvfb`, and runs
pytest, ruff and mypy natively on Python 3.13 on every push, pull request and
manual dispatch. `checks` is a required status context on `master` and the README
carries the badge.

CI does **not** run `make check-313`: its interpreter already is 3.13, the
declared floor, so the container target exists for the run *before* a push. The
first CI run paid for itself — it found that the window module could not be
imported on 3.13 at all (`tk.Event[...]` is only subscriptable from 3.14).

## When a check fails

- **pins**: `./_check_pins` names the drifting tools; install the pins
  (`python3 -m pip install -r requirements-dev.txt`) or, after a run you verified,
  re-pin with `./_check_pins --update`.
- **docs**: the committed pages drifted; run `make man` and `make tldr`.
- **gui**: run `make check-gui` and read the failure; with
  `FOLDER_REMOVE_EMPTY_GUI_DISPLAY=session` the window opens on your screen.
- **version**: `./_check_version` prints the file whose stamp is stale; re-stamp
  it from `~/sbin/timestamp`.
