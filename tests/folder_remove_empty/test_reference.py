"""byte-for-byte comparison of the engine against the captured Go reference.

The captures in tests/folder_remove_empty/reference/ hold the exact stdout,
stderr and exit status of the Go program; this module rebuilds the documented
tree, runs the Python engine over it and compares the two streams byte for
byte. The observer below renders the shapes of the Go reporter, so phase 3 can
replace it with remove_empty_folder_report.TerminalReporter (driven through
main()) and keep the same assertions.
"""

import os
import shutil
import subprocess
import tempfile
import unittest

from remove_empty_folder_core import Action, Event, Observer, Options, Summary, execute

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.join(HERE, "reference")
BUILDER = os.path.join(REFERENCE, "build_tree.sh")
# the scratch root the Go captures were taken in; the prefix is normalised away
GO_SCRATCH = "/tmp/fre-ref.E6hTEvVG"

# capture name, dry run, verbose, extras — the Go commands are listed in cases.md
CASES: tuple[tuple[str, bool, bool, str], ...] = (
    ("terminal_run", False, False, ""),
    ("terminal_dry_run", True, False, ""),
    ("terminal_verbose", False, True, ""),
    ("env_excludes", False, False, "keep-*"),
)


class ReferenceReporter(Observer):
    """write the lines the Go reporter would print, one list per stream."""

    def __init__(self) -> None:
        self.out: list[str] = []
        self.err: list[str] = []

    def start(self, start_path: str) -> None:
        self.err.append(f"path exists: {start_path}")
        self.err.append(f"start folder: {start_path}")

    def current(self, folder: str) -> None:
        return None

    def done(self, event: Event) -> None:
        if event.action is Action.REMOVED:
            line = event.folder if event.dry_run else f"removed: {event.folder}"
            self.out.append(line)
        else:
            self.err.append(event.text())

    def summary(self, summary: Summary) -> None:
        if summary.dry_run:
            return None
        if summary.removed == 0:
            self.out.append("no empty folder found")
        else:
            self.out.append(f"{summary.removed} empty folder(s) removed")
        if summary.failed:
            self.err.append(f"{summary.failed} folder(s) kept")
        return None

    def checkpoint(self) -> bool:
        return True


def _force_remove(root: str) -> None:
    """delete a tree that holds read-only folders, restoring the modes first."""
    for base, dirs, _files in os.walk(root, topdown=False):
        for name in dirs:
            os.chmod(os.path.join(base, name), 0o755)
    shutil.rmtree(root, ignore_errors=True)


def _render(lines: list[str]) -> str:
    """join the collected lines into the byte shape the capture files hold."""
    return "\n".join(lines) + "\n" if lines else ""


@unittest.skipIf(os.geteuid() == 0, "the refusal case needs a non-root user")
@unittest.skipIf(shutil.which("bash") is None, "the tree builder is a bash script")
class ReferenceFidelityTest(unittest.TestCase):
    """the engine reproduces the Go captures line for line."""

    def test_every_capture_matches(self) -> None:
        for case, dry_run, verbose, extras in CASES:
            with self.subTest(case=case):
                self._check_case(case, dry_run, verbose, extras)

    def _check_case(self, case: str, dry_run: bool, verbose: bool, extras: str) -> None:
        holder = tempfile.mkdtemp(prefix=f"fre-ref-{case}-")
        self.addCleanup(_force_remove, holder)
        tree = os.path.join(holder, "tree")
        _ = subprocess.run(["bash", BUILDER, tree], check=True, capture_output=True)

        reporter = ReferenceReporter()
        _ = execute(
            Options(start_path=tree, dry_run=dry_run, verbose=verbose,
                    excludes=extras, no_gui=True),
            reporter,
        )

        prefix = f"{GO_SCRATCH}/{case}/tree"
        for stream, lines in (("out", reporter.out), ("err", reporter.err)):
            name = f"{case}.{stream}"
            with open(os.path.join(REFERENCE, name), encoding="utf-8") as handle:
                expected = handle.read().replace(prefix, tree)
            self.assertEqual(_render(lines), expected, f"{name} differs from the Go run")


if __name__ == "__main__":
    unittest.main()
