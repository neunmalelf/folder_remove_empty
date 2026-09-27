"""the private-display policy that keeps automation off the screen you work on.

Opening a tkinter window on the session display takes the focus and flashes the
whole desktop, so every test, check and script that opens the window does it on
a private Xvfb display. Only the program itself (`make run`, `_run`, the
installed launcher) and an explicit opt-in use the session display:

    FOLDER_REMOVE_EMPTY_GUI_DISPLAY=session   automation on the session screen

A run knows that it is private either through the marker its wrapper set, or by
comparing its own `DISPLAY` with the session display the wrapper recorded. The
test suite (`tests/folder_remove_empty/gui_display.py`), `make check-gui`,
`make check-313`, the pre-commit `gui` module and `assets/make_screenshots.sh`
all speak this one contract, and a script that would draw on the session display
stops itself with:

    python3 -m remove_empty_folder_display --check [ROLE]
"""

import os
import shlex
import shutil
import subprocess
import sys
from collections.abc import Sequence

# "session" opts into the screen the user is sitting in front of
POLICY = "FOLDER_REMOVE_EMPTY_GUI_DISPLAY"
SESSION_POLICY = "session"
# set by whoever started a private display (a script, the guard test, the hook)
PRIVATE_MARKER = "FOLDER_REMOVE_EMPTY_PRIVATE_DISPLAY"
# set by the private run to record the display it was given
DISPLAY_MARKER = "FOLDER_REMOVE_EMPTY_PRIVATE_DISPLAY_NAME"
# set by the private run to remember which display the session had, so a caller
# can prove that the window never went there
SESSION_MARKER = "FOLDER_REMOVE_EMPTY_SESSION_DISPLAY"
# the geometry of every private run: the window tests and the screenshots
XVFB_ARGS = ("-a", "--server-args=-screen 0 1280x1024x24")


def xvfb_run() -> str | None:
    """report the path of xvfb-run
    usage: xvfb_run
    returns: the path of xvfb-run, or None when it is not installed

    example: xvfb_run()

    """
    return shutil.which("xvfb-run")


def session_wanted() -> bool:
    """report whether the session display was asked for by name
    usage: session_wanted
    returns: True when FOLDER_REMOVE_EMPTY_GUI_DISPLAY is "session"

    example: session_wanted()

    """
    return os.environ.get(POLICY) == SESSION_POLICY


def marked_private() -> bool:
    """report whether a wrapper marked this run as private
    usage: marked_private
    returns: True when FOLDER_REMOVE_EMPTY_PRIVATE_DISPLAY is "1"

    example: marked_private()

    """
    return os.environ.get(PRIVATE_MARKER) == "1"


def session_display() -> str | None:
    """report the display the user is working on
    usage: session_display
    returns: the recorded session display, else the current DISPLAY, else None

    example: session_display()

    """
    recorded = os.environ.get(SESSION_MARKER)
    return recorded if recorded else os.environ.get("DISPLAY")


def private_display_name() -> str | None:
    """report the display this run draws on when it is a private one
    usage: private_display_name
    returns: the recorded private display or "private", or None when the run is
             not marked private

    example: private_display_name()

    """
    if not marked_private():
        return None
    return os.environ.get(DISPLAY_MARKER) or os.environ.get("DISPLAY") or "private"


def display_is_private() -> bool:
    """report whether this process draws on a private display
    usage: display_is_private
    returns: True when the run is marked private or its DISPLAY differs from the
             recorded session display

    example: display_is_private()

    """
    if session_wanted():
        return False
    if marked_private():
        return True
    recorded = os.environ.get(SESSION_MARKER)
    current = os.environ.get("DISPLAY")
    return recorded is not None and current != recorded


def private_display_wanted() -> bool:
    """report whether a run should move to a private display first
    usage: private_display_wanted
    returns: True when xvfb-run is available, the session display is not asked
             for and this run is not private already

    example: private_display_wanted()

    """
    return bool(xvfb_run()) and not marked_private() and not session_wanted()


def require_private_display(role: str = "automation") -> None:
    """stop a script that would draw on the screen the user is working on
    usage: require_private_display [ROLE]
    returns: None when the run is private or the session display was asked for
    raises: SystemExit(1) with the reason, so a script fails instead of flashing
            the desktop

    example: require_private_display("make_screenshots.sh")

    """
    if display_is_private() or session_wanted():
        return
    name = session_display() or "the session display"
    print(
        f"{role}: refusing to open a window on {name} - automation uses a private display.\n"
        f"{role}: wrap the command in 'xvfb-run -a' (or export "
        f"{POLICY}={SESSION_POLICY} to ask for the session screen).",
        file=sys.stderr,
    )
    raise SystemExit(1)


