"""tests of the terminal reporter: the stream split, the shapes and the colours."""

import io
import unittest

from remove_empty_folder_core import Action, Event, Options, Summary
from remove_empty_folder_report import (
    ANSI_GREEN,
    ANSI_OFF,
    ANSI_YELLOW,
    TerminalReporter,
    color_code,
    paint,
)


class FakeTty(io.StringIO):
    """a text stream that claims to be a terminal."""

    def isatty(self) -> bool:
        return True


def no_color(_name: str) -> str | None:
    return None


def with_no_color(name: str) -> str | None:
    return "1" if name == "NO_COLOR" else None


class StreamSplitTest(unittest.TestCase):
    """the removed folders go to stdout, everything else to stderr."""

    def test_removed_and_the_summary_go_to_stdout(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        reporter = TerminalReporter(Options(start_path="/t"), out=out, err=err, getenv=no_color)
        reporter.start("/t")
        reporter.done(Event("/t/a", Action.REMOVED))
        reporter.summary(Summary(start_path="/t", folders=1, removed=1))
        self.assertEqual(out.getvalue(), "removed: /t/a\n1 empty folder(s) removed\n")
        self.assertEqual(err.getvalue(), "path exists: /t\nstart folder: /t\n")

    def test_the_start_lines_name_the_path_only_when_it_was_given(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        reporter = TerminalReporter(Options(), out=out, err=err, getenv=no_color)
        reporter.start("/t")
        self.assertEqual(err.getvalue(), "start folder: /t\n")
        self.assertEqual(out.getvalue(), "")

    def test_kept_refused_and_errors_go_to_stderr(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        reporter = TerminalReporter(Options(), out=out, err=err, getenv=no_color)
        reporter.done(Event("/t/keep", Action.KEPT))
        reporter.done(Event("/t/ro", Action.FAILED, err=OSError(13, "Permission denied", "/t/ro")))
        reporter.summary(Summary(start_path="/t", folders=2, failed=1))
        self.assertEqual(out.getvalue(), "no empty folder found\n")
        self.assertEqual(
            err.getvalue(),
            "excluded, kept: /t/keep\n"
            "not removed: /t/ro (remove /t/ro: permission denied)\n"
            "1 folder(s) kept\n",
        )

    def test_a_refusal_without_a_refusal_counter_prints_no_kept_line(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        reporter = TerminalReporter(Options(), out=out, err=err, getenv=no_color)
        reporter.summary(Summary(start_path="/t", folders=0))
        self.assertEqual(out.getvalue(), "no empty folder found\n")
        self.assertEqual(err.getvalue(), "")


class DryRunTest(unittest.TestCase):
    """a dry run prints the plain paths and no summary."""

    def test_only_the_plain_paths_and_nothing_else(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        reporter = TerminalReporter(
            Options(start_path="/t", dry_run=True), out=out, err=err, getenv=no_color
        )
        reporter.start("/t")
        reporter.done(Event("/t/a", Action.REMOVED, dry_run=True))
        reporter.done(Event("/t/b", Action.REMOVED, dry_run=True))
        reporter.summary(Summary(start_path="/t", dry_run=True, folders=2, removed=2))
        self.assertEqual(out.getvalue(), "/t/a\n/t/b\n")
        self.assertEqual(err.getvalue(), "path exists: /t\nstart folder: /t\n")


class ColorTest(unittest.TestCase):
    """a colour appears only on a terminal and without NO_COLOR."""

    def test_the_label_is_coloured_on_a_terminal(self) -> None:
        out, err = FakeTty(), FakeTty()
        reporter = TerminalReporter(Options(), out=out, err=err, getenv=no_color)
        reporter.done(Event("/t/a", Action.REMOVED))
        reporter.done(Event("/t/ro", Action.FAILED, err=OSError(13, "Permission denied", "/t/ro")))
        self.assertEqual(out.getvalue(), f"{ANSI_GREEN}removed:{ANSI_OFF} /t/a\n")
        self.assertEqual(
            err.getvalue(),
            f"{ANSI_YELLOW}not removed:{ANSI_OFF} /t/ro (remove /t/ro: permission denied)\n",
        )

    def test_no_color_switches_the_colour_off_on_a_terminal(self) -> None:
        out = FakeTty()
        reporter = TerminalReporter(Options(), out=out, err=io.StringIO(), getenv=with_no_color)
        reporter.done(Event("/t/a", Action.REMOVED))
        self.assertEqual(out.getvalue(), "removed: /t/a\n")

    def test_a_pipe_takes_no_colour_even_without_no_color(self) -> None:
        out = io.StringIO()
        reporter = TerminalReporter(Options(), out=out, err=io.StringIO(), getenv=no_color)
        reporter.done(Event("/t/a", Action.REMOVED))
        self.assertEqual(out.getvalue(), "removed: /t/a\n")

    def test_the_helpers_answer_for_themselves(self) -> None:
        self.assertEqual(color_code(FakeTty(), ANSI_GREEN, no_color), ANSI_GREEN)
        self.assertEqual(color_code(io.StringIO(), ANSI_GREEN, no_color), "")
        self.assertEqual(color_code(FakeTty(), ANSI_GREEN, with_no_color), "")
        self.assertEqual(paint(io.StringIO(), ANSI_GREEN, "removed:", no_color), "removed:")
        self.assertEqual(
            paint(FakeTty(), ANSI_GREEN, "removed:", no_color),
            f"{ANSI_GREEN}removed:{ANSI_OFF}",
        )


class NoProgressTest(unittest.TestCase):
    """the terminal front end cannot pause or stop."""

    def test_current_writes_nothing_and_checkpoint_continues(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        reporter = TerminalReporter(Options(), out=out, err=err, getenv=no_color)
        reporter.current("/t/a")
        self.assertEqual((out.getvalue(), err.getvalue()), ("", ""))
        self.assertTrue(reporter.checkpoint())


if __name__ == "__main__":
    unittest.main()
