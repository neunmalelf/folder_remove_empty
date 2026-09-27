"""tests of the mark set: which vacant folders a run removes."""

import os
import unittest

from remove_empty_folder_core import scan_tree
from tests.folder_remove_empty.testhelpers import remove_tree, tmp_tree


class MarkDeletesTest(unittest.TestCase):
    """the keep rule of a vacant folder and its parent."""

    def test_a_kept_folder_stays_while_its_parent_stays(self) -> None:
        root = tmp_tree({"holder": {".cache": {}, "file.txt": "x"}})
        self.addCleanup(remove_tree, root)
        holder = os.path.join(root, "holder")

        deletes = scan_tree(root, []).mark_deletes()

        self.assertNotIn(os.path.join(holder, ".cache"), deletes)
        self.assertNotIn(holder, deletes)

    def test_a_kept_folder_goes_with_its_removed_parent(self) -> None:
        root = tmp_tree({"holder": {".cache": {}}})
        self.addCleanup(remove_tree, root)
        holder = os.path.join(root, "holder")

        deletes = scan_tree(root, []).mark_deletes()

        self.assertIn(holder, deletes)
        self.assertIn(os.path.join(holder, ".cache"), deletes)
        self.assertNotIn(root, deletes)

    def test_a_kept_folder_stays_when_only_kept_folders_hold_the_parent(self) -> None:
        root = tmp_tree({"ZZZZ_outer": {"ZZZZ_inner": {"empty": {}}}})
        self.addCleanup(remove_tree, root)
        outer = os.path.join(root, "ZZZZ_outer")
        inner = os.path.join(outer, "ZZZZ_inner")

        deletes = scan_tree(root, []).mark_deletes()

        self.assertIn(os.path.join(inner, "empty"), deletes)
        self.assertNotIn(inner, deletes)
        self.assertNotIn(outer, deletes)

    def test_a_kept_folder_with_an_extra_name_goes_with_its_parent(self) -> None:
        root = tmp_tree({"holder": {"mine": {}}})
        self.addCleanup(remove_tree, root)
        holder = os.path.join(root, "holder")

        deletes = scan_tree(root, ["mine"]).mark_deletes()

        self.assertIn(holder, deletes)
        self.assertIn(os.path.join(holder, "mine"), deletes)


if __name__ == "__main__":
    unittest.main()
