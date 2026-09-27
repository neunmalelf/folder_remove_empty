"""byte-for-byte comparison of the port against the captured Go reference.

The captures in tests/folder_remove_empty/reference/ hold the exact stdout,
stderr and exit status of the Go program. Three groups drive the comparison:
the colourless `<case>.*` files (both streams redirected to regular files), the
`pty_<case>.*` files (captured through two ptys, so they carry the ANSI
colours) and the informational outputs. `main()` re-runs the recorded command
and must reproduce every byte and every exit code.
"""

import io
import os
import shutil
import subprocess
import tempfile
import unittest
from collections.abc import Callable

from folder_remove_empty import main
from remove_empty_folder_core import ENV_EXCLUDES, Options, execute
from remove_empty_folder_report import TerminalReporter
from remove_empty_folder_version import __VERSION__

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.join(HERE, "reference")
BUILDER = os.path.join(REFERENCE, "build_tree.sh")
# the scratch roots the Go captures were taken in; the prefixes are normalised away
GO_PLAIN = "/tmp/fre-ref.E6hTEvVG"
GO_PTY = "/tmp/fre-pty.GMLIjB"

# the Go stamp of the captures; the Python stamp carries the trailing Z, which
# _check_version requires and setuptools rejects, so the two differ on purpose
GO_VERSION = "0.5.20260923194832"
VERSION_LINE = ((GO_VERSION, __VERSION__),)

# capture name, dry run, verbose, extras — the Go commands are in cases.md
PLAIN_CASES: tuple[tuple[str, bool, bool, str], ...] = (
    ("terminal_run", False, False, ""),
    ("terminal_dry_run", True, False, ""),
    ("terminal_verbose", False, True, ""),
    ("env_excludes", False, False, "keep-*"),
)
PTY_CASES: tuple[tuple[str, bool, bool, str, bool], ...] = (
    ("pty_run", False, False, "", False),
    ("pty_dry_run", True, False, "", False),
    ("pty_verbose", False, True, "", False),
    ("pty_env_excludes", False, False, "keep-*", False),
    ("pty_no_color", False, False, "", True),
)


class FakeTty(io.StringIO):
    """a text stream that claims to be a terminal."""

    def isatty(self) -> bool:
        return True


def plain_env(_name: str) -> str | None:
    """read no environment at all, so NO_COLOR stays unset."""
    return None


def no_color_env(name: str) -> str | None:
    """set NO_COLOR, the one variable the coloured captures vary."""
    return "1" if name == "NO_COLOR" else None


def excludes_env(name: str) -> str | None:
    """set the extra kept names of the env_excludes case."""
    return "keep-*" if name == ENV_EXCLUDES else None


def _force_remove(root: str) -> None:
    """delete a tree that holds read-only folders, restoring the modes first."""
    for base, dirs, _files in os.walk(root, topdown=False):
        for name in dirs:
            os.chmod(os.path.join(base, name), 0o755)
    shutil.rmtree(root, ignore_errors=True)


def _capture(case: str, stream: str) -> str:
    """read one captured stream of a case."""
    with open(os.path.join(REFERENCE, f"{case}.{stream}"), encoding="utf-8") as handle:
        return handle.read()


def _capture_rc(case: str) -> int:
    """read the captured exit status of a case."""
    return int(_capture(case, "rc").strip())


@unittest.skipIf(os.geteuid() == 0, "the refusal case needs a non-root user")
@unittest.skipIf(shutil.which("bash") is None, "the tree builder is a bash script")
class ReferenceFidelityTest(unittest.TestCase):
    """the terminal front end reproduces the Go captures line for line."""

    def _run(
        self,
        case: str,
        dry_run: bool,
        verbose: bool,
        extras: str,
        tty: bool,
        env: Callable[[str], str | None],
    ) -> tuple[str, str, str]:
        holder = tempfile.mkdtemp(prefix=f"fre-ref-{case}-")
        self.addCleanup(_force_remove, holder)
        tree = os.path.join(holder, "tree")
        _ = subprocess.run(["bash", BUILDER, tree], check=True, capture_output=True)

        out = FakeTty() if tty else io.StringIO()
        err = FakeTty() if tty else io.StringIO()
        options = Options(
            start_path=tree, dry_run=dry_run, verbose=verbose, excludes=extras, no_gui=True
        )
        _ = execute(options, TerminalReporter(options, out=out, err=err, getenv=env))
        return tree, out.getvalue(), err.getvalue()

    def _compare(self, case: str, scratch: str, tree: str, out: str, err: str) -> None:
        for stream, mine in (("out", out), ("err", err)):
            expected = _capture(case, stream).replace(f"{scratch}/{case}/tree", tree)
            self.assertEqual(mine, expected, f"{case}.{stream}")

    def test_every_colourless_capture_matches(self) -> None:
        for case, dry_run, verbose, extras in PLAIN_CASES:
            with self.subTest(case=case):
                tree, out, err = self._run(case, dry_run, verbose, extras, False, plain_env)
                self._compare(case, GO_PLAIN, tree, out, err)

    def test_every_coloured_capture_matches(self) -> None:
        for case, dry_run, verbose, extras, no_color in PTY_CASES:
            with self.subTest(case=case):
                env = no_color_env if no_color else plain_env
                tree, out, err = self._run(case, dry_run, verbose, extras, True, env)
                self._compare(case, GO_PTY, tree, out, err)


