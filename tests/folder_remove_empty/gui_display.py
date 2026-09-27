"""the display policy of the window tests: never the session screen.

Opening the window on the session display steals the focus and makes the whole
screen flash, so the window tests (and the pre-commit `gui` module that drives
them) run on a private Xvfb display. The session display is used only when it is
asked for by name:

    FOLDER_REMOVE_EMPTY_GUI_DISPLAY=session   run on the screen you are sitting in front of

The private child is marked with `FOLDER_REMOVE_EMPTY_PRIVATE_DISPLAY=1` so a
test run that already sits on a private display does not start another one.
Without `xvfb-run` the tests fall back to the session display and say so, or
skip when there is no display at all.
"""

import os
import shutil
import subprocess
from collections.abc import Sequence

# set by whoever started a private display (the guard test, the pre-commit hook)
PRIVATE_MARKER = "FOLDER_REMOVE_EMPTY_PRIVATE_DISPLAY"
# set by the private run to record the display it was given
DISPLAY_MARKER = "FOLDER_REMOVE_EMPTY_PRIVATE_DISPLAY_NAME"
# set by the private run to remember which display the session had, so a test
# can assert that the window never went there
SESSION_MARKER = "FOLDER_REMOVE_EMPTY_SESSION_DISPLAY"
# "session" opts into the screen the user is working on
POLICY = "FOLDER_REMOVE_EMPTY_GUI_DISPLAY"

XVFB_RUN = shutil.which("xvfb-run")
PRIVATE = os.environ.get(PRIVATE_MARKER) == "1"
SESSION_WANTED = os.environ.get(POLICY) == "session"
PRIVATE_NAME = os.environ.get(DISPLAY_MARKER)
SESSION_DISPLAY = os.environ.get("DISPLAY")


def window_refusal() -> str | None:
    """report why no window can be opened on the current display
    usage: window_refusal
    returns: the tkinter error text, or None when a root can be opened

    example: window_refusal()

    """
    import tkinter

    try:
        probe = tkinter.Tk()
    except tkinter.TclError as err:
        return str(err)
    probe.destroy()
    return None


REFUSAL = window_refusal()
NO_WINDOW = REFUSAL or "no display"


def private_display_wanted() -> bool:
    """report whether this run should move to a private display first
    usage: private_display_wanted
    returns: True when xvfb-run is available, the session display is not asked
             for and this run is not already private

    example: private_display_wanted()

    """
    return bool(XVFB_RUN) and not PRIVATE and not SESSION_WANTED


def skip_arguments() -> tuple[bool, str]:
    """build the skip condition and its reason for the window test classes
    usage: skip_arguments
    returns: (skip, reason) for unittest.skipIf

    example: @unittest.skipIf(*gui_display.skip_arguments())

    """
    if private_display_wanted():
        return True, "the window tests run on a private display, see gui_display"
    if REFUSAL is not None:
        return True, NO_WINDOW
    return False, ""


def run_under_xvfb(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """run a command on a fresh private Xvfb display
    usage: run_under_xvfb <ARGV>
    returns: the completed process of the private run

    example: run_under_xvfb([sys.executable, "-m", "pytest", "tests/...", "-q"])

    """
    environment = dict(os.environ, **{PRIVATE_MARKER: "1"})
    environment[DISPLAY_MARKER] = "private"
    if SESSION_DISPLAY is not None:
        environment[SESSION_MARKER] = SESSION_DISPLAY
    environment.pop("DISPLAY", None)
    assert XVFB_RUN is not None
    return subprocess.run(
        [XVFB_RUN, "-a", "--server-args=-screen 0 1280x1024x24", *argv],
        capture_output=True,
        text=True,
        env=environment,
        cwd=os.getcwd(),
    )
