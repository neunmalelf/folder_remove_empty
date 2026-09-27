"""the settings file of folder_remove_empty: the state the window remembers.

The window writes this file on close and both front ends read it as the
lowest-precedence pre-fill, so a command-line option beats a saved value and a
saved value beats the built-in default.

Reading never raises: a missing, unreadable or malformed file yields the
defaults. Writing never raises either, so a settings file that cannot be
written can neither abort a run nor block the close of the window, and the
previous file stays as it was.

The file is INI:

    [window]
    width = 960
    height = 720
    x = -1920
    y = 0

    [options]
    dry_run = False
    verbose = False
    excludes =
    history_filter = All
    dark = False

A geometry that is not complete (all four keys present and whole numbers) is
read as "no geometry saved", never as a half-set window.
"""

import configparser
import os
import tempfile
from dataclasses import dataclass

# the folder and the file the window remembers its state in.
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "folder_remove_empty")
CONFIG_PATH = os.path.join(CONFIG_DIR, "folder_remove_empty.conf")

# the section and the keys of the saved window geometry.
_WINDOW_SECTION = "window"
_GEOMETRY_KEYS = ("width", "height", "x", "y")

# the section of the saved options.
_OPTIONS_SECTION = "options"

# the history filters of the window, spec §9; a saved value outside this list
# is read as "All".
_HISTORY_FILTERS = ("All", "Removed", "Kept", "Not removed")
_HISTORY_FILTER = "history_filter"
_DEFAULT_HISTORY_FILTER = "All"

# the prefix of the temporary file a save writes before it replaces the target.
_TEMP_PREFIX = ".folder_remove_empty-"


@dataclass
class SavedSettings:
    """the state the window remembers between two runs
    usage: SavedSettings([GEOMETRY]) [DRY_RUN] [VERBOSE] [EXCLUDES] [_HISTORY_FILTER] [DARK]
    returns: the saved settings, every field on its built-in default

    example: SavedSettings((960, 720, -1920, 0), dark=True)

    """

    # the saved window geometry (width, height, x, y); None means "not saved".
    geometry: tuple[int, int, int, int] | None = None
    # the state of the dry run switch.
    dry_run: bool = False
    # the state of the verbose switch.
    verbose: bool = False
    # the extra kept names, ':' separated.
    excludes: str = ""
    # the selected history filter.
    history_filter: str = _DEFAULT_HISTORY_FILTER
    # the selected theme; True is the dark one.
    dark: bool = False


def config_path() -> str:
    """return the path of the settings file of this user
    usage: config_path
    returns: CONFIG_PATH, the per-user settings file

    example: config_path()

    """
    return CONFIG_PATH


def load(path: str | None = None) -> SavedSettings:
    """read the settings file when it is present and well-formed, else the defaults
    usage: load [PATH]
    returns: the saved settings; a missing, unreadable or malformed file yields SavedSettings()

    example: load("/home/user/.config/folder_remove_empty/folder_remove_empty.conf")

    """
    settings = SavedSettings()
    try:
        parser = _read(path)
    except (OSError, configparser.Error, ValueError):
        return settings
    window = _section(parser, _WINDOW_SECTION)
    options = _section(parser, _OPTIONS_SECTION)
    settings.geometry = _geometry(window)
    settings.dry_run = _flag(options, "dry_run")
    settings.verbose = _flag(options, "verbose")
    settings.excludes = _text(options, "excludes")
    settings.history_filter = _history_filter(options)
    settings.dark = _flag(options, "dark")
    return settings


def save(settings: SavedSettings, path: str | None = None) -> None:
    """write SETTINGS to the settings file atomically, silently giving up when it cannot be written
    usage: save <SETTINGS> [PATH]
    returns: nothing; an unwritable target leaves the previous file untouched

    example: save(SavedSettings(dry_run=True, dark=True))

    """
    target = config_path() if path is None else path
    directory = os.path.dirname(target) or "."
    temporary = ""
    try:
        fresh = not os.path.isdir(directory)
        os.makedirs(directory, mode=0o700, exist_ok=True)
        if fresh:
            os.chmod(directory, 0o700)
        descriptor, temporary = tempfile.mkstemp(prefix=_TEMP_PREFIX, dir=directory)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            _parser(settings).write(handle)
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
        temporary = ""
    except OSError:
        return
    finally:
        _discard(temporary)


