"""test helpers shared by the folder_remove_empty test modules.

The observer fake of the engine tests joins them in phase 2, as soon as the
Observer ABC of remove_empty_folder_core.py exists.
"""

import contextlib
import io
import os
import pathlib
import shutil
import tempfile
from collections.abc import Generator


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
