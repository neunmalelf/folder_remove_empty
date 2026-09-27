"""tests of the generated man page and tldr page."""

import re
import unittest

import remove_empty_folder_docs as docs
import remove_empty_folder_version as version
from remove_empty_folder_core import ENV_EXCLUDES

# the man sections, in the order the page shows them.
SECTIONS = [
    "NAME",
    "SYNOPSIS",
    "DESCRIPTION",
    "OPTIONS",
    "THE WINDOW",
    "KEPT FOLDERS",
    "ENVIRONMENT",
    "EXIT STATUS",
    "EXAMPLES",
    "SEE ALSO",
]

# one tldr example block: the description line, an empty line, then the command
# in backticks with two leading spaces.
EXAMPLE_RE = re.compile(r"\n- (?P<description>[^\n]*)\n\n  `(?P<command>[^`]*)`\n")


class ManPageTest(unittest.TestCase):
    """the roff page: sections, .TH line and the version stamp."""

    def setUp(self) -> None:
        self.page = docs.man_page()

    def test_every_section_header_is_present_in_order(self) -> None:
        positions = []
        for section in SECTIONS:
            header = ".SH " + section + "\n"
            self.assertIn(header, self.page)
            positions.append(self.page.index(header))
        self.assertEqual(positions, sorted(positions))

    def test_th_line_names_the_program_and_carries_the_stamp(self) -> None:
        first = self.page.splitlines()[0]
        self.assertEqual(
            first,
            ".TH " + version.APP_NAME_VERBOSE + ' 1 "' + version.__VERSION__ + '" "'
            + version.__VERSION__ + '" "User Commands"',
        )

    def test_name_section_names_the_program(self) -> None:
        self.assertIn(".SH NAME\n" + version.APP_NAME + " \\- ", self.page)

    def test_pages_carry_the_version_stamp_where_it_belongs(self) -> None:
        # twice in the .TH line: the date field and the source field
        self.assertEqual(self.page.count(version.__VERSION__), 2)

    def test_environment_section_names_the_environment_variable(self) -> None:
        self.assertIn("\\fB" + ENV_EXCLUDES + "\\fR\n", self.page)


class TldrPageTest(unittest.TestCase):
    """the markdown page: the head and one block per example."""

    def setUp(self) -> None:
        self.page = docs.tldr_page()

    def test_head_is_the_app_name_then_the_three_summary_lines(self) -> None:
        head = (
            "# " + version.APP_NAME + "\n\n"
            "> Remove every empty folder below a start folder, deepest first.\n"
            "> The start folder itself is never removed, only the folders below it.\n"
            "> More information: <https://github.com/neunmalelf/folder_remove_empty>.\n"
        )
        self.assertTrue(self.page.startswith(head))

    def test_exactly_eight_blocks_matching_the_examples(self) -> None:
        blocks = EXAMPLE_RE.findall(self.page)
        self.assertEqual(len(blocks), 8)
        self.assertEqual(blocks, docs.TLD_EXAMPLES)
        self.assertEqual(len(self.page.split("\n- ")) - 1, 8)

    def test_every_block_description_is_one_line(self) -> None:
        for description, _command in EXAMPLE_RE.findall(self.page):
            self.assertNotIn("\n", description)
            self.assertTrue(description.endswith(":"))

    def test_every_command_is_backticked_and_indented(self) -> None:
        for block in self.page.split("\n- ")[1:]:
            self.assertIn("\n\n  `", block)
            command_line = block.split("\n\n  `", 1)[1]
            self.assertTrue(command_line.endswith("`\n"))
            self.assertNotIn("\n", command_line[:-2])


class ExamplesTest(unittest.TestCase):
    """the eight (description, command) pairs the pages are built from."""

    def test_eight_entries(self) -> None:
        self.assertEqual(len(docs.TLD_EXAMPLES), 8)

    def test_every_command_names_the_program_or_the_environment(self) -> None:
        for description, command in docs.TLD_EXAMPLES:
            self.assertTrue(
                command.startswith(version.APP_NAME) or command.startswith(ENV_EXCLUDES),
                command,
            )
            self.assertTrue(description.endswith(":"), description)

    def test_every_command_stays_on_one_line(self) -> None:
        for _description, command in docs.TLD_EXAMPLES:
            self.assertNotIn("\n", command)

    def test_environment_example_keeps_its_shape(self) -> None:
        command = docs.TLD_EXAMPLES[4][1]
        self.assertEqual(
            command,
            ENV_EXCLUDES + "='keep-*:downloads*' " + version.APP_NAME + " --no-gui /data/archive",
        )


if __name__ == "__main__":
    unittest.main()
