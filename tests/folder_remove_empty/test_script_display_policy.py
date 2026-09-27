"""the scripts that open the window stay off the screen the user works on.

`remove_empty_folder_display.py` holds the policy and the window tests enforce it
for themselves; this module extends the same rule to the repository scripts: a
script that runs the program must either go through `xvfb-run` (or call the
policy's `--check`), or be one of the two places that are meant to open the real
window for a human being - `_run` and `_menu`'s "r" entry. `make run` is the
third such place, but it spells the program as `$(PYTHON) -m $(APP)`, so the
textual discovery below does not see it.

The discovery is textual on purpose: this is a repository policy about shell
recipes, not about program behaviour, and a new script that pops windows on the
desktop has to be caught before somebody's work is interrupted again.
"""

import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAKEFILE = os.path.join(ROOT, "Makefile")
HOOK = os.path.join(ROOT, "hooks", "pre-commit")
ROOT_SCRIPTS = ("_run", "_menu", "_tests", "_install", "_build", "_check_pins", "_check_version")

# the scripts that may open the real window: a human being asked for it
SESSION_OPENERS = {"_run", "_menu"}

# a run of the program that opens the window: the module run, or the installed
# console script at a command position (never a path or a bare mention)
WINDOW_RUN = re.compile(
    r"python3\s+-m\s+folder_remove_empty\b"
    r"|^folder_remove_empty\b"
    r"|(?:[;&(`]|\$\()\s*folder_remove_empty\b"
)
# a pure output flag keeps the window closed
PURE_OUTPUT = re.compile(r"--(?:no-gui|help|version|print-man|print-tldr)")
# a real Tk use, not the word in a help text
TK_USE = re.compile(r"^\s*(?:import|from)\s+tkinter\b|remove_empty_folder_gui", re.MULTILINE)
# a private display is asked for through xvfb-run or through the policy module
PRIVATE_MECHANISM = ("xvfb-run", "remove_empty_folder_display")


def script_paths() -> list[str]:
    """collect the repository scripts that may run the program
    usage: script_paths()
    returns: the absolute paths of the root scripts, the hook, the asset scripts
             and the Makefile

    example: script_paths()

    """
    paths = [os.path.join(ROOT, name) for name in ROOT_SCRIPTS]
    paths.append(HOOK)
    paths.append(MAKEFILE)
    assets = os.path.join(ROOT, "assets")
    if os.path.isdir(assets):
        paths.extend(
            os.path.join(assets, name)
            for name in sorted(os.listdir(assets))
            if name.endswith(".sh")
        )
    return [path for path in paths if os.path.isfile(path)]


def reads(path: str) -> str:
    """read a repository script
    usage: reads <PATH>
    returns: the text of the file

    example: reads(os.path.join(ROOT, "assets", "make_screenshots.sh"))

    """
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def runs_the_window(text: str) -> bool:
    """report whether a script text runs the program with a window
    usage: runs_the_window <TEXT>
    returns: True when a non-comment line invokes the program without a pure
             output flag

    example: runs_the_window(reads(path))

    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if not WINDOW_RUN.search(line):
            continue
        if PURE_OUTPUT.search(line):
            continue
        return True
    return False


def openers() -> set[str]:
    """find the scripts that run the window without a private display
    usage: openers()
    returns: the repository-relative names of those scripts

    example: openers()

    """
    found: set[str] = set()
    for path in script_paths():
        text = reads(path)
        if not runs_the_window(text):
            continue
        if any(mechanism in text for mechanism in PRIVATE_MECHANISM):
            continue
        found.add(os.path.relpath(path, ROOT))
    return found


class ScriptDisplayPolicyTest(unittest.TestCase):
    """every script that opens the window goes through the private-display policy."""

    def test_the_session_openers_are_the_known_ones(self) -> None:
        self.assertEqual(
            openers(),
            SESSION_OPENERS,
            "a script that runs the program changed: as long as a human being asked for "
            "the window, add it to SESSION_OPENERS; otherwise wrap it in xvfb-run and it "
            "leaves this set",
        )

    def test_every_tk_script_is_private(self) -> None:
        for path in script_paths():
            name = os.path.relpath(path, ROOT)
            if name in SESSION_OPENERS:
                continue
            text = reads(path)
            if not runs_the_window(text) and not TK_USE.search(text):
                continue
            with self.subTest(script=name):
                self.assertTrue(
                    any(mechanism in text for mechanism in PRIVATE_MECHANISM),
                    f"{name} opens a window without xvfb-run or "
                    "remove_empty_folder_display: it would flash the screen you work on",
                )

    def test_the_policy_refuses_the_session_display(self) -> None:
        away = {"DISPLAY": ":0", "FOLDER_REMOVE_EMPTY_SESSION_DISPLAY": ":0"}
        refused = self.run_policy({**away}, ["--check"])
        self.assertEqual(refused.returncode, 1, refused.stdout + refused.stderr)
        self.assertIn("refusing to open a window on :0", refused.stderr)

        private = self.run_policy({**away, "FOLDER_REMOVE_EMPTY_PRIVATE_DISPLAY": "1"}, ["--check"])
        self.assertEqual(private.returncode, 0, private.stdout + private.stderr)

        asked = self.run_policy({**away, "FOLDER_REMOVE_EMPTY_GUI_DISPLAY": "session"}, ["--check"])
        self.assertEqual(asked.returncode, 0, asked.stdout + asked.stderr)

        where = self.run_policy(
            {**away, "FOLDER_REMOVE_EMPTY_PRIVATE_DISPLAY": "1", "DISPLAY": ":99"}, ["--print"]
        )
        self.assertEqual(where.returncode, 0, where.stdout + where.stderr)
        self.assertIn("private display :99", where.stdout)

    def run_policy(
        self, environment: dict[str, str], argv: list[str]
    ) -> subprocess.CompletedProcess[str]:
        """run the display policy in a controlled environment
        usage: run_policy <ENVIRONMENT> <ARGV>
        returns: the completed process of `python3 -m remove_empty_folder_display ARGV`

        example: run_policy({"DISPLAY": ":0"}, ["--check"])

        """
        clean = {key: value for key, value in os.environ.items() if key != "DISPLAY"}
        policy_keys = [key for key in clean if key.startswith("FOLDER_REMOVE_EMPTY_")]
        for key in policy_keys:
            del clean[key]
        return subprocess.run(
            [sys.executable, "-m", "remove_empty_folder_display", *argv],
            capture_output=True,
            text=True,
            env={**clean, **environment},
            cwd=ROOT,
        )


if __name__ == "__main__":
    unittest.main()
