"""tests of the tkinter window, its dialogs and the settings it remembers.

The module needs a display: it runs directly when a tkinter root can be opened,
The module needs a display, and it never takes the one the user is working on:
`test_private_display.py` re-runs the window modules under `xvfb-run`, while these
classes skip themselves in the parent run (todo/goal.md §8). Ask for the session
screen explicitly with `FOLDER_REMOVE_EMPTY_GUI_DISPLAY=session`.
"""

import contextlib
import os
import shutil
import tempfile
import time
import tkinter
import unittest
from collections.abc import Callable
from unittest import mock

import remove_empty_folder_config as config
import remove_empty_folder_gui as gui
from remove_empty_folder_config import SavedSettings, load, save
from remove_empty_folder_core import Action, Event, Options, Summary
from remove_empty_folder_gui import (
    CURRENT_PLACEHOLDER,
    FILTER_ALL,
    FILTER_KEPT,
    FILTER_NOT_REMOVED,
    FILTER_REMOVED,
    PATH_PLACEHOLDER,
    FolderPicker,
    GuiObserver,
    HelpDialog,
    MainWindow,
    _set_icon,
    run_gui,
)
from remove_empty_folder_theme import DARK, LIGHT
from remove_empty_folder_version import __VERSION__, APP_NAME_VERBOSE
from tests.folder_remove_empty import gui_display
from tests.folder_remove_empty.testhelpers import remove_tree, tmp_tree

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@unittest.skipIf(*gui_display.skip_arguments())
class WindowTestCase(unittest.TestCase):
    """a built window on a fresh root, with a settings file inside a temp folder."""

    def setUp(self) -> None:
        self.root = tkinter.Tk()
        self.addCleanup(self._destroy_root)
        self.folder = tempfile.mkdtemp(prefix="fre-gui-")
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)
        self.config_file = os.path.join(self.folder, "folder_remove_empty.conf")
        self.config_backup = config.CONFIG_PATH
        config.CONFIG_PATH = self.config_file
        self.addCleanup(setattr, config, "CONFIG_PATH", self.config_backup)
        self.window = MainWindow(self.root, Options(), SavedSettings())
        self.root.update()

    def _destroy_root(self) -> None:
        """destroy the test root once, ignoring a root a test closed already."""
        with contextlib.suppress(AttributeError, tkinter.TclError):
            self.root.destroy()

    def _lines(self) -> list[str]:
        """return the rendered history lines without the trailing newline."""
        return self.window.history_text.get("1.0", "end").rstrip("\n").splitlines()

    def _pump(self, predicate: Callable[[], bool], timeout: float = 10.0) -> bool:
        """run the event loop until PREDICATE holds or the timeout passes."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.root.update()
            if predicate():
                return True
            time.sleep(0.01)
        return False

    def _open_fake_run(self, tree: str) -> GuiObserver:
        """register a scripted run on the window and return its observer."""
        _generation, updates, control = self.window._open_run()
        observer = GuiObserver(updates, control)
        observer.start(tree)
        observer.current(f"{tree}/a")
        observer.done(Event(f"{tree}/a", Action.REMOVED))
        observer.current(f"{tree}/b")
        observer.done(Event(f"{tree}/b", Action.REMOVED, dry_run=True))
        observer.current(f"{tree}/c")
        observer.done(Event(f"{tree}/c", Action.FAILED, err=OSError(13, "Permission denied")))
        observer.done(Event(f"{tree}/d", Action.KEPT))
        observer.summary(Summary(start_path=tree, folders=4, removed=2))
        self.window._drain()
        return observer


class LayoutTest(WindowTestCase):
    """the nine rows of spec §7.2, their labels and their widgets."""

    def test_the_nine_rows_come_in_the_documented_order(self) -> None:
        rows = {
            "start_label": 0,
            "path_entry": 0,
            "browse_button": 0,
            "status_label": 1,
            "options_frame": 2,
            "excludes_entry": 3,
            "filter_frame": 4,
            "button_row": 5,
            "current_entry": 6,
            "history_label": 7,
            "history_text": 8,
        }
        for name, expected in rows.items():
            widget = getattr(self.window, name)
            self.assertEqual(int(widget.grid_info()["row"]), expected, name)

    def test_the_rows_carry_the_documented_labels(self) -> None:
        self.assertEqual(self.window.start_label.cget("text"), "Start path")
        self.assertEqual(self.window.browse_button.cget("text"), "Browse…")
        self.assertEqual(
            self.window.dry_run_button.cget("text"),
            "Dry run - print the folders that would be removed and remove nothing",
        )
        self.assertEqual(
            self.window.verbose_button.cget("text"),
            "Verbose - report every kept folder that was left in place",
        )
        self.assertEqual(self.window.excludes_label.cget("text"), "Extra excludes")
        self.assertEqual(self.window.filter_label.cget("text"), "Show in history")
        self.assertEqual(
            [button.cget("text") for button in self.window.filter_buttons],
            ["All", "Removed", "Kept", "Not removed"],
        )
        self.assertEqual(self.window.current_label.cget("text"), "Current folder")
        self.assertEqual(self.window.current_entry.get(), CURRENT_PLACEHOLDER)
        self.assertEqual(self.window.history_label.cget("text"), "History")
        self.assertIn("bold", str(self.window.history_label.cget("font")))

    def test_the_button_row_carries_the_five_buttons_side_by_side(self) -> None:
        self.assertEqual(
            [button.cget("text") for button in self.window.button_row.winfo_children()],
            ["Help", "Dark mode", "Exit", "Pause", "Start"],
        )
        for column in range(5):
            self.assertEqual(int(self.window.button_row.grid_columnconfigure(column)["weight"]), 1)
        self.assertEqual(
            int(self.window.dry_run_button.grid_info()["row"]),
            int(self.window.verbose_button.grid_info()["row"]),
        )

    def test_the_history_list_is_bordered_and_scrollable(self) -> None:
        self.assertEqual(int(self.window.history_text.cget("highlightthickness")), 1)
        self.assertEqual(str(self.window.history_text.cget("state")), "disabled")

    def test_the_fields_carry_the_documented_placeholders(self) -> None:
        self.window._put_value(self.window.path_entry, "")
        self.assertEqual(self.window.path_entry.get(), PATH_PLACEHOLDER)
        self.assertEqual(self.window._value(self.window.path_entry), "")
        self.window.path_entry.event_generate("<FocusIn>")
        self.root.update()
        self.assertEqual(self.window.path_entry.get(), "")
        self.window.path_entry.event_generate("<FocusOut>")
        self.root.update()
        self.assertEqual(self.window.path_entry.get(), PATH_PLACEHOLDER)


class StartUpTest(WindowTestCase):
    """the start-up values of the fields and the live status line, spec §7.2/§7.3."""

    def test_the_path_field_defaults_to_the_current_folder(self) -> None:
        self.assertEqual(self.window._value(self.window.path_entry), os.getcwd())
        self.assertFalse(self.window.dry_run.get())
        self.assertFalse(self.window.verbose.get())
        self.assertEqual(self.window._value(self.window.excludes_entry), "")
        self.assertEqual(self.window.filter_var.get(), FILTER_ALL)
        self.assertFalse(self.window.dark)

    def test_the_options_fill_the_fields(self) -> None:
        tree = tmp_tree({"a": {}})
        self.addCleanup(remove_tree, tree)
        window = MainWindow(
            self.root,
            Options(start_path=tree, dry_run=True, verbose=True, excludes="keep-*"),
            SavedSettings(),
        )
        self.assertEqual(window._value(window.path_entry), tree)
        self.assertTrue(window.dry_run.get())
        self.assertTrue(window.verbose.get())
        self.assertEqual(window._value(window.excludes_entry), "keep-*")

    def test_the_settings_fill_the_fields_the_options_leave_open(self) -> None:
        settings = SavedSettings(
            dry_run=True, verbose=True, excludes="tmp-*", history_filter=FILTER_KEPT, dark=True
        )
        window = MainWindow(self.root, Options(), settings)
        self.assertTrue(window.dry_run.get())
        self.assertTrue(window.verbose.get())
        self.assertEqual(window._value(window.excludes_entry), "tmp-*")
        self.assertEqual(window.filter_var.get(), FILTER_KEPT)
        self.assertFalse(window.dark)

    def test_the_options_win_over_the_settings(self) -> None:
        window = MainWindow(
            self.root,
            Options(dry_run=True, excludes="cli-*"),
            SavedSettings(dry_run=False, excludes="file-*", history_filter=FILTER_ALL),
        )
        self.assertTrue(window.dry_run.get())
        self.assertEqual(window._value(window.excludes_entry), "cli-*")

    def test_the_status_line_reports_a_usable_and_an_unusable_path(self) -> None:
        tree = tmp_tree({"a": {}})
        self.addCleanup(remove_tree, tree)
        self.window._set_path(tree)
        self.assertEqual(self.window.status_label.cget("text"), f"path exists: {tree}")
        self.assertEqual(str(self.window.status_label.cget("foreground")), LIGHT.success)
        self.window._set_path(os.path.join(tree, "not-there"))
        self.assertTrue(
            str(self.window.status_label.cget("text")).startswith(
                "ERROR: the given path does not exist:"
            )
        )
        self.assertEqual(str(self.window.status_label.cget("foreground")), LIGHT.danger)

    def test_typing_rechecks_the_status_line_through_the_debounce(self) -> None:
        self.window._put_value(self.window.path_entry, "/nowhere/at/all")
        self.window.path_entry.focus_force()
        self.root.update()
        self.window.path_entry.event_generate("<KeyRelease>")
        self.root.update()
        self.assertIsNotNone(self.window._check_after)
        self.assertTrue(
            self._pump(lambda: "ERROR:" in str(self.window.status_label.cget("text")))
        )


class FakeRunTest(WindowTestCase):
    """a scripted run through the observer, the queue and the drain, spec §7.5."""

    def test_the_current_folder_and_one_line_per_outcome(self) -> None:
        self._open_fake_run("/tmp/tree")
        self.assertEqual(self.window.current_folder, "/tmp/tree/c")
        self.assertEqual(self.window.current_entry.get(), "/tmp/tree/c")
        lines = self._lines()
        self.assertEqual(lines[0], "start folder: /tmp/tree")
        self.assertIn("removed: /tmp/tree/a", lines)
        self.assertIn("would remove: /tmp/tree/b", lines)
        self.assertIn(
            Event("/tmp/tree/c", Action.FAILED, err=OSError(13, "Permission denied")).text(), lines
        )
        self.assertIn("excluded, kept: /tmp/tree/d", lines)
        self.assertEqual(len(lines), 6)
        self.assertEqual(
            [item.kind for item in self.window.items],
            ["", FILTER_REMOVED, FILTER_REMOVED, FILTER_NOT_REMOVED, FILTER_KEPT, ""],
        )

    def test_the_closing_line_of_a_stopped_run(self) -> None:
        _generation, updates, control = self.window._open_run()
        GuiObserver(updates, control).summary(
            Summary(start_path="/tmp/tree", folders=2, removed=1, stopped=True)
        )
        self.window._drain()
        self.assertEqual(self._lines()[-2:], ["stopped", "1 empty folder(s) removed"])

    def test_the_counters_of_a_dry_run_and_of_a_run_without_removals(self) -> None:
        _generation, updates, control = self.window._open_run()
        observer = GuiObserver(updates, control)
        observer.summary(Summary(start_path="/tmp/tree", dry_run=True, folders=4, removed=2))
        self.window._drain()
        self.assertEqual(self._lines(), ["dry run: 2 of 4 folder(s) would be removed"])
        observer.summary(Summary(start_path="/tmp/tree", folders=0))
        self.window._drain()
        self.assertEqual(self._lines()[-1], "no empty folder found")

    def test_the_refusals_line_follows_the_counters(self) -> None:
        _generation, updates, control = self.window._open_run()
        GuiObserver(updates, control).summary(
            Summary(start_path="/tmp/tree", folders=2, removed=1, failed=1)
        )
        self.window._drain()
        self.assertEqual(self._lines(), ["1 empty folder(s) removed", "1 folder(s) kept"])

    def test_a_filter_change_re_renders_the_whole_list(self) -> None:
        self._open_fake_run("/tmp/tree")
        note_start, note_close = "start folder: /tmp/tree", "2 empty folder(s) removed"
        self.window.filter_var.set(FILTER_REMOVED)
        self.window._on_filter()
        self.assertEqual(
            self._lines(),
            [note_start, "removed: /tmp/tree/a", "would remove: /tmp/tree/b", note_close],
        )
        self.window.filter_var.set(FILTER_KEPT)
        self.window._on_filter()
        self.assertEqual(self._lines(), [note_start, "excluded, kept: /tmp/tree/d", note_close])
        self.window.filter_var.set(FILTER_NOT_REMOVED)
        self.window._on_filter()
        self.assertEqual(
            self._lines(),
            [
                note_start,
                Event("/tmp/tree/c", Action.FAILED, err=OSError(13, "Permission denied")).text(),
                note_close,
            ],
        )

    def test_an_older_run_never_updates_the_window(self) -> None:
        old_generation, old_updates, old_control = self.window._open_run()
        _new_generation, new_updates, new_control = self.window._open_run()
        GuiObserver(old_updates, old_control).current("/old/folder")
        self.window._drain()
        self.assertEqual(self.window.current_folder, "")
        GuiObserver(new_updates, new_control).current("/new/folder")
        self.window._apply(old_generation, "current", "/stale/folder")
        self.window._drain()
        self.assertEqual(self.window.current_folder, "/new/folder")


class RunTest(WindowTestCase):
    """the run in flight: the labels, a real removal and the failures, spec §7.3/§7.5."""

    def test_a_real_run_removes_the_empty_folders_and_follows_the_current_folder(self) -> None:
        tree = tmp_tree({"gone": {"deep": {}}, "keep": {"file.txt": "x"}})
        self.addCleanup(remove_tree, tree)
        self.window._set_path(tree)
        self.window._start()
        self.assertTrue(
            self._pump(lambda: self.window._control is None),
            self.window.history_text.get("1.0", "end"),
        )
        self.assertFalse(os.path.exists(os.path.join(tree, "gone")))
        self.assertTrue(os.path.isfile(os.path.join(tree, "keep", "file.txt")))
        lines = self._lines()
        self.assertEqual(lines[0], f"start folder: {tree}")
        self.assertIn(f"removed: {os.path.join(tree, 'gone', 'deep')}", lines)
        self.assertIn(f"removed: {os.path.join(tree, 'gone')}", lines)
        self.assertEqual(lines[-1], "2 empty folder(s) removed")
        self.assertEqual(self.window.current_folder, os.path.join(tree, "gone"))
        self.assertEqual(self.window.start_button.cget("text"), "Start")
        self.assertEqual(str(self.window.pause_button.cget("state")), "disabled")

    def test_the_start_pause_and_exit_labels(self) -> None:
        self.assertEqual(self.window.start_button.cget("text"), "Start")
        self.assertEqual(self.window.pause_button.cget("text"), "Pause")
        self.assertEqual(str(self.window.pause_button.cget("state")), "disabled")
        self.assertEqual(self.window.exit_button.cget("text"), "Exit")
        self.window._open_run()
        self.assertEqual(self.window.start_button.cget("text"), "Restart")
        self.assertEqual(str(self.window.pause_button.cget("state")), "normal")
        self.window._toggle_pause()
        self.assertEqual(self.window.pause_button.cget("text"), "Resume")
        self.window._toggle_pause()
        self.assertEqual(self.window.pause_button.cget("text"), "Pause")
        self.window._finish_run(self.window._generation)
        self.assertEqual(self.window.start_button.cget("text"), "Start")
        self.assertEqual(str(self.window.pause_button.cget("state")), "disabled")

    def test_a_refused_path_adds_an_error_line_and_starts_nothing(self) -> None:
        self.window._set_path("/nowhere/at/all")
        self.window._start()
        self.assertIsNone(self.window._control)
        self.assertEqual(len(self.window.items), 1)
        item = self.window.items[0]
        self.assertTrue(
            item.text.startswith("ERROR: the given path does not exist: /nowhere/at/all")
        )
        self.assertEqual(item.importance, "error")
        self.assertEqual(item.kind, FILTER_NOT_REMOVED)
        self.assertEqual(self.window.start_button.cget("text"), "Start")

    def test_a_run_takes_the_path_and_the_trimmed_excludes_of_the_fields(self) -> None:
        tree = tmp_tree({"a": {}})
        self.addCleanup(remove_tree, tree)
        self.window._set_path(tree)
        self.window._put_value(self.window.excludes_entry, " keep-* : tmp ")
        with mock.patch.object(gui, "execute") as runner:
            self.window._start()
            self.assertTrue(self._pump(lambda: self.window._control is None))
        options = runner.call_args.args[0]
        self.assertEqual(options.start_path, tree)
        self.assertEqual(options.excludes, "keep-* : tmp")
        self.assertFalse(options.no_gui)

    def test_browse_takes_the_choice_and_falls_back_without_a_standard_dialog(self) -> None:
        tree = tmp_tree({"alpha": {}})
        self.addCleanup(remove_tree, tree)
        self.window._set_path("")
        with mock.patch.object(gui.filedialog, "askdirectory", return_value=tree):
            self.window._browse()
        self.assertEqual(self.window._value(self.window.path_entry), tree)
        self.window._set_path("")
        with mock.patch.object(
            gui.filedialog, "askdirectory", side_effect=tkinter.TclError("no dialog")
        ):
            self.window._browse()
        dialog = self.window.dialog
        assert isinstance(dialog, FolderPicker)
        self.assertEqual(dialog.folder, os.getcwd())
        self.assertEqual(self.window._value(self.window.path_entry), "")

    def test_a_broken_worker_becomes_an_error_line_and_keeps_the_window_open(self) -> None:
        tree = tmp_tree({"a": {}})
        self.addCleanup(remove_tree, tree)
        self.window._set_path(tree)
        with mock.patch.object(gui, "execute", side_effect=ValueError("boom")):
            self.window._start()
            self.assertTrue(
                self._pump(lambda: self.window._control is None),
                self.window.history_text.get("1.0", "end"),
            )
        self.assertIn("ERROR: internal failure: boom", self.window.history_text.get("1.0", "end"))
        self.assertEqual(self.window.start_button.cget("text"), "Start")
        self.assertTrue(self.root.winfo_exists())


class ThemeTest(WindowTestCase):
    """the theme toggle repaints every widget, spec §7.3/§7.7."""

    def test_the_toggle_flips_the_colours_and_the_button_label(self) -> None:
        self.assertEqual(self.window.theme_button.cget("text"), "Dark mode")
        self.assertEqual(str(self.window.history_text.cget("background")), LIGHT.bg)
        self.assertEqual(str(self.window.path_entry.cget("highlightbackground")), LIGHT.border)
        self.assertEqual(
            str(self.window.history_text.tag_cget("removed", "foreground")), LIGHT.success
        )
        self.window.toggle_theme()
        self.assertTrue(self.window.dark)
        self.assertEqual(self.window.theme_button.cget("text"), "Light mode")
        self.assertEqual(str(self.window.history_text.cget("background")), DARK.bg)
        self.assertEqual(str(self.window.path_entry.cget("highlightbackground")), DARK.border)
        self.assertEqual(str(self.window.status_label.cget("foreground")), DARK.success)
        self.assertEqual(str(self.window.help_button.cget("activebackground")), DARK.border)
        self.assertEqual(
            str(self.window.history_text.tag_cget("removed", "foreground")), DARK.success
        )


class AccentTest(WindowTestCase):
    """no control is filled with the purple accent (user request 2026-09-27)."""

    FILL_OPTIONS = ("background", "activebackground", "selectcolor", "selectbackground",
                    "troughcolor")

    def test_no_widget_is_filled_with_the_accent(self) -> None:
        for dark in (False, True):
            if dark:
                self.window.toggle_theme()
            theme = DARK if dark else LIGHT
            for widget in self.window._widgets():
                supported = widget.keys()
                for option in self.FILL_OPTIONS:
                    if option not in supported:
                        continue
                    with self.subTest(dark=dark, widget=widget.winfo_class(), option=option):
                        self.assertNotEqual(str(widget.cget(option)), theme.accent)

    def test_the_indicators_and_the_hover_are_not_the_accent(self) -> None:
        self.assertEqual(str(self.window.dry_run_button.cget("selectcolor")), LIGHT.bg)
        self.assertEqual(str(self.window.verbose_button.cget("selectcolor")), LIGHT.bg)
        for button in self.window.filter_buttons:
            with self.subTest(filter=button.cget("text")):
                self.assertEqual(str(button.cget("selectcolor")), LIGHT.bg)
        self.assertEqual(str(self.window.help_button.cget("activebackground")), LIGHT.border)
        self.assertEqual(str(self.window.path_entry.cget("selectbackground")), LIGHT.fg)
        self.assertEqual(str(self.window.path_entry.cget("selectforeground")), LIGHT.bg)


class CloseTest(WindowTestCase):
    """closing the window remembers its state and drops late updates, spec §12/§7.5."""

    def test_the_close_saves_the_window_state(self) -> None:
        self.root.update()
        self.window.dry_run.set(True)
        self.window._put_value(self.window.excludes_entry, "keep-*,tmp")
        self.window.filter_var.set(FILTER_KEPT)
        self.window._on_filter()
        self.window.toggle_theme()
        self.window.exit_button.invoke()
        settings = load()
        self.assertTrue(settings.dry_run)
        self.assertFalse(settings.verbose)
        self.assertEqual(settings.excludes, "keep-*,tmp")
        self.assertEqual(settings.history_filter, FILTER_KEPT)
        self.assertTrue(settings.dark)
        self.assertIsNotNone(settings.geometry)
        assert settings.geometry is not None
        self.assertEqual(len(settings.geometry), 4)
        self.assertGreater(settings.geometry[0], 0)

    def test_a_closed_window_drops_late_updates(self) -> None:
        generation, updates, control = self.window._open_run()
        self.window._close_window()
        GuiObserver(updates, control).current("/late/folder")
        self.window._apply(generation, "current", "/late/folder")
        self.window._drain()
        self.assertEqual(self.window.current_folder, "")
        self.assertEqual(self.window.items, [])

    def test_starting_a_run_does_not_write_the_settings_file(self) -> None:
        tree = tmp_tree({"a": {}})
        self.addCleanup(remove_tree, tree)
        self.assertFalse(os.path.exists(self.config_file))
        self.window._set_path(tree)
        self.window._start()
        self.assertTrue(self._pump(lambda: self.window._control is None))
        self.assertFalse(os.path.exists(self.config_file))


class PickerTest(WindowTestCase):
    """the built-in folder picker and the help dialog, spec §7.6/§8.2."""

    def test_the_picker_lists_one_button_per_subfolder(self) -> None:
        tree = tmp_tree({"beta": {}, "alpha": {"inner": {}}, "note.txt": "x"})
        self.addCleanup(remove_tree, tree)
        picker = FolderPicker(self.window, tree)
        self.assertEqual(self.window.frame.grid_info(), {})
        self.assertEqual(picker.heading.cget("text"), "Choose folder")
        self.assertEqual(picker.folder_label.cget("text"), tree)
        self.assertEqual(picker.error_label.cget("text"), "")
        self.assertEqual([button.cget("text") for button in picker.buttons], ["alpha", "beta"])
        picker.buttons[0].invoke()
        self.assertEqual(picker.folder, os.path.join(tree, "alpha"))
        self.assertEqual([button.cget("text") for button in picker.buttons], ["inner"])
        picker.up_button.invoke()
        self.assertEqual(picker.folder, tree)

    def test_the_picker_selects_the_folder_and_cancels_without_touching_it(self) -> None:
        tree = tmp_tree({"alpha": {}})
        self.addCleanup(remove_tree, tree)
        picker = FolderPicker(self.window, tree)
        picker.select_button.invoke()
        self.assertIsNone(self.window.dialog)
        self.assertEqual(self.window._value(self.window.path_entry), tree)
        self.assertEqual(self.window.status_label.cget("text"), f"path exists: {tree}")
        self.assertNotEqual(self.window.frame.grid_info(), {})
        self.window._put_value(self.window.path_entry, "")
        picker = FolderPicker(self.window, tree)
        picker.cancel_button.invoke()
        self.assertIsNone(self.window.dialog)
        self.assertEqual(self.window._value(self.window.path_entry), "")

    def test_the_picker_reports_a_folder_it_cannot_read(self) -> None:
        if os.geteuid() == 0:
            self.skipTest("root reads a folder without permissions")
        folder = tempfile.mkdtemp(prefix="fre-gui-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        blocked = os.path.join(folder, "blocked")
        os.mkdir(blocked)
        os.chmod(blocked, 0)
        self.addCleanup(os.chmod, blocked, 0o700)
        picker = FolderPicker(self.window, blocked)
        self.assertTrue(str(picker.error_label.cget("text")).startswith("ERROR: "))
        self.assertEqual(picker.buttons, [])

    def test_the_help_dialog_shows_the_usage_text_and_closes(self) -> None:
        self.window.help_button.invoke()
        dialog = self.window.dialog
        assert isinstance(dialog, HelpDialog)
        self.assertEqual(dialog.heading.cget("text"), "Help")
        self.assertEqual(self.window.frame.grid_info(), {})
        text = dialog.text.get("1.0", "end")
        self.assertIn("Usage: folder_remove_empty [OPTIONS] [PATH]", text)
        self.assertIn("--dryrun", text)
        dialog.ok_button.invoke()
        self.assertIsNone(self.window.dialog)
        self.assertNotEqual(self.window.frame.grid_info(), {})


@unittest.skipIf(*gui_display.skip_arguments())
class RunGuiTest(unittest.TestCase):
    """run_gui builds the window of spec §7.1 and returns 0."""

    def setUp(self) -> None:
        self.roots: list[tkinter.Tk] = []
        self.folder = tempfile.mkdtemp(prefix="fre-gui-run-")
        self.addCleanup(shutil.rmtree, self.folder, ignore_errors=True)
        self.config_backup = config.CONFIG_PATH
        config.CONFIG_PATH = os.path.join(self.folder, "folder_remove_empty.conf")
        self.addCleanup(setattr, config, "CONFIG_PATH", self.config_backup)

        def mainloop(root: tkinter.Misc) -> None:
            assert isinstance(root, tkinter.Tk)
            self.roots.append(root)
            root.update()

        self.patcher = mock.patch.object(tkinter.Misc, "mainloop", mainloop)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.addCleanup(self._destroy_roots)

    def _destroy_roots(self) -> None:
        """destroy every root a run_gui call left behind."""
        for root in self.roots:
            with contextlib.suppress(AttributeError, tkinter.TclError):
                root.destroy()

    def test_run_gui_builds_the_window_and_returns_zero(self) -> None:
        save(SavedSettings(geometry=(800, 600, 10, 20)))
        self.assertEqual(run_gui(Options()), 0)
        root = self.roots[0]
        self.assertEqual(root.title(), f"{APP_NAME_VERBOSE} {__VERSION__}")
        self.assertIn("800x600", root.geometry())
        self.assertTrue(root.winfo_exists())

    def test_run_gui_falls_back_to_the_default_geometry(self) -> None:
        self.assertEqual(run_gui(Options()), 0)
        self.assertIn(gui.DEFAULT_GEOMETRY, self.roots[0].geometry())

    def test_the_icon_file_loads(self) -> None:
        root = tkinter.Tk()
        self.roots.append(root)
        icon = _set_icon(root)
        self.assertIsNotNone(icon)
        assert icon is not None
        self.assertEqual(icon.width(), 512)
