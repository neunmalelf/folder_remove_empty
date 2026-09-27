"""tests of the command line: every option, both refusals, environment and usage text."""

import os
import unittest
from unittest import mock

from remove_empty_folder_core import FolderRemoveEmptyError, Options
from remove_empty_folder_options import (
    Command,
    UnknownOptionError,
    new_options,
    parse_args,
    usage,
)
from tests.folder_remove_empty.testhelpers import reference_text


class ParseArgsTest(unittest.TestCase):
    """every option of the shell original and of the port."""

    def test_every_option_is_read(self) -> None:
        cases = [
            ([], Options(), Command.RUN),
            (["/tmp"], Options(start_path="/tmp"), Command.RUN),
            (["-d"], Options(dry_run=True), Command.RUN),
            (["--dryrun"], Options(dry_run=True), Command.RUN),
            (["--dry-run"], Options(dry_run=True), Command.RUN),
            (["-v"], Options(verbose=True), Command.RUN),
            (["--verbose"], Options(verbose=True), Command.RUN),
            (["--no-gui"], Options(no_gui=True), Command.RUN),
            (
                ["-v", "/tmp", "--no-gui", "-d"],
                Options(start_path="/tmp", verbose=True, no_gui=True, dry_run=True),
                Command.RUN,
            ),
            (["-h"], Options(), Command.HELP),
            (["--help"], Options(), Command.HELP),
            (["--version"], Options(), Command.VERSION),
            (["--print-man"], Options(), Command.MAN),
            (["--print-tldr"], Options(), Command.TLDR),
        ]
        for args, want, command in cases:
            with self.subTest(args=args):
                options, got_command = parse_args(args, getenv=lambda name: None)
                self.assertEqual(options, want)
                self.assertEqual(got_command, command)

    def test_the_first_informational_option_wins(self) -> None:
        options, command = parse_args(["--help", "--version"], getenv=lambda name: None)
        self.assertEqual(command, Command.HELP)
        self.assertEqual(options, Options())


class RefusalTest(unittest.TestCase):
    """the two refusals of the shell original."""

    def test_an_unknown_option_names_the_option(self) -> None:
        with self.assertRaises(UnknownOptionError) as caught:
            parse_args(["--nope"], getenv=lambda name: None)
        self.assertEqual(caught.exception.option, "--nope")
        self.assertEqual(str(caught.exception), "unknown option: --nope")

    def test_a_second_path_is_refused_with_the_argument(self) -> None:
        with self.assertRaises(FolderRemoveEmptyError) as caught:
            parse_args(["-d", "/tmp/a", "/tmp/b"], getenv=lambda name: None)
        self.assertEqual(str(caught.exception), "only one path is allowed, got: /tmp/b")


class EnvironmentTest(unittest.TestCase):
    """the extra kept names come from the environment."""

    def test_an_injected_getenv_prefills_the_excludes(self) -> None:
        options = new_options(lambda name: "keep-*:downloads*")
        self.assertEqual(options.excludes, "keep-*:downloads*")

    def test_a_missing_variable_leaves_the_excludes_empty(self) -> None:
        self.assertEqual(new_options(lambda name: None).excludes, "")

    def test_the_environment_is_read_by_default(self) -> None:
        with mock.patch.dict(os.environ, {"FOLDER_REMOVE_EMPTY_EXCLUDE": "keep-me"}):
            self.assertEqual(new_options().excludes, "keep-me")
            self.assertEqual(parse_args([])[0].excludes, "keep-me")


class UsageTest(unittest.TestCase):
    """the usage text is the one the Go tool printed."""

    def test_usage_matches_the_captured_go_text(self) -> None:
        self.assertEqual(usage(), reference_text("info_help.out"))

    def test_usage_names_the_environment_variable_and_the_kept_names(self) -> None:
        text = usage()
        self.assertIn("FOLDER_REMOVE_EMPTY_EXCLUDE", text)
        self.assertIn("!!! MISSING !!!", text)
        self.assertIn("--print-tldr", text)


if __name__ == "__main__":
    unittest.main()
