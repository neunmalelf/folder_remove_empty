"""tests of the keep list: the fixed names, the prefixes and the extras."""

import unittest

from remove_empty_folder_core import excluded_name, split_excludes


class ExcludedNameTest(unittest.TestCase):
    """every keep rule of the shell original, one folder name per rule."""

    def test_the_fixed_keep_list(self) -> None:
        cases = [
            (".Trash-1000", True),
            (".cache", True),
            ("$RECYCLE.BIN", True),
            (".$RECYCLE.BIN", True),
            ("System Volume Information", True),
            ("empty", False),
            (".cache2", False),
            ("$RECYCLE.BIN.bak", False),
            ("cache", False),
            ("", False),
        ]
        for name, kept in cases:
            with self.subTest(name=name):
                self.assertEqual(excluded_name(name, []), kept)

    def test_the_zzzz_prefix_is_kept_in_upper_case_only(self) -> None:
        for name in ("ZZZZ", "ZZZZ_backup", "ZZZZZZ"):
            with self.subTest(name=name):
                self.assertTrue(excluded_name(name, []))
        for name in ("zzzz", "aZZZZ", " ZZZZ"):
            with self.subTest(name=name):
                self.assertFalse(excluded_name(name, []))

    def test_four_leading_digits_are_kept(self) -> None:
        for name in ("2026-09-23", "9999", "0000_backup", "1234"):
            with self.subTest(name=name):
                self.assertTrue(excluded_name(name, []))
        for name in ("202", "a2026", "20x6", " 2026", "12 34"):
            with self.subTest(name=name):
                self.assertFalse(excluded_name(name, []))

    def test_only_ascii_digits_count(self) -> None:
        self.assertFalse(excluded_name("２０２６", []))
        self.assertFalse(excluded_name("١٢٣٤backup", []))

    def test_the_missing_marker_is_kept_in_any_letter_case(self) -> None:
        for name in (
            "backup !!! MISSING !!! folder",
            "backup !!! missing !!! folder",
            "!!! MiSsInG !!!",
            "!!! MISSING !!!",
        ):
            with self.subTest(name=name):
                self.assertTrue(excluded_name(name, []))
        for name in ("missing", "!!! MISSING", "MISSING !!!"):
            with self.subTest(name=name):
                self.assertFalse(excluded_name(name, []))


class ExtraKeepListTest(unittest.TestCase):
    """the extra kept names: exact names and names with a trailing '*'."""

    def test_an_extra_name_matches_exactly(self) -> None:
        extras = ["downloads"]
        self.assertTrue(excluded_name("downloads", extras))
        self.assertFalse(excluded_name("downloads2", extras))
        self.assertFalse(excluded_name("download", extras))

    def test_an_extra_name_with_a_star_is_a_prefix_rule(self) -> None:
        extras = ["keep-*"]
        for name in ("keep-me", "keep-", "keep-2026-09-23"):
            with self.subTest(name=name):
                self.assertTrue(excluded_name(name, extras))
        self.assertFalse(excluded_name("keep", extras))
        self.assertFalse(excluded_name("", extras))

    def test_split_excludes_drops_the_empty_pieces(self) -> None:
        self.assertEqual(split_excludes("keep-*:downloads::"), ["keep-*", "downloads"])
        self.assertEqual(split_excludes(":a::b:"), ["a", "b"])
        self.assertEqual(split_excludes(""), [])
        self.assertEqual(split_excludes("::"), [])

    def test_the_split_list_is_read_by_the_matcher(self) -> None:
        extras = split_excludes("keep-*:downloads::")
        self.assertTrue(excluded_name("keep-me", extras))
        self.assertTrue(excluded_name("downloads", extras))
        self.assertFalse(excluded_name("keep", extras))


if __name__ == "__main__":
    unittest.main()
