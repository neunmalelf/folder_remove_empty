"""the terminal front end of folder_remove_empty: the reporter and its colours.

A port of reporter.go. The removed folders go to stdout, every note, kept and
refused folder to stderr; a dry run prints the plain folder paths instead of a
report, and a colour appears only when the stream is a terminal and NO_COLOR is
empty.
"""

import os
import sys
from collections.abc import Callable
from typing import TextIO

from remove_empty_folder_core import Action, Event, Observer, Options, Summary

# the ANSI colours of the report, the ones the shell original used.
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_OFF = "\033[0m"


def color_code(
    stream: TextIO,
    color: str,
    getenv: Callable[[str], str | None] | None = None,
) -> str:
    """report the ANSI colour to use on a stream, or an empty text when it takes none
    usage: color_code <STREAM> <COLOR> [GETENV]
    returns: the colour when the stream is a terminal and NO_COLOR is empty, else ""

    example: color_code(sys.stdout, ANSI_GREEN)

    """
    if getenv is None:
        getenv = os.environ.get
    if getenv("NO_COLOR"):
        return ""
    isatty = getattr(stream, "isatty", None)
    if isatty is None or not isatty():
        return ""
    return color


def paint(
    stream: TextIO,
    color: str,
    text: str,
    getenv: Callable[[str], str | None] | None = None,
) -> str:
    """wrap a label in an ANSI colour when the stream takes colours
    usage: paint <STREAM> <COLOR> <TEXT> [GETENV]
    returns: the text, coloured and closed again on a terminal, unchanged otherwise

    example: paint(sys.stdout, ANSI_GREEN, "removed:")

    """
    on = color_code(stream, color, getenv)
    if not on:
        return text
    return on + text + ANSI_OFF


class TerminalReporter(Observer):
    """write the progress of a run to the terminal, removed folders on stdout
    usage: TerminalReporter <OPTIONS> [OUT] [ERR] [GETENV]
    returns: the reporter of one run

    example: TerminalReporter(Options(no_gui=True))

    """

    def __init__(
        self,
        options: Options,
        out: TextIO | None = None,
        err: TextIO | None = None,
        getenv: Callable[[str], str | None] | None = None,
    ) -> None:
        """bind the reporter to the two streams, resolving the defaults at call time
        usage: TerminalReporter __init__ <OPTIONS> [OUT] [ERR] [GETENV]
        returns: nothing

        example: TerminalReporter(Options(), out=sys.stdout, err=sys.stderr)

        """
        self.options = options
        self.out = sys.stdout if out is None else out
        self.err = sys.stderr if err is None else err
        self.getenv = os.environ.get if getenv is None else getenv

    def start(self, start_path: str) -> None:
        """report the checked path and the start folder before the first folder
        usage: start <START_PATH>
        returns: nothing

        example: reporter.start("/data/archive")

        """
        if self.options.start_path:
            print(f"path exists: {start_path}", file=self.err)
        print(f"start folder: {start_path}", file=self.err)

    def current(self, folder: str) -> None:
        """do nothing: the terminal report names a folder once it is done
        usage: current <FOLDER>
        returns: nothing

        example: reporter.current("/data/archive/a")

        """
        return None

    def done(self, event: Event) -> None:
        """report one outcome, the shape and the stream depending on it
        usage: done <EVENT>
        returns: nothing

        example: reporter.done(Event("/data/archive/a", Action.REMOVED))

        """
        if event.action is Action.REMOVED:
            if event.dry_run:
                # a dry run prints the plain folder, as the shell original did
                print(event.folder, file=self.out)
                return None
            label = "removed:"
            rest = event.text().removeprefix(label)
            print(paint(self.out, ANSI_GREEN, label, self.getenv) + rest, file=self.out)
            return None
        if event.action is Action.FAILED:
            label = "not removed:"
            rest = event.text().removeprefix(label)
            print(paint(self.err, ANSI_YELLOW, label, self.getenv) + rest, file=self.err)
            return None
        print(event.text(), file=self.err)
        return None

    def summary(self, summary: Summary) -> None:
        """report the closing counters of a run, and nothing for a dry run
        usage: summary <SUMMARY>
        returns: nothing

        example: reporter.summary(Summary(start_path="/data/archive", removed=3))

        """
        if summary.dry_run:
            return None
        if summary.removed == 0:
            print("no empty folder found", file=self.out)
        else:
            print(f"{summary.removed} empty folder(s) removed", file=self.out)
        if summary.failed:
            print(f"{summary.failed} folder(s) kept", file=self.err)
        return None

    def checkpoint(self) -> bool:
        """let the run continue: the terminal front end cannot pause or stop
        usage: checkpoint
        returns: True, always

        example: reporter.checkpoint()

        """
        return True
