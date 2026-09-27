"""version identity of folder_remove_empty.

The stamp is the UTC output of ~/sbin/timestamp (YYYYMMDDhhmmss) with the
trailing Z the repository convention asks for. It lives here once:

- `__VERSION__` is the repository stamp; `_check_version` reads it and the
  tests assert its shape;
- `__version__` is the same stamp without the Z, because PEP 440 forbids a
  trailing letter and the packaging layer (setuptools, read through
  `[tool.setuptools.dynamic]`) refuses `1.0.20260927111114Z`.

tests/folder_remove_empty/test_version.py fails when the two drift apart.
"""

__VERSION__ = "1.0.20260927131905Z"
__version__ = __VERSION__.removesuffix("Z")
APP_NAME = "folder_remove_empty"
APP_NAME_VERBOSE = "FOLDER_REMOVE_EMPTY"


def version_banner() -> str:
    """build the one-line version banner printed by --version
    usage: version_banner
    returns: "<app name> version <stamp>"

    example: version_banner()

    """
    return APP_NAME + " version " + __VERSION__
