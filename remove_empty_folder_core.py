"""the engine of folder_remove_empty: scan, keep list and removal.

This module is the reusable core of the program. It imports no tkinter, no
argparse and no sys, and it writes to no stream, so another program and the
tests drive it headless. Both front ends (the tkinter window and the terminal
reporter) watch a run through the Observer interface.
"""

import abc
import os
import stat
import threading
from dataclasses import dataclass, field
from enum import IntEnum

# the environment variable that carries the extra kept names, ':' separated.
ENV_EXCLUDES = "FOLDER_REMOVE_EMPTY_EXCLUDE"

# the folder names that are never removed on their own.
_KEPT_NAMES = (
    ".Trash-1000",
    ".cache",
    "$RECYCLE.BIN",
    ".$RECYCLE.BIN",
    "System Volume Information",
)

# the name prefix whose folders are never removed on their own.
_KEPT_PREFIX = "ZZZZ"

# keeps a folder that carries the marker in its name in any letter case: it
# marks a folder whose content is known to be missing, so an empty one is a
# hole and not a leftover.
_MISSING_MARKER = "!!! MISSING !!!"


class FolderRemoveEmptyError(Exception):
    """the reason a run was refused before it did anything
    usage: FolderRemoveEmptyError <REASON>
    returns: the exception carrying the reason behind an ERROR: line

    example: FolderRemoveEmptyError("the given path does not exist: /tmp/nope")

    """


class Action(IntEnum):
    """what a run did to one folder
    usage: Action
    returns: the outcome of one folder, REMOVED, FAILED or KEPT

    example: Event("/tmp/tree/a", Action.REMOVED).text()

    """

    # the folder was removed; with a dry run it stayed in place.
    REMOVED = 0
    # the folder was rated empty but its removal was refused.
    FAILED = 1
    # the folder is on the keep list and stayed in place.
    KEPT = 2


@dataclass
class Options:
    """the engine settings of one run
    usage: Options([START_PATH]) [DRY_RUN] [VERBOSE] [EXCLUDES] [NO_GUI]
    returns: the options of a run

    example: Options(start_path="/tmp/tree", dry_run=True)

    """

    # the folder the run starts in; "" means the current folder.
    start_path: str = ""
    # report the folders that would be removed and touch nothing.
    dry_run: bool = False
    # report the vacant kept folders that were left in place.
    verbose: bool = False
    # the extra kept names, ':' separated.
    excludes: str = ""
    # the terminal mode runs without the window.
    no_gui: bool = False


@dataclass(frozen=True)
class Event:
    """one step of a run, handed to the observer
    usage: Event <FOLDER> <ACTION> [DRY_RUN] [ERR]
    returns: the outcome of one folder

    example: Event("/tmp/tree/a", Action.REMOVED).text()

    """

    # the folder the step worked on.
    folder: str
    # what happened to the folder.
    action: Action
    # marks a step that only reported the folder.
    dry_run: bool = False
    # the reason the removal was refused, set for Action.FAILED only.
    err: OSError | None = None

    def text(self) -> str:
        """describe the step in one line without colors
        usage: text
        returns: the one-line description of the outcome

        example: Event("/tmp/tree/a", Action.FAILED, err=OSError(13, "Permission denied")).text()

        """
        if self.action == Action.REMOVED:
            if self.dry_run:
                return f"would remove: {self.folder}"
            return f"removed: {self.folder}"
        if self.action == Action.FAILED:
            return f"not removed: {self.folder} ({_reason(self.err)})"
        return f"excluded, kept: {self.folder}"


@dataclass
class Summary:
    """the closing counters of one run
    usage: Summary([START_PATH]) [DRY_RUN] [FOLDERS] [REMOVED] [FAILED] [STOPPED]
    returns: the counters of a run

    example: Summary(start_path="/tmp/tree", folders=3, removed=3)

    """

    # the folder the run worked in.
    start_path: str = ""
    # reports whether the run only reported the folders.
    dry_run: bool = False
    # the number of folders that were rated below the start folder.
    folders: int = 0
    # the folders that were removed, or would have been removed in a dry run.
    removed: int = 0
    # the folders whose removal was refused.
    failed: int = 0
    # reports that the run was stopped before its end.
    stopped: bool = False


