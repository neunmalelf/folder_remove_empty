"""tests of the pause and stop control of one run."""

import threading
import unittest

from remove_empty_folder_core import RunControl


def ask_in_background(control: RunControl) -> tuple[threading.Thread, list[bool]]:
    """ask one checkpoint of CONTROL in a worker thread and collect its answer
    usage: ask_in_background <CONTROL>
    returns: the running worker and the list its answer lands in

    example: worker, answers = ask_in_background(RunControl())

    """
    answers: list[bool] = []
    worker = threading.Thread(target=lambda: answers.append(control.checkpoint()))
    worker.start()
    return worker, answers


class RunControlTest(unittest.TestCase):
    """the checkpoint, the pause and the stop."""

    def test_a_fresh_control_lets_the_run_go_on(self) -> None:
        control = RunControl()

        self.assertTrue(control.checkpoint())
        self.assertTrue(control.checkpoint())

    def test_pause_holds_the_run_until_resume(self) -> None:
        control = RunControl()
        self.assertTrue(control.pause())

        worker, answers = ask_in_background(control)
        worker.join(timeout=0.5)
        self.assertTrue(worker.is_alive(), "a paused run must wait in front of a folder")

        self.assertFalse(control.pause())
        worker.join(timeout=5)
        self.assertFalse(worker.is_alive(), "the resumed run must go on")
        self.assertEqual(answers, [True])

    def test_stop_releases_a_waiting_checkpoint_and_ends_the_run(self) -> None:
        control = RunControl()
        control.pause()

        worker, answers = ask_in_background(control)
        control.stop()
        worker.join(timeout=5)

        self.assertFalse(worker.is_alive(), "a stopped run must not keep waiting")
        self.assertEqual(answers, [False])
        self.assertFalse(control.checkpoint())

    def test_pause_after_stop_is_a_no_op_that_reports_false(self) -> None:
        control = RunControl()
        control.stop()

        self.assertFalse(control.pause())
        self.assertFalse(control.pause())
        self.assertFalse(control.checkpoint())


if __name__ == "__main__":
    unittest.main()