def private_environment() -> dict[str, str]:
    """build the environment of a run that is moved to a private display
    usage: private_environment
    returns: the environment with the private marker, the private display name,
             the recorded session display and without DISPLAY

    example: private_environment()

    """
    environment = dict(os.environ, **{PRIVATE_MARKER: "1"})
    environment[DISPLAY_MARKER] = "private"
    session = os.environ.get("DISPLAY")
    if session is not None:
        environment[SESSION_MARKER] = session
    environment.pop("DISPLAY", None)
    return environment


def wrap_command(argv: Sequence[str]) -> list[str]:
    """build the command line that runs a program on a private display
    usage: wrap_command <ARGV>
    returns: xvfb-run plus the command, or the command itself when this run is
             private already, the session display was asked for or xvfb-run is
             not installed

    example: wrap_command(["python3", "your_check.py"])

    """
    runner = xvfb_run()
    if display_is_private() or session_wanted() or runner is None:
        return list(argv)
    return [runner, *XVFB_ARGS, *argv]


def run_wrapped(argv: Sequence[str]) -> int:
    """run a command on a private display and report its exit status
    usage: run_wrapped <ARGV>
    returns: the exit status of the command, 2 when no command was given

    example: run_wrapped(["python3", "your_check.py"])

    """
    if not argv:
        print("remove_empty_folder_display: --wrap needs a command", file=sys.stderr)
        return 2
    command = wrap_command(argv)
    if command == list(argv):
        return subprocess.run(command).returncode
    return subprocess.run(command, env=private_environment()).returncode


def run_under_xvfb(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """run a command on a fresh private Xvfb display
    usage: run_under_xvfb <ARGV>
    returns: the completed process of the private run
    raises: AssertionError when xvfb-run is not installed

    example: run_under_xvfb([sys.executable, "-m", "pytest", "-q", "tests/..."])

    """
    environment = private_environment()
    runner = xvfb_run()
    assert runner is not None, "xvfb-run is not installed"
    return subprocess.run(
        [runner, *XVFB_ARGS, *argv],
        capture_output=True,
        text=True,
        env=environment,
        cwd=os.getcwd(),
    )


def describe() -> str:
    """report where this run would open a window
    usage: describe
    returns: one line naming the private display, the session display or "no display"

    example: describe()

    """
    name = private_display_name()
    if name:
        return f"private display {name}"
    display = os.environ.get("DISPLAY")
    if session_wanted():
        return f"session display {display} (asked for by {POLICY}={SESSION_POLICY})"
    if display:
        return f"session display {display}"
    return "no display"


def usage() -> str:
    """build the module help text
    usage: usage
    returns: the help text of `python3 -m remove_empty_folder_display`

    example: print(usage())

    """
    return f"""remove_empty_folder_display - where automation may open the window

usage: python3 -m remove_empty_folder_display [OPTIONS]

options:
  -h, --help    show this help and exit
  --check       exit 0 when this run is private (or the session display was
                asked for), else print the reason and exit 1
  --print       print where this run would open a window and exit
  --wrap CMD    run CMD on a private display (xvfb-run; it inherits the markers
                and its exit status is returned)
  --wrap --print CMD
                print that command line instead of running it
  --wrap-sh SNIPPET
                run SNIPPET through 'sh -c' on a private display, for a
                pipeline; --wrap-sh --print prints the command line

environment:
  {POLICY}=session                    open on the session display (default: never)
  {PRIVATE_MARKER}=1                  this run is already private
  {DISPLAY_MARKER}                    the display the private run was given
  {SESSION_MARKER}                    the display the session had"""


def main(argv: Sequence[str] | None = None) -> int:
    """run the command line of the display policy
    usage: main [ARGV]
    returns: the exit status: 0 private or asked for, 1 not private, 2 usage,
             else the status of the wrapped command

    example: main(["--check"])

    """
    arguments = list(argv if argv is not None else sys.argv[1:])
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument in ("-h", "--help"):
            print(usage())
            return 0
        if argument == "--print":
            print(describe())
            return 0
        if argument == "--check":
            try:
                require_private_display("remove_empty_folder_display --check")
            except SystemExit as status:
                return int(status.code or 1)
            return 0
        if argument in ("--wrap", "--wrap-sh"):
            rest = arguments[index + 1 :]
            printing = rest[:1] == ["--print"]
            if printing:
                rest = rest[1:]
            if argument == "--wrap-sh":
                if not rest:
                    print("remove_empty_folder_display: --wrap-sh needs a snippet", file=sys.stderr)
                    return 2
                rest = ["sh", "-c", " ".join(rest)]
            if printing:
                print(shlex.join(wrap_command(rest)))
                return 0
            return run_wrapped(rest)
        print(f"remove_empty_folder_display: unknown option {argument!r}")
        return 2
    print(usage())
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