def _read(path: str | None) -> configparser.ConfigParser:
    """parse the settings file, interpolation off so a name with % survives
    usage: _read <PATH>
    returns: the parser carrying the file; raises OSError, configparser.Error or ValueError

    example: _read("/home/user/.config/folder_remove_empty/folder_remove_empty.conf")

    """
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(config_path() if path is None else path, encoding="utf-8")
    return parser


def _parser(settings: SavedSettings) -> configparser.ConfigParser:
    """build the parser that carries every key of SETTINGS
    usage: _parser <SETTINGS>
    returns: the parser a save writes, with the [window] and [options] sections

    example: _parser(SavedSettings((960, 720, 0, 0)))

    """
    parser = configparser.ConfigParser(interpolation=None)
    if settings.geometry is not None:
        parser[_WINDOW_SECTION] = {
            key: str(value) for key, value in zip(_GEOMETRY_KEYS, settings.geometry, strict=True)
        }
    parser[_OPTIONS_SECTION] = {
        "dry_run": str(settings.dry_run),
        "verbose": str(settings.verbose),
        "excludes": settings.excludes,
        _HISTORY_FILTER: settings.history_filter,
        "dark": str(settings.dark),
    }
    return parser


def _section(parser: configparser.ConfigParser, name: str) -> configparser.SectionProxy | None:
    """return the section NAME of PARSER, or None when the file does not carry it
    usage: _section <PARSER> <NAME>
    returns: the section, or None

    example: _section(parser, "window")

    """
    return parser[name] if parser.has_section(name) else None


def _geometry(section: configparser.SectionProxy | None) -> tuple[int, int, int, int] | None:
    """read the four geometry keys of SECTION as whole signed numbers
    usage: _geometry <SECTION>
    returns: (width, height, x, y), or None when a key is absent or not a whole number

    example: _geometry(_section(parser, "window"))

    """
    if section is None:
        return None
    values: list[int] = []
    for key in _GEOMETRY_KEYS:
        try:
            values.append(int(section[key]))
        except (KeyError, ValueError):
            return None
    return (values[0], values[1], values[2], values[3])


def _flag(section: configparser.SectionProxy | None, key: str) -> bool:
    """read the switch KEY of SECTION
    usage: _flag <SECTION> <KEY>
    returns: the saved switch; a missing or unreadable one is False

    example: _flag(_section(parser, "options"), "dark")

    """
    if section is None:
        return False
    try:
        saved = section.getboolean(key)
    except (KeyError, ValueError):
        return False
    return saved is True


def _text(section: configparser.SectionProxy | None, key: str) -> str:
    """read the text KEY of SECTION
    usage: _text <SECTION> <KEY>
    returns: the saved text; a missing one is ""

    example: _text(_section(parser, "options"), "excludes")

    """
    if section is None:
        return ""
    return section.get(key, "")


def _history_filter(section: configparser.SectionProxy | None) -> str:
    """read the saved history filter of SECTION, spec §9
    usage: _history_filter <SECTION>
    returns: the saved filter, or "All" when it is missing or unknown

    example: _history_filter(_section(parser, "options"))

    """
    saved = _text(section, _HISTORY_FILTER)
    return saved if saved in _HISTORY_FILTERS else _DEFAULT_HISTORY_FILTER


def _discard(path: str) -> None:
    """delete the temporary file PATH when it was left behind, ignoring a failure or an empty path
    usage: _discard <PATH>
    returns: nothing

    example: _discard("/home/user/.config/folder_remove_empty/.folder_remove_empty-ab12cd")

    """
    if not path:
        return
    try:
        os.unlink(path)
    except OSError:
        return
