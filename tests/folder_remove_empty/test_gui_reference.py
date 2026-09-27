"""structural capture of the window: the fourth fidelity group.

The dump is not a screenshot: it records the widget rows, their classes, the
texts, the start-up values and the states, so a structural drift shows up as
one diffable file. Pixel geometry is deliberately left out — it follows the
desktop theme, not this program.

Regenerate the fixture after an intended change with

    python3 -m tests.folder_remove_empty.test_gui_reference
"""

import os
import tkinter
import unittest

from remove_empty_folder_config import SavedSettings
from remove_empty_folder_core import Options
from remove_empty_folder_gui import MainWindow
from remove_empty_folder_version import __VERSION__, APP_NAME_VERBOSE
from tests.folder_remove_empty import gui_display

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "reference", "gui_window.txt")

# the fixed options the dump is taken with, so it does not depend on the
# current folder or on the settings file of the machine that runs it
OPTIONS = Options(start_path="/tmp", dry_run=True, excludes="keep-*")

# the fill options the accent must never reach (user request 2026-09-27); the
# dump records them so a purple indicator cannot slip back in unnoticed
COLOUR_OPTIONS = ("background", "activebackground", "selectcolor", "selectbackground")


def _value_lines(root: tkinter.Tk, widget: tkinter.Misc, window: MainWindow) -> list[str]:
    """describe the value-carrying state of one widget
    usage: _value_lines <ROOT> <WIDGET> <WINDOW>
    returns: the extra lines for that widget, empty for a plain widget

    example: _value_lines(root, window.dry_run_button, window)

    """
    lines: list[str] = []
    if isinstance(widget, (tkinter.Checkbutton, tkinter.Radiobutton)):
        variable = widget.cget("variable")
        current = root.getvar(variable)
        if isinstance(widget, tkinter.Radiobutton):
            lines.append(f"selected={current == widget.cget('value')}")
        else:
            lines.append(f"value={bool(current)}")
    if isinstance(widget, tkinter.Entry):
        placeholders = window._placeholders  # noqa: SLF001 - the dump is internal
        placeholder = placeholders.get(widget)
        lines.append(f"value={widget.get()!r}")
        lines.append(f"placeholder={placeholder!r}")
        state = str(widget.cget("state"))
        if state != "normal":
            lines.append(f"state={state}")
    if isinstance(widget, tkinter.Text):
        lines.append(f"lines={int(widget.index('end-1c').split('.')[0])}")
        lines.append(f"state={widget.cget('state')}")
    if isinstance(widget, tkinter.Button):
        state = str(widget.cget("state"))
        if state != "normal":
            lines.append(f"state={state}")
    supported = widget.keys()
    colours = [f"{name}={widget.cget(name)}" for name in COLOUR_OPTIONS if name in supported]
    if colours:
        lines.append("colors " + " ".join(colours))
    return lines


def _walk(root: tkinter.Tk, widget: tkinter.Misc, window: MainWindow, depth: int) -> list[str]:
    """describe one widget and, indented, everything it holds
    usage: _walk <ROOT> <WIDGET> <WINDOW> <DEPTH>
    returns: the dump lines of that subtree

    example: _walk(root, window.frame, window, 0)

    """
    configured = widget.keys()
    text = str(widget.cget("text")) if "text" in configured else ""
    bold = "font" in configured and "bold" in str(widget.cget("font"))
    font = "bold" if bold else ""
    head = f"{'  ' * depth}{widget.winfo_class()}"
    if text:
        head += f" {text!r}"
    if font:
        head += f" font={font}"
    lines = [head]
    lines.extend(f"{'  ' * (depth + 1)}{extra}" for extra in _value_lines(root, widget, window))
    children = [child for child in widget.winfo_children()]
    for child in children:
        lines.extend(_walk(root, child, window, depth + 1))
    return lines


def dump(root: tkinter.Tk, window: MainWindow) -> str:
    """describe the whole window as diffable text
    usage: dump <ROOT> <WINDOW>
    returns: the dump text, ending with one newline

    example: dump(root, window)

    """
    title = root.title().replace(__VERSION__, "<VERSION>")
    lines = [
        f"title: {title}",
        f"options: start_path={OPTIONS.start_path!r} dry_run={OPTIONS.dry_run}",
        f"status: {window.status_label.cget('text')!r}",
        f"filter: {window.filter_var.get()!r}",
        f"theme: {'dark' if window.dark else 'light'}",
    ]
    lines.extend(_walk(root, window.frame, window, 0))
    return "\n".join(lines) + "\n"


def capture() -> str:
    """open a window with the fixed options and dump it
    usage: capture
    returns: the dump of a fresh window

    example: capture()

    """
    root = tkinter.Tk()
    try:
        root.title(f"{APP_NAME_VERBOSE} {__VERSION__}")
        window = MainWindow(root, OPTIONS, SavedSettings())
        root.update()
        return dump(root, window)
    finally:
        root.destroy()


@unittest.skipIf(*gui_display.skip_arguments())
class WindowStructureTest(unittest.TestCase):
    """the committed structure of the window matches the built window."""

    def test_the_window_dump_matches_the_fixture(self) -> None:
        with open(FIXTURE, encoding="utf-8") as handle:
            expected = handle.read()
        self.assertEqual(capture(), expected)

    def test_the_dump_names_the_nine_rows(self) -> None:
        text = capture()
        for marker in (
            "Label 'Start path'",
            "Button 'Browse…'",
            "Checkbutton",
            "Label 'Extra excludes'",
            "Label 'Show in history'",
            "Button 'Help'",
            "Button 'Exit'",
            "Button 'Pause'",
            "Button 'Start'",
            "Label 'Current folder'",
            "Label 'History'",
            "Text",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)


if __name__ == "__main__":
    with open(FIXTURE, "w", encoding="utf-8") as out:
        _ = out.write(capture())
    print(f"wrote {FIXTURE}")
