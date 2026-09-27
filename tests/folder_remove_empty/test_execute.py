"""tests of one run: the phases, the removals, the refusals and the stop."""

import os
import unittest
from unittest import mock

from remove_empty_folder_core import (
    Action,
    Event,
    FolderRemoveEmptyError,
    Options,
    execute,
    resolve_start,
)
from tests.folder_remove_empty.testhelpers import FakeObserver, remove_tree, tmp_tree


def chain(root: str) -> list[str]:
    """create a chain of three nested empty folders below ROOT, the deepest first
    usage: chain <ROOT>
    returns: the three folders, deepest first

    example: chain("/tmp/tree")

    """
    paths = [
        os.path.join(root, "chain"),
        os.path.join(root, "chain", "inner"),
        os.path.join(root, "chain", "inner", "deepest"),
    ]
    os.makedirs(paths[-1])
    return list(reversed(paths))


class ResolveStartTest(unittest.TestCase):
    """the path check in front of a run."""

    def test_an_empty_path_means_the_current_folder(self) -> None:
        self.assertEqual(resolve_start(""), os.path.abspath(os.getcwd()))

    def test_a_given_path_is_made_absolute_and_cleaned(self) -> None:
        root = tmp_tree({"sub": {}})
        self.addCleanup(remove_tree, root)

        self.assertEqual(resolve_start(os.path.join(root, "sub", "..")), root)

    def test_a_missing_path_is_refused(self) -> None:
        root = tmp_tree({})
        self.addCleanup(remove_tree, root)
        missing = os.path.join(root, "nope")

        with self.assertRaises(FolderRemoveEmptyError) as caught:
            resolve_start(missing)

        self.assertEqual(str(caught.exception), f"the given path does not exist: {missing}")

    def test_a_path_that_is_a_file_is_refused(self) -> None:
        root = tmp_tree({"file.txt": "x"})
        self.addCleanup(remove_tree, root)
        path = os.path.join(root, "file.txt")

        with self.assertRaises(FolderRemoveEmptyError) as caught:
            resolve_start(path)

        self.assertEqual(str(caught.exception), f"the given path is not a folder: {path}")


class EventTextTest(unittest.TestCase):
    """the one-line shape of every outcome."""

    def test_every_outcome_has_its_own_line(self) -> None:
        cases = [
            (Event("/a", Action.REMOVED), "removed: /a"),
            (Event("/a", Action.REMOVED, dry_run=True), "would remove: /a"),
            (Event("/a", Action.KEPT), "excluded, kept: /a"),
            (
                Event("/a", Action.FAILED, err=OSError(13, "Permission denied", "/a")),
                "not removed: /a (remove /a: permission denied)",
            ),
            (
                Event("/a", Action.FAILED, err=OSError(13, "Permission denied")),
                "not removed: /a (permission denied)",
            ),
        ]
        for event, want in cases:
            with self.subTest(action=event.action):
                self.assertEqual(event.text(), want)


class ExecuteChainTest(unittest.TestCase):
    """one run over a chain of nested empty folders."""

    def test_a_dry_run_reports_every_folder_and_touches_nothing(self) -> None:
        root = tmp_tree({})
        self.addCleanup(remove_tree, root)
        deepest, inner, folder = chain(root)

        observer = FakeObserver()
        summary = execute(Options(start_path=root, dry_run=True), observer)

        self.assertEqual(observer.started, root)
        self.assertEqual(observer.currents, [deepest, inner, folder])
        self.assertEqual([event.action for event in observer.events], [Action.REMOVED] * 3)
        self.assertEqual(
            [event.text() for event in observer.events],
            [f"would remove: {path}" for path in (deepest, inner, folder)],
        )
        self.assertEqual(observer.summaries, [summary])
        self.assertTrue(summary.dry_run)
        self.assertEqual(summary.start_path, root)
        self.assertEqual(summary.folders, 3)
        self.assertEqual(summary.removed, 3)
        self.assertEqual(summary.failed, 0)
        self.assertFalse(summary.stopped)
        for path in (deepest, inner, folder):
            self.assertTrue(os.path.isdir(path))

    def test_a_run_removes_the_whole_chain_deepest_first(self) -> None:
        root = tmp_tree({})
        self.addCleanup(remove_tree, root)
        deepest, inner, folder = chain(root)

        observer = FakeObserver()
        summary = execute(Options(start_path=root), observer)

        self.assertEqual(observer.started, root)
        self.assertEqual(observer.currents, [deepest, inner, folder])
        self.assertEqual(
            [event.text() for event in observer.events],
            [f"removed: {path}" for path in (deepest, inner, folder)],
        )
        self.assertEqual(observer.summaries, [summary])
        self.assertEqual(summary.folders, 3)
        self.assertEqual(summary.removed, 3)
        self.assertEqual(summary.failed, 0)
        self.assertFalse(summary.stopped)
        for path in (deepest, inner, folder):
            self.assertFalse(os.path.exists(path))
        self.assertTrue(os.path.isdir(root))

    def test_the_start_folder_is_never_removed(self) -> None:
        root = tmp_tree({"empty": {}})
        self.addCleanup(remove_tree, root)

        first = execute(Options(start_path=root), FakeObserver())

        self.assertEqual((first.folders, first.removed), (1, 1))
        self.assertTrue(os.path.isdir(root))

        observer = FakeObserver()
        second = execute(Options(start_path=root), observer)

        self.assertEqual((second.folders, second.removed), (0, 0))
        self.assertEqual(observer.events, [])
        self.assertEqual(observer.currents, [])
        self.assertTrue(os.path.isdir(root))

    def test_a_folder_holding_a_file_is_left_alone(self) -> None:
        root = tmp_tree({"data": {"empty": {}, "file.txt": "x"}})
        self.addCleanup(remove_tree, root)

        observer = FakeObserver()
        summary = execute(Options(start_path=root), observer)

        self.assertEqual((summary.folders, summary.removed), (2, 1))
        self.assertEqual(observer.folders(Action.REMOVED), [os.path.join(root, "data", "empty")])
        self.assertTrue(os.path.isfile(os.path.join(root, "data", "file.txt")))
        self.assertTrue(os.path.isdir(os.path.join(root, "data")))


