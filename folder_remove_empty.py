"""command line entry point of folder_remove_empty.

Phase 1 of the plan (todo/goal.md) ships only the version output, so the
package installs and `folder_remove_empty --version` answers. The command
line parser (phase 3), the terminal front end (phase 3) and the tkinter
window (phase 5) follow in their phases.
"""

import sys
from collections.abc import Callable
from typing import TextIO

from remove_empty_folder_version import version_banner


def main(
    argv: list[str] | None = None,
    out: TextIO | None = None,
    err: TextIO | None = None,
    getenv: Callable[[str], str | None] | None = None,
) -> int:
    """run one invocation of the program, the version output first
    usage: main [ARGV] [OUT] [ERR] [GETENV]
    returns: the exit code, 0 when the version banner was printed

    example: main(["--version"])

    """
    if argv is None:
        argv = sys.argv[1:]
    if out is None:
        out = sys.stdout

    if "--version" in argv:
        print(version_banner(), file=out)
        return 0

    raise NotImplementedError("the window and the terminal mode are phases 2-5 of todo/goal.md")


if __name__ == "__main__":
    raise SystemExit(main())
