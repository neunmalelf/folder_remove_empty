"""the generated documentation of folder_remove_empty: the man page and the tldr page.

A port of man.go and tldr.go. Both pages are built from the same facts the
`usage()` help text carries, so the man page, the tldr page and `--help` name
the same program, the same options and the same environment variable and
cannot drift apart. The module imports no tkinter, no argparse and no sys.
"""

from remove_empty_folder_core import ENV_EXCLUDES
from remove_empty_folder_version import __VERSION__, APP_NAME, APP_NAME_VERBOSE

# the tldr examples, in the order they are shown: the description line and the
# command that does the job. The commands carry the backticks in the page, not
# here, because the page format owns them.
TLD_EXAMPLES: list[tuple[str, str]] = [
    (
        "Remove the empty folders below the current folder, in the window:",
        APP_NAME,
    ),
    (
        "Remove them on the terminal, with every removed folder named:",
        APP_NAME + " --no-gui /data/archive",
    ),
    (
        "Look first, remove nothing:",
        APP_NAME + " --dry-run --verbose /data/archive",
    ),
    (
        "Report every kept folder that was left in place:",
        APP_NAME + " --verbose /data/archive",
    ),
    (
        "Keep every folder whose name matches an extra pattern as well:",
        ENV_EXCLUDES + "='keep-*:downloads*' " + APP_NAME + " --no-gui /data/archive",
    ),
    (
        "Print the usage text:",
        APP_NAME + " --help",
    ),
    (
        "Print the version:",
        APP_NAME + " --version",
    ),
    (
        "Read the exit code of a refused path:",
        APP_NAME + " --no-gui /data/does-not-exist; echo $?",
    ),
]