class ExecuteKeptFolderTest(unittest.TestCase):
    """the verbose report of a vacant kept folder."""

    def test_verbose_reports_a_vacant_kept_folder(self) -> None:
        root = tmp_tree({"holder": {".cache": {}, "file.txt": "x"}})
        self.addCleanup(remove_tree, root)
        kept = os.path.join(root, "holder", ".cache")

        observer = FakeObserver()
        summary = execute(Options(start_path=root, verbose=True), observer)

        self.assertEqual(summary.folders, 2)
        self.assertEqual(summary.removed, 0)
        self.assertEqual(observer.currents, [kept])
        self.assertEqual(observer.events, [Event(kept, Action.KEPT)])
        self.assertEqual(observer.events[0].text(), f"excluded, kept: {kept}")
        self.assertTrue(os.path.isdir(kept))

    def test_a_run_without_verbose_says_nothing_about_a_kept_folder(self) -> None:
        root = tmp_tree({"holder": {".cache": {}, "file.txt": "x"}})
        self.addCleanup(remove_tree, root)
        kept = os.path.join(root, "holder", ".cache")

        observer = FakeObserver()
        summary = execute(Options(start_path=root), observer)

        self.assertEqual((summary.folders, summary.removed), (2, 0))
        self.assertEqual(observer.events, [])
        self.assertEqual(observer.currents, [])
        self.assertTrue(os.path.isdir(kept))


class ExecuteRefusalTest(unittest.TestCase):
    """a removal the file system refuses."""

    def test_a_refused_removal_is_reported_and_its_parent_is_skipped(self) -> None:
        root = tmp_tree({"readonly": {"empty": {}}})
        self.addCleanup(remove_tree, root)
        parent = os.path.join(root, "readonly")
        refused = os.path.join(parent, "empty")

        def refuse(path: str) -> None:
            raise OSError(13, "Permission denied", path)

        observer = FakeObserver()
        with mock.patch("os.rmdir", side_effect=refuse):
            summary = execute(Options(start_path=root), observer)

        self.assertEqual((summary.folders, summary.removed, summary.failed), (2, 0, 1))
        self.assertEqual(observer.currents, [refused])
        self.assertEqual(len(observer.events), 1)
        failure = observer.events[0]
        self.assertEqual(failure.action, Action.FAILED)
        self.assertEqual(failure.folder, refused)
        self.assertIsInstance(failure.err, OSError)
        self.assertEqual(
            failure.text(), f"not removed: {refused} (remove {refused}: permission denied)"
        )
        self.assertTrue(os.path.isdir(refused))
        self.assertTrue(os.path.isdir(parent))

    def test_a_missing_start_path_is_refused_before_the_run(self) -> None:
        root = tmp_tree({})
        self.addCleanup(remove_tree, root)
        missing = os.path.join(root, "nope")
        observer = FakeObserver()

        with self.assertRaises(FolderRemoveEmptyError) as caught:
            execute(Options(start_path=missing), observer)

        self.assertEqual(str(caught.exception), f"the given path does not exist: {missing}")
        self.assertIsNone(observer.started)
        self.assertEqual(observer.events, [])

    def test_a_start_path_that_is_a_file_is_refused_before_the_run(self) -> None:
        root = tmp_tree({"file.txt": "x"})
        self.addCleanup(remove_tree, root)
        path = os.path.join(root, "file.txt")
        observer = FakeObserver()

        with self.assertRaises(FolderRemoveEmptyError) as caught:
            execute(Options(start_path=path), observer)

        self.assertEqual(str(caught.exception), f"the given path is not a folder: {path}")
        self.assertIsNone(observer.started)
        self.assertEqual(observer.events, [])


class ExecuteStopTest(unittest.TestCase):
    """the checkpoint that ends a run."""

    def test_a_false_checkpoint_stops_the_run_in_front_of_the_next_folder(self) -> None:
        root = tmp_tree({})
        self.addCleanup(remove_tree, root)
        deepest, inner, folder = chain(root)

        observer = FakeObserver([True, False])
        summary = execute(Options(start_path=root), observer)

        self.assertTrue(summary.stopped)
        self.assertEqual(summary.folders, 3)
        self.assertEqual(summary.removed, 1)
        self.assertEqual(observer.currents, [deepest])
        self.assertEqual(observer.events, [Event(deepest, Action.REMOVED)])
        self.assertEqual(observer.summaries, [summary])
        self.assertFalse(os.path.exists(deepest))
        self.assertTrue(os.path.isdir(inner))
        self.assertTrue(os.path.isdir(folder))

    def test_a_stop_before_the_first_folder_removes_nothing(self) -> None:
        root = tmp_tree({})
        self.addCleanup(remove_tree, root)
        deepest, inner, folder = chain(root)

        observer = FakeObserver([False])
        summary = execute(Options(start_path=root), observer)

        self.assertTrue(summary.stopped)
        self.assertEqual(summary.folders, 3)
        self.assertEqual(summary.removed, 0)
        self.assertEqual(observer.currents, [])
        self.assertEqual(observer.events, [])
        self.assertEqual(observer.summaries, [summary])
        for path in (deepest, inner, folder):
            self.assertTrue(os.path.isdir(path))


if __name__ == "__main__":
    unittest.main()
