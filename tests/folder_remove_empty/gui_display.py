"""the display policy of the window tests: never the session screen.

The contract lives in `remove_empty_folder_display.py` (the module the scripts,
`make check-gui` and `make check-313` use too); this module adds the two things
only a test run needs: the tkinter probe that tells whether a window can be
opened here at all, and the skip pair for the window test classes.

    FOLDER_REMOVE_EMPTY_GUI_DISPLAY=session   run on the screen you are sitting in front of

The private child is marked with `FOLDER_REMOVE_EMPTY_PRIVATE_DISPLAY=1` so a
test run that already sits on a private display does not start another one.
Without `xvfb-run` the tests fall back to the session display and say so, or
skip when there is no display at all.
"""

from remove_empty_folder_display import (
    DISPLAY_MARKER,
    POLICY,
    PRIVATE_MARKER,
    SESSION_MARKER,
    marked_private,
    private_display_wanted,
    run_under_xvfb,
    session_wanted,
    xvfb_run,
)

XVFB_RUN = xvfb_run()
PRIVATE = marked_private()
SESSION_WANTED = session_wanted()


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


__all__ = [
    "DISPLAY_MARKER",
    "NO_WINDOW",
    "POLICY",
    "PRIVATE",
    "PRIVATE_MARKER",
    "REFUSAL",
    "SESSION_MARKER",
    "SESSION_WANTED",
    "XVFB_RUN",
    "private_display_wanted",
    "run_under_xvfb",
    "skip_arguments",
    "window_refusal",
]