@unittest.skipIf(os.geteuid() == 0, "the refusal case needs a non-root user")
@unittest.skipIf(shutil.which("bash") is None, "the tree builder is a bash script")
class MainFidelityTest(unittest.TestCase):
    """main() reproduces the captured streams and the captured exit codes."""

    def _tree(self, case: str) -> str:
        holder = tempfile.mkdtemp(prefix=f"fre-main-{case}-")
        self.addCleanup(_force_remove, holder)
        tree = os.path.join(holder, "tree")
        _ = subprocess.run(["bash", BUILDER, tree], check=True, capture_output=True)
        return tree

    def _main(
        self, argv: list[str], env: Callable[[str], str | None] = plain_env
    ) -> tuple[str, str, int]:
        out, err = io.StringIO(), io.StringIO()
        code = main(argv, out=out, err=err, getenv=env)
        return out.getvalue(), err.getvalue(), code

    def _compare(
        self, case: str, got: tuple[str, str, int], replace: tuple[tuple[str, str], ...] = ()
    ) -> None:
        out, err, code = got
        for stream, mine in (("out", out), ("err", err)):
            expected = _capture(case, stream)
            for old, new in replace:
                expected = expected.replace(old, new)
            self.assertEqual(mine, expected, f"{case}.{stream}")
        self.assertEqual(code, _capture_rc(case), f"{case}.rc")

    def test_the_run_cases_through_main(self) -> None:
        for case, flags, env in (
            ("terminal_run", ["--no-gui"], plain_env),
            ("terminal_dry_run", ["--no-gui", "--dry-run"], plain_env),
            ("terminal_verbose", ["--no-gui", "--verbose"], plain_env),
            ("env_excludes", ["--no-gui"], excludes_env),
        ):
            with self.subTest(case=case):
                tree = self._tree(case)
                got = self._main([*flags, tree], env=env)
                self._compare(case, got, ((f"{GO_PLAIN}/{case}/tree", tree),))

    def test_the_refusals_through_main(self) -> None:
        holder = tempfile.mkdtemp(prefix="fre-main-refusals-")
        self.addCleanup(_force_remove, holder)
        first = os.path.join(holder, "a")
        second = os.path.join(holder, "b")
        os.makedirs(first, exist_ok=True)
        os.makedirs(second, exist_ok=True)

        with self.subTest(case="unknown_option"):
            self._compare("unknown_option", self._main(["--no-gui", "--bogus"]))

        with self.subTest(case="two_paths"):
            got = self._main(["--no-gui", first, second])
            self._compare("two_paths", got, ((f"{GO_PLAIN}/two_paths", holder),))

        with self.subTest(case="missing_path"):
            missing = "/tmp/does-not-exist"
            if os.path.exists(missing):
                self.skipTest(f"{missing} exists, the capture cannot be reproduced")
            self._compare("missing_path", self._main(["--no-gui", missing]))

        with self.subTest(case="not_a_folder"):
            tree = self._tree("not_a_folder")
            note = os.path.join(tree, "withfile", "note.txt")
            got = self._main(["--no-gui", note])
            self._compare("not_a_folder", got, ((f"{GO_PLAIN}/not_a_folder/tree", tree),))

    def test_the_informational_outputs_through_main(self) -> None:
        for case, flag, replace in (
            ("info_version", "--version", VERSION_LINE),
            ("info_help", "--help", ()),
            ("info_print_tldr", "--print-tldr", ()),
        ):
            with self.subTest(case=case):
                self._compare(case, self._main([flag]), replace)

        # the man page differs on purpose in exactly two lines: the Python stamp
        # carries the trailing Z, and the page names this port; the other 152
        # lines must stay identical to the Go page
        with self.subTest(case="info_print_man"):
            man_replace = VERSION_LINE + (
                ("the Go port of the shell script", "the Python port of the shell script"),
            )
            self._compare("info_print_man", self._main(["--print-man"]), man_replace)


if __name__ == "__main__":
    unittest.main()