class Observer(abc.ABC):
    """the progress interface both front ends implement
    usage: Observer(...)
    returns: the interface execute() reports through

    example: execute(Options(start_path="/tmp/tree"), fake_observer)

    """

    @abc.abstractmethod
    def start(self, start_path: str) -> None:
        """report the start folder a run begins in, after the path check
        usage: start <START_PATH>
        returns: nothing

        example: observer.start("/tmp/tree")

        """

    @abc.abstractmethod
    def current(self, folder: str) -> None:
        """report the folder that is rated or removed next
        usage: current <FOLDER>
        returns: nothing

        example: observer.current("/tmp/tree/a")

        """

    @abc.abstractmethod
    def done(self, event: Event) -> None:
        """report the outcome of one folder
        usage: done <EVENT>
        returns: nothing

        example: observer.done(Event("/tmp/tree/a", Action.REMOVED))

        """

    @abc.abstractmethod
    def summary(self, summary: Summary) -> None:
        """report the closing counters of the run
        usage: summary <SUMMARY>
        returns: nothing

        example: observer.summary(Summary(start_path="/tmp/tree"))

        """

    @abc.abstractmethod
    def checkpoint(self) -> bool:
        """block while the run is paused and report whether it may work on
        usage: checkpoint
        returns: False when the run was stopped and must end

        example: observer.checkpoint()

        """


@dataclass
class Scan:
    """the result of one bottom-up scan below a start folder
    usage: Scan <ROOT> [ORDER] [VACANT] [KEPT]
    returns: the rating of every folder below the root

    example: scan_tree("/tmp/tree", [])

    """

    # the start folder the scan ran in; it is never part of order.
    root: str
    # every folder below the root, children before their parent.
    order: list[str] = field(default_factory=list)
    # the folders that hold no file, no link and no vacant subfolder.
    vacant: set[str] = field(default_factory=set)
    # the folders whose name is on the keep list.
    kept: set[str] = field(default_factory=set)

    def mark_deletes(self) -> set[str]:
        """mark the folders to remove top down, so a parent is decided before its children
        usage: mark_deletes
        returns: the folders the run removes, kept folders included when their parent goes

        example: scan.mark_deletes()

        """
        deletes: set[str] = set()
        for folder in reversed(self.order):
            if folder not in self.vacant:
                continue
            if folder not in self.kept or os.path.dirname(folder) in deletes:
                deletes.add(folder)
        return deletes

    def _rate(self, folder: str, extras: list[str]) -> bool:
        """rate one folder and every folder below it bottom up, appending them to the order
        usage: _rate <FOLDER> <EXTRAS>
        returns: True when the folder is vacant, False otherwise

        example: scan._rate("/tmp/tree/a", ["keep-*"])

        """
        vacant = True
        entries: list[os.DirEntry[str]] = []
        try:
            with os.scandir(folder) as iterator:
                entries = sorted(iterator, key=lambda entry: entry.name)
        except OSError:
            # what cannot be read cannot be proven empty.
            vacant = False

        for entry in entries:
            # a link to a folder is a link: removing the folder it points at is
            # not this run's job, so the link blocks its parent like a file does.
            if not entry.is_dir(follow_symlinks=False):
                vacant = False
                continue
            if not self._rate(os.path.join(folder, entry.name), extras):
                vacant = False

        if vacant:
            self.vacant.add(folder)
        if excluded_name(os.path.basename(folder), extras):
            self.kept.add(folder)
        self.order.append(folder)
        return vacant


def resolve_start(path: str) -> str:
    """resolve the folder a run starts in to an absolute path, refusing a bad one
    usage: resolve_start <PATH>
    returns: the absolute, cleaned folder to start in

    example: resolve_start("/tmp/tree")

    """
    if path == "":
        try:
            current = os.getcwd()
        except OSError as err:
            raise FolderRemoveEmptyError(f"the current folder cannot be read: {err}") from None
        return os.path.abspath(current)

    try:
        info = os.stat(path)
    except OSError:
        # a path that cannot be read at all is reported as missing.
        raise FolderRemoveEmptyError(f"the given path does not exist: {path}") from None
    if not stat.S_ISDIR(info.st_mode):
        raise FolderRemoveEmptyError(f"the given path is not a folder: {path}")

    try:
        return os.path.abspath(path)
    except OSError as err:
        reason = f"the given path cannot be made absolute: {path} ({err})"
        raise FolderRemoveEmptyError(reason) from None


def scan_tree(root: str, extras: list[str]) -> Scan:
    """rate every folder below ROOT bottom up, the names of EXTRAS kept in place
    usage: scan_tree <ROOT> <EXTRAS>
    returns: the scan of the folders below ROOT, empty when ROOT cannot be read

    example: scan_tree("/tmp/tree", ["keep-*"])

    """
    scan = Scan(root=root)
    children: list[os.DirEntry[str]] = []
    try:
        with os.scandir(root) as iterator:
            children = sorted(iterator, key=lambda entry: entry.name)
    except OSError:
        # the root is reported as an empty scan; the caller checked it already.
        return scan

    for entry in children:
        if not entry.is_dir(follow_symlinks=False):
            continue
        scan._rate(os.path.join(root, entry.name), extras)
    return scan


