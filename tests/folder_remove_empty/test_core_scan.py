"""tests of the folder scan: order, vacancy and the unreadable cases."""

import os
import unittest

from remove_empty_folder_core import scan_tree
from tests.folder_remove_empty.testhelpers import remove_tree, tmp_tree

ROOT_CAN_READ_EVERYTHING = os.geteuid() == 0


class ScanOrderTest(unittest.TestCase):
    """the children-first order of the scan and the folders it leaves out."""

    def test_a_chain_of_nested_folders_is_rated_children_first(self) -> None:
        root = tmp_tree({"chain": {"inner": {"deepest": {}}}})
        self.addCleanup(remove_tree, root)
        deepest = os.path.join(root, "chain", "inner", "deepest")
        inner = os.path.join(root, "chain", "inner")
        chain = os.path.join(root, "chain")

        scan = scan_tree(root, [])

        self.assertEqual(scan.root, root)
        self.assertEqual(scan.order, [deepest, inner, chain])
        for folder in scan.order:
            self.assertIn(folder, scan.vacant)
        self.assertEqual(scan.mark_deletes(), {deepest, inner, chain})

    def test_a_file_blocks_its_folder(self) -> None:
        root = tmp_tree({"data": {"empty": {}, "file.txt": "x"}})
        self.addCleanup(remove_tree, root)
        data = os.path.join(root, "data")
        empty = os.path.join(data, "empty")

        scan = scan_tree(root, [])

        self.assertNotIn(data, scan.vacant)
        self.assertIn(empty, scan.vacant)

    def test_the_start_folder_is_never_part_of_the_scan(self) -> None:
        root = tmp_tree({"a": {"b": {}}, "c": {}})
        self.addCleanup(remove_tree, root)

        scan = scan_tree(root, [])

        self.assertNotIn(root, scan.order)
        self.assertNotIn(root, scan.mark_deletes())
        self.assertEqual(len(scan.order), 3)

    def test_a_link_to_a_folder_blocks_its_parent_and_is_never_followed(self) -> None:
        root = tmp_tree({"holder": {"inner": {}}})
        outside = tmp_tree({"file.txt": "x"})
        self.addCleanup(remove_tree, root)
        self.addCleanup(remove_tree, outside)
        holder = os.path.join(root, "holder")
        inner = os.path.join(holder, "inner")
        os.symlink(outside, os.path.join(holder, "dir-link"))
        os.symlink(os.path.join(outside, "file.txt"), os.path.join(holder, "file-link"))

        scan = scan_tree(root, [])

        self.assertNotIn(holder, scan.vacant)
        self.assertIn(inner, scan.vacant)
        self.assertNotIn(outside, scan.order)
        self.assertEqual(scan.order, [inner, holder])

    @unittest.skipIf(ROOT_CAN_READ_EVERYTHING, "root reads every folder")
    def test_an_unreadable_folder_is_not_vacant(self) -> None:
        root = tmp_tree({"locked": {"inner": {}}})
        self.addCleanup(remove_tree, root)
        locked = os.path.join(root, "locked")
        os.chmod(locked, 0o000)
        self.addCleanup(os.chmod, locked, 0o755)

        scan = scan_tree(root, [])

        self.assertNotIn(locked, scan.vacant)
        self.assertNotIn(os.path.join(locked, "inner"), scan.order)
        self.assertIn(locked, scan.order)
        self.assertNotIn(locked, scan.mark_deletes())

    @unittest.skipIf(ROOT_CAN_READ_EVERYTHING, "root reads every folder")
    def test_an_unreadable_root_yields_an_empty_scan(self) -> None:
        root = tmp_tree({"inner": {"deepest": {}}})
        self.addCleanup(remove_tree, root)
        os.chmod(root, 0o000)
        self.addCleanup(os.chmod, root, 0o700)

        scan = scan_tree(root, [])

        self.assertEqual(scan.root, root)
        self.assertEqual(scan.order, [])
        self.assertEqual(scan.vacant, set())
        self.assertEqual(scan.kept, set())


class ScanKeepListTest(unittest.TestCase):
    """the keep list as the scan marks it."""

    def test_the_keep_list_marks_the_folders_that_stay(self) -> None:
        root = tmp_tree(
            {
                "2026-09-23": {"zzz": {}},
                "ZZZZ-keep": {"zzz": {}},
                "mine": {"zzz": {}},
                "keep-me": {"zzz": {}},
            }
        )
        self.addCleanup(remove_tree, root)

        scan = scan_tree(root, ["mine", "keep-*"])

        for kept in ("2026-09-23", "ZZZZ-keep", "mine", "keep-me"):
            self.assertIn(os.path.join(root, kept), scan.kept)
        self.assertNotIn(os.path.join(root, "2026-09-23", "zzz"), scan.kept)

    def test_names_that_only_resemble_a_keep_rule_are_not_marked(self) -> None:
        root = tmp_tree({"cache": {"inner": {}}, "downloads2": {"inner": {}}})
        self.addCleanup(remove_tree, root)

        scan = scan_tree(root, ["downloads", "keep-*"])

        self.assertEqual(scan.kept, set())