def man_page() -> str:
    r"""build the roff man page when --print-man asks for it
    usage: man_page
    returns: the roff man page as one string, ending in a newline

    example: man_page()

    """
    return rf""".TH {APP_NAME_VERBOSE} 1 "{__VERSION__}" "{__VERSION__}" "User Commands"
.SH NAME
{APP_NAME} \- remove every empty folder below a start folder
.SH SYNOPSIS
.B {APP_NAME}
[\fIoptions\fR] [\fIpath\fR]
.SH DESCRIPTION
.B {APP_NAME}
removes every empty folder below a start folder, deepest first. The start
folder itself is never removed, only the folders below it.
.PP
A folder is empty when it holds no file, no link and no subfolder that is not
empty itself. The folders are rated bottom up, so one run removes a whole chain
of nested empty folders: a folder is removed as soon as its last empty
subfolder is gone. Removing a folder with
.BR rmdir (1)
never touches content, and a folder that is not empty is refused.
.PP
Without arguments the program opens a window that shows the start path with its
check, the options as check boxes and the folder that is worked on right now,
and lists every folder the run worked on in a history. With
.B \-\-no\-gui
the run works on the terminal instead, like the shell original did.
.PP
A given
.I path
must exist and must be a folder. It is made absolute before the run, so the
report and the history name the folder in full.
.SH OPTIONS
.TP
\fB\-d\fR, \fB\-\-dryrun\fR
Print the folders that would be removed and remove nothing.
.TP
\fB\-v\fR, \fB\-\-verbose\fR
Report every kept folder that was left in place.
.TP
\fB\-\-no\-gui\fR
Work on the terminal instead of opening the window.
.TP
\fB\-\-print\-man\fR
Print this man page and exit.
.TP
\fB\-\-print\-tldr\fR
Print the tldr page and exit.
.TP
\fB\-\-version\fR
Print the program version and exit.
.TP
\fB\-h\fR, \fB\-\-help\fR
Print the usage text and exit.
.SH THE WINDOW
.TP
\fBStart path\fR
The folder to scan. It is checked as you type: the line below the field names
the absolute folder or the reason it cannot be used. Without a path the current
folder is used. The button behind the field asks for a folder instead of making
the path be typed.
.TP
\fBDry run\fR, \fBVerbose\fR
The options \fB\-d\fR and \fB\-v\fR.
.TP
\fBExtra excludes\fR
Folder names that are never removed, ':' separated. A name that ends with '*'
keeps every name that starts with it.
.TP
\fBShow in history\fR
Which outcomes the history lists, and which it leaves out.
.TP
\fBHelp\fR
Show the usage text in a dialog that scrolls.
.TP
\fBLight mode\fR, \fBDark mode\fR
Switch the window between the light and the dark theme. The button names the
theme it switches to; the foreground, the background and the control borders
follow the switch. The window starts in the variant the desktop asks for.
.TP
\fBExit\fR
Close the window. A run in flight is stopped.
.TP
\fBPause\fR
Hold the run in front of the next folder. The button turns into
.B Resume
while the run is held.
.TP
\fB(Re)start\fR
Start the job. While a run is in flight the button stops it and starts the job
over with the settings of the fields.
.TP
\fBCurrent folder\fR
The folder that is rated or removed right now.
.TP
\fBHistory\fR
Every folder this session worked on, with its outcome.
.PP
The window carries the app icon, a purple rectangle with the white letters "fr",
in the sizes a desktop asks for; \fBmake install\fR copies them below
\fI~/.local/share/icons/hicolor\fR.
.SH KEPT FOLDERS
Never removed: \fB.Trash\-1000\fR, \fB.cache\fR, \fBSystem Volume Information\fR
and \fB$RECYCLE.BIN\fR (with or without the leading dot), every name that
starts with \fBZZZZ\fR, every name that starts with four digits and every name
that holds "!!! MISSING !!!" in any letter case.
.PP
The empty subfolders of a kept folder are still removed. The kept folder itself
stays, also when it is empty then, unless its parent is empty apart from empty
kept folders: then it goes with the parent.
.SH ENVIRONMENT
.TP
\fB{ENV_EXCLUDES}\fR
Extra folder names that are never removed, ':' separated. A name that ends with
'*' keeps every name that starts with it.
.TP
\fBNO_COLOR\fR
A non-empty value switches the colors of the terminal report off.
.SH EXIT STATUS
.TP
\fB0\fR
The job ran to its end, or a help, man, tldr or version output was asked for.
.TP
\fB1\fR
The given path does not exist, is not a folder, or an option is unknown.
.SH EXAMPLES
Remove the empty folders below the current folder, in the window:
.PP
.nf
{APP_NAME}
.fi
.PP
Remove them on the terminal, naming every folder that goes:
.PP
.nf
{APP_NAME} \-\-no\-gui /data/archive
.fi
.PP
Look first, remove nothing:
.PP
.nf
{APP_NAME} \-d \-v /data/archive
.fi
.PP
Keep every folder whose name starts with "keep\-" as well:
.PP
.nf
{ENV_EXCLUDES}='keep\-*:downloads*' {APP_NAME} \-v \-\-no\-gui /data/archive
.fi
.SH SEE ALSO
.BR rmdir (1),
.BR find (1)
.PP
The program is the Python port of the shell script
.B _folder_remove_empty
(version 0.6.20260923165923), which it replaced.
"""


# the commands of the tldr page carry the backticks on purpose. tealdeer 1.7.3
# renders a bare indented command as nothing at all, so a page without them
# shows its descriptions and drops every command.
def tldr_page() -> str:
    """build the markdown tldr page when --print-tldr asks for it
    usage: tldr_page
    returns: the tldr page as one string, ending in a newline

    example: tldr_page()

    """
    page = "# " + APP_NAME + "\n\n"
    page += "> Remove every empty folder below a start folder, deepest first.\n"
    page += "> The start folder itself is never removed, only the folders below it.\n"
    page += "> More information: <https://github.com/neunmalelf/folder_remove_empty>.\n"

    for description, command in TLD_EXAMPLES:
        page += "\n- " + description + "\n\n  `" + command + "`\n"

    return page
