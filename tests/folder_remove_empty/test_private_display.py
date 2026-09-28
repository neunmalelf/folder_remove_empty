"""the guard that keeps the window tests off the screen the user is working on.

`gui_display.py` holds the policy and this module is the collected part of it:
when a private display is wanted it re-runs the window checks under `xvfb-run`
through the one entry point, `./_tests --gui` (which in turn drives
`tests/folder_remove_empty/window_checks.sh`, the only place that names the
window test modules). That child refuses a session display itself, so the check
that the window never went to the user's screen lives in one place and is in
force for `make test`, `make check-gui` and `make check-313` alike.
"""

import os
import unittest

from tests.folder_remove_empty import gui_display

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TESTS = os.path.join(ROOT, "_tests")


@unittest.skipUnless(
    gui_display.private_display_wanted(),
    "already on a private display or the session display was asked for",
)
class PrivateDisplayGuardTest(unittest.TestCase):
    """run the window tests on a private display, not on the user's screen."""

    def test_the_window_tests_pass_on_a_private_display(self) -> None:
        result = gui_display.run_under_xvfb(["bash", TESTS, "--gui"])
        self.assertEqual(
            result.returncode,
            0,
            f"the private run failed:\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}",
        )


if __name__ == "__main__":
    unittest.main()
