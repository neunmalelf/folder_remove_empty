"""command line entry point of folder_remove_empty.

The port of run.go: it parses the command line, prints the informational
answers and hands a job to the terminal reporter or to the tkinter window of
remove_empty_folder_gui.
"""

import os
import sys
from collections.abc import Callable
from typing import TextIO

from remove_empty_folder_core import FolderRemoveEmptyError, Options, execute
from remove_empty_folder_docs import man_page, tldr_page
from remove_empty_folder_options import (
    Command,
    UnknownOptionError,
    parse_args,
    usage,
)
from remove_empty_folder_report import ANSI_RED, TerminalReporter, paint
from remove_empty_folder_version import version_banner


def main(
    argv: list[str] | None = None,
    out: TextIO | None = None,
    err: TextIO | None = None,
    getenv: Callable[[str], str | None] | None = None,
) -> int:
    """work one invocation of the program and report its exit code
    usage: main [ARGV] [OUT] [ERR] [GETENV]
    returns: 0 when the job ran or an informational output was printed,
             1 when the command line or the start path was refused

    example: main(["--no-gui", "--dry-run", "/data/archive"])

    """
    argv = sys.argv[1:] if argv is None else argv
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err
    getenv = os.environ.get if getenv is None else getenv

    try:
        options, command = parse_args(argv, getenv)
    except UnknownOptionError as refusal:
        print(_error_line(err, refusal, getenv), file=err)
        print(usage(), file=err, end="")
        return 1
    except FolderRemoveEmptyError as refusal:
        print(_error_line(err, refusal, getenv), file=err)
        return 1

    if command is Command.HELP:
        print(usage(), file=out, end="")
        return 0
    if command is Command.VERSION:
        print(version_banner(), file=out)
        return 0
    if command is Command.MAN:
        print(man_page(), file=out, end="")
        return 0
    if command is Command.TLDR:
        print(tldr_page(), file=out, end="")
        return 0

    if options.no_gui:
        return run_terminal(options, out, err, getenv)

    return run_window(options)


def run_terminal(
    options: Options,
    out: TextIO,
    err: TextIO,
    getenv: Callable[[str], str | None],
) -> int:
    """work a job on the terminal, in the shape the Go tool reported it
    usage: run_terminal <OPTIONS> <OUT> <ERR> <GETENV>
    returns: 0 when the job ran to its end, 1 when the start path was refused

    example: run_terminal(Options(no_gui=True), sys.stdout, sys.stderr, os.environ.get)

    """
    try:
        _ = execute(options, TerminalReporter(options, out=out, err=err, getenv=getenv))
    except FolderRemoveEmptyError as refusal:
        print(_error_line(err, refusal, getenv), file=err)
        return 1
    return 0


def run_window(options: Options) -> int:
    """open the window of the program and block until it is closed
    usage: run_window <OPTIONS>
    returns: 0 when the window was closed again

    example: run_window(Options(start_path="/data/archive"))

    """
    # the toolkit is imported here, so the informational options keep working
    # on a machine that carries no tkinter.
    from remove_empty_folder_gui import run_gui

    return run_gui(options)


def _error_line(err: TextIO, refusal: Exception, getenv: Callable[[str], str | None]) -> str:
    """build the one error line of a refused command line or start path
    usage: _error_line <ERR> <REFUSAL> <GETENV>
    returns: the line, red on a terminal and plain otherwise

    example: _error_line(sys.stderr, FolderRemoveEmptyError("nope"), os.environ.get)

    """
    return paint(err, ANSI_RED, "ERROR:", getenv) + f" {refusal}"


if __name__ == "__main__":
    raise SystemExit(main())