def split_excludes(list_: str) -> list[str]:
    """split a ':' separated list of extra kept names, leaving empty pieces out
    usage: split_excludes <LIST>
    returns: the single kept names of the list, [] for an empty list

    example: split_excludes("keep-*:downloads::")

    """
    if list_ == "":
        return []
    return [piece for piece in list_.split(":") if piece != ""]


def excluded_name(name: str, extras: list[str]) -> bool:
    """report whether a folder name is on the keep list, so the folder stays
    usage: excluded_name <NAME> <EXTRAS>
    returns: True when the name is kept, False otherwise

    example: excluded_name("ZZZZ_backup", [])

    """
    if name in _KEPT_NAMES:
        return True
    if name.startswith(_KEPT_PREFIX):
        return True
    if _has_four_leading_digits(name):
        return True
    if _MISSING_MARKER.lower() in name.lower():
        return True

    for extra in extras:
        prefix = extra.removesuffix("*")
        if prefix != extra:
            if name.startswith(prefix):
                return True
            continue
        if name == extra:
            return True
    return False


def _has_four_leading_digits(name: str) -> bool:
    """report whether a name starts with four ASCII digits, as in "2026-09-23_backup"
    usage: _has_four_leading_digits <NAME>
    returns: True when the first four characters are all ASCII digits

    example: _has_four_leading_digits("2026-09-23")

    """
    return len(name) >= 4 and all("0" <= digit <= "9" for digit in name[:4])


def _reason(err: OSError | None) -> str:
    """build the reason text of a refused removal, in the shape the Go tool printed it
    usage: _reason <ERR>
    returns: "remove <path>: <strerror>", or the bare strerror without a file name,
             or the exception text when the error carries no strerror

    example: _reason(OSError(13, "Permission denied", "/tmp/tree/readonly/inner"))

    """
    if err is None:
        return ""
    if err.strerror is None:
        return str(err)
    text = err.strerror.lower()
    if err.filename:
        return f"remove {err.filename}: {text}"
    return text


def execute(options: Options, observer: Observer) -> Summary:
    """work one run: resolve, scan, mark and remove the empty folders deepest first
    usage: execute <OPTIONS> <OBSERVER>
    returns: the counters of the run

    example: execute(Options(start_path="/tmp/tree"), TerminalReporter(Options()))

    """
    start = resolve_start(options.start_path)

    summary = Summary(start_path=start, dry_run=options.dry_run)
    observer.start(start)

    scan = scan_tree(start, split_excludes(options.excludes))
    deletes = scan.mark_deletes()
    summary.folders = len(scan.order)

    # a refused child is the reason its parent would fail next, so the parent
    # is skipped as well.
    failed: set[str] = set()
    for folder in scan.order:
        if not observer.checkpoint():
            summary.stopped = True
            break
        parent = os.path.dirname(folder)

        if folder not in deletes:
            if options.verbose and folder in scan.kept and folder in scan.vacant:
                observer.current(folder)
                observer.done(Event(folder=folder, action=Action.KEPT))
            continue
        if folder in failed:
            failed.add(parent)
            continue

        observer.current(folder)
        if options.dry_run:
            observer.done(Event(folder=folder, action=Action.REMOVED, dry_run=True))
            summary.removed += 1
            continue

        # os.rmdir refuses a folder that is not empty, so nothing but the
        # vacant folders marked above can be lost.
        try:
            os.rmdir(folder)
        except OSError as err:
            observer.done(Event(folder=folder, action=Action.FAILED, err=err))
            summary.failed += 1
            failed.add(parent)
            continue
        observer.done(Event(folder=folder, action=Action.REMOVED))
        summary.removed += 1

    observer.summary(summary)
    return summary


class RunControl:
    """hold the pause and the stop state of one run
    usage: RunControl
    returns: the control one run asks its checkpoints from

    example: RunControl().checkpoint()

    """

    def __init__(self) -> None:
        """start a control that is neither paused nor stopped
        usage: __init__
        returns: nothing

        example: RunControl()

        """
        self._condition = threading.Condition()
        self._paused = False
        self._stopped = False

    def checkpoint(self) -> bool:
        """wait while the run is paused and report whether it may work on
        usage: checkpoint
        returns: False when the run was stopped and must end

        example: control.checkpoint()

        """
        with self._condition:
            while self._paused and not self._stopped:
                self._condition.wait()
            return not self._stopped

    def pause(self) -> bool:
        """hold the run in front of the next folder, or let it go on when held
        usage: pause
        returns: the state after the toggle, False when the run was stopped

        example: control.pause()

        """
        with self._condition:
            if self._stopped:
                return False
            self._paused = not self._paused
            self._condition.notify_all()
            return self._paused

    def stop(self) -> None:
        """end the run in front of the next folder and release a waiting checkpoint
        usage: stop
        returns: nothing

        example: control.stop()

        """
        with self._condition:
            self._stopped = True
            self._paused = False
            self._condition.notify_all()
