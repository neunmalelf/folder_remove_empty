"""the guard that keeps the window tests off the screen the user is working on.

`gui_display.py` holds the policy; this module is the collected part of it: when
a private display is wanted it re-runs the window checks (`window_checks.sh`,
which owns the module list) under `xvfb-run`, and inside that private run it
asserts that the session display was really left alone.
"""

import os
import unittest

from tests.folder_remove_empty import gui_display

HERE = os.path.dirname(os.path.abspath(__file__))
WINDOW_CHECKS = os.path.join(HERE, "window_checks.sh")


@unittest.skipUnless(
    gui_display.private_display_wanted(),
    "already on a private display or the session display was asked for",
)
class PrivateDisplayGuardTest(unittest.TestCase):
    """run the window tests on a private display, not on the user's screen."""

    def test_the_window_tests_pass_on_a_private_display(self) -> None:
        result = gui_display.run_under_xvfb(["bash", WINDOW_CHECKS, "--assert-private"])
        self.assertEqual(
            result.returncode,
            0,
            f"the private run failed:\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}",
        )


@unittest.skipUnless(gui_display.PRIVATE, "not the private run")
class PrivateDisplayUsedTest(unittest.TestCase):
    """inside the private run: prove the session display was not touched."""

    def test_the_display_is_not_the_session_one(self) -> None:
        session = os.environ.get(gui_display.SESSION_MARKER)
        if session is None:
            self.skipTest("the session display was unset, nothing to compare")
        self.assertNotEqual(os.environ.get("DISPLAY"), session)


if __name__ == "__main__":
    unittest.main()
