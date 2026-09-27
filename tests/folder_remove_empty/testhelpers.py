"""test helpers shared by the folder_remove_empty test modules."""

import contextlib
import io
import os
import pathlib
import shutil
import tempfile
from collections.abc import Generator

from remove_empty_folder_core import Action, Event, Observer, Summary

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.join(HERE, "reference")


def reference_text(name: str) -> str:
    """read one captured Go output file from the reference directory
    usage: reference_text <NAME>
    returns: the captured text of that file

    example: reference_text("info_help.out")

    """
    with open(os.path.join(REFERENCE, name), encoding="utf-8") as handle:
        return handle.read()


def tmp_tree(spec: dict[str, object]) -> str:
    """build a folder tree from a nested dict and return its root folder
    usage: tmp_tree <SPEC>
    returns: the absolute path of the created root folder

    example: tmp_tree({"a": {"b": {}}, "c.txt": None})

    """
    root = tempfile.mkdtemp(prefix="fre-test-")
    _fill(root, spec)
    return root


def _fill(root: str, spec: dict[str, object]) -> None:
    """create the entries of SPEC inside the existing folder ROOT
    usage: _fill <ROOT> <SPEC>
    returns: nothing

    example: _fill("/tmp/x", {"a": {}})

    """
    for name, content in spec.items():
        path = os.path.join(root, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            _fill(path, content)
        elif content is None:
            pathlib.Path(path).touch()
        else:
            pathlib.Path(path).write_text(str(content), encoding="utf-8")


def remove_tree(root: str) -> None:
    """delete a tree built by tmp_tree, ignoring an already gone folder
    usage: remove_tree <ROOT>
    returns: nothing

    example: remove_tree("/tmp/fre-test-abc")

    """
    shutil.rmtree(root, ignore_errors=True)


@contextlib.contextmanager
def capture() -> Generator[tuple[io.StringIO, io.StringIO]]:
    """capture everything a call writes to sys.stdout and sys.stderr
    usage: capture
    returns: a context manager yielding the (out, err) buffers

    example: with capture() as (out, err): print("hi")

    """
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        yield out, err


class FakeObserver(Observer):
    """record the progress of one engine run and answer its checkpoints from a script

    The script is read once per checkpoint: the first call answers with its
    first value, and every call after the last value lets the run go on.
    usage: FakeObserver([CHECKPOINTS])
    returns: an observer fake for execute()

    example: FakeObserver([True, False])

    """

    def __init__(self, checkpoints: list[bool] | None = None) -> None:
        """start a fake with an empty record and an optional checkpoint script
        usage: __init__ [CHECKPOINTS]
        returns: nothing

        example: FakeObserver([False])

        """
        self.started: str | None = None
        self.currents: list[str] = []
        self.events: list[Event] = []
        self.summaries: list[Summary] = []
        self.checkpoints: list[bool] = list(checkpoints) if checkpoints else []
        self.answered: int = 0

    def start(self, start_path: str) -> None:
        """record the start folder of the run
        usage: start <START_PATH>
        returns: nothing

        example: observer.start("/tmp/tree")

        """
        self.started = start_path

    def current(self, folder: str) -> None:
        """record the folder the run works on next
        usage: current <FOLDER>
        returns: nothing

        example: observer.current("/tmp/tree/a")

        """
        self.currents.append(folder)

    def done(self, event: Event) -> None:
        """record the outcome of one folder
        usage: done <EVENT>
        returns: nothing

        example: observer.done(Event("/tmp/tree/a", Action.REMOVED))

        """
        self.events.append(event)

    def summary(self, summary: Summary) -> None:
        """record the closing counters of the run
        usage: summary <SUMMARY>
        returns: nothing

        example: observer.summary(Summary(start_path="/tmp/tree"))

        """
        self.summaries.append(summary)

    def checkpoint(self) -> bool:
        """answer with the next scripted value, or True once the script is used up
        usage: checkpoint
        returns: the scripted value, True when the script is exhausted

        example: observer.checkpoint()

        """
        self.answered += 1
        if self.answered <= len(self.checkpoints):
            return self.checkpoints[self.answered - 1]
        return True

    def folders(self, action: Action) -> list[str]:
        """return the folders that were reported with ACTION, in report order
        usage: folders <ACTION>
        returns: the folders of the matching events

        example: observer.folders(Action.REMOVED)

        """
        return [event.folder for event in self.events if event.action == action]
