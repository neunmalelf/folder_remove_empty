"""the command line of folder_remove_empty: options, usage text and environment.

A port of options.go. The environment is read through an injected `getenv` so a
test never depends on the shell it runs in, and the four informational options
return their command immediately, as the Go original does.
"""

import os
from collections.abc import Callable, Sequence
from enum import IntEnum

from remove_empty_folder_core import ENV_EXCLUDES, FolderRemoveEmptyError, Options
from remove_empty_folder_version import APP_NAME


class Command(IntEnum):
    """what the command line asked the program to do
    usage: Command
    returns: RUN, HELP, VERSION, MAN or TLDR

    example: parse_args(["--version"])[1] is Command.VERSION

    """

    # start the job, in the window or on the terminal.
    RUN = 0
    # print the usage text.
    HELP = 1
    # print the version banner.
    VERSION = 2
    # print the man page.
    MAN = 3
    # print the tldr page.
    TLDR = 4


class UnknownOptionError(FolderRemoveEmptyError):
    """the option the program does not know, which the caller answers with the usage text
    usage: UnknownOptionError <OPTION>
    returns: the exception carrying the refused option

    example: UnknownOptionError("--bogus").option

    """

    def __init__(self, option: str) -> None:
        """record the refused option and build the message the Go tool printed
        usage: UnknownOptionError __init__ <OPTION>
        returns: nothing

        example: UnknownOptionError("--bogus")

        """
        super().__init__(f"unknown option: {option}")
        self.option = option


def new_options(getenv: Callable[[str], str | None] | None = None) -> Options:
    """build the options of a job started without arguments, reading the environment
    usage: new_options [GETENV]
    returns: the Options, with the extra kept names pre-filled from the environment

    example: new_options(lambda name: "keep-*")

    """
    if getenv is None:
        getenv = os.environ.get
    return Options(excludes=getenv(ENV_EXCLUDES) or "")


def parse_args(
    args: Sequence[str],
    getenv: Callable[[str], str | None] | None = None,
) -> tuple[Options, Command]:
    """read the command line and report the options and the command to run
    usage: parse_args <ARGS> [GETENV]
    returns: (Options, Command), or raises UnknownOptionError / FolderRemoveEmptyError

    example: parse_args(["--no-gui", "--dry-run", "/data/archive"])

    """
    options = new_options(getenv)

    for arg in args:
        if arg in ("-d", "--dryrun", "--dry-run"):
            options.dry_run = True
        elif arg in ("-v", "--verbose"):
            options.verbose = True
        elif arg == "--no-gui":
            options.no_gui = True
        elif arg in ("-h", "--help"):
            return options, Command.HELP
        elif arg == "--version":
            return options, Command.VERSION
        elif arg == "--print-man":
            return options, Command.MAN
        elif arg == "--print-tldr":
            return options, Command.TLDR
        elif arg.startswith("-"):
            raise UnknownOptionError(arg)
        elif options.start_path:
            raise FolderRemoveEmptyError(f"only one path is allowed, got: {arg}")
        else:
            options.start_path = arg

    return options, Command.RUN


def usage() -> str:
    """build the usage text of --help and of the help dialog
    usage: usage
    returns: the usage text, byte for byte the one the Go tool printed

    example: print(usage())

    """
    return (
        f"Usage: {APP_NAME} [OPTIONS] [PATH]\n"
        "\n"
        "Remove every empty folder below PATH, deepest first. The start folder itself\n"
        "is never removed, only the folders below it. Without arguments the window\n"
        "opens, pre-filled with PATH and the options below.\n"
        "\n"
        "Options:\n"
        "  -d, --dryrun     Print the folders that would be removed and remove nothing\n"
        "  -v, --verbose    Report every kept folder that was left in place\n"
        "      --no-gui     Work on the terminal instead of opening the window\n"
        "      --print-man  Print the man page (roff) and exit\n"
        "      --print-tldr Print the tldr page (markdown) and exit\n"
        "      --version    Print the program version and exit\n"
        "  -h, --help       Print this help and exit\n"
        "\n"
        "Arguments:\n"
        "  PATH             Folder to scan (default: the current folder)\n"
        "\n"
        "The window offers the same settings:\n"
        "  Start path       Folder to scan, checked against the file system as you type;\n"
        "                   the button behind the field asks for a folder\n"
        "  Dry run          The option -d\n"
        "  Verbose          The option -v\n"
        "  Extra excludes   Folder names that are never removed, ':' separated\n"
        "  Show in history  Which outcomes the history lists\n"
        "  Help             Show this text in a dialog that scrolls\n"
        "  Light/Dark mode  Switch the window between the light and the dark theme\n"
        "  Exit             Close the window, stopping a run in flight\n"
        "  Pause            Hold the run in front of the next folder, Resume lets it go\n"
        "  (Re)start        Start the job, or stop the running one and start it over\n"
        "  Current folder   The folder that is rated or removed right now\n"
        "  History          Every folder this session worked on, with its outcome\n"
        "\n"
        "Kept:\n"
        "  Never removed: .Trash-1000, .cache, System Volume Information, $RECYCLE.BIN\n"
        "  (with or without the leading dot), names starting with ZZZZ, names starting\n"
        '  with four digits and names holding "!!! MISSING !!!" in any letter case.\n'
        "  Their empty subfolders are still removed, the kept folder itself goes only\n"
        "  with a parent that is empty apart from empty kept folders.\n"
        "\n"
        "Environment Variables:\n"
        f"  {ENV_EXCLUDES}   Extra names that are never removed,\n"
        "                           ':' separated, '*' at the end keeps every name that\n"
        "                           starts with it\n"
        "\n"
        "Exit Codes:\n"
        "  0   The job ran to the end (empty folders removed or listed)\n"
        "  1   The given PATH does not exist, is not a folder, or an option is unknown\n"
    )
