"""the tkinter window of folder_remove_empty: the form, the history and the dialogs.

A port of ui.go. The engine is GUI-free and blocking, so one run works in one
`threading.Thread`, reports through the `Observer` interface into a
`queue.Queue`, and the window drains that queue from a `root.after` loop. A
per-run generation token makes the newest run the only owner of the window, so
"Restart" replaces a live run and closing drops late updates (spec §7.5).
"""

from __future__ import annotations

import contextlib
import functools
import os
import queue
import threading
import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import filedialog, scrolledtext

import remove_empty_folder_config as config
from remove_empty_folder_config import SavedSettings
from remove_empty_folder_core import (
    Action,
    Event,
    FolderRemoveEmptyError,
    Observer,
    Options,
    RunControl,
    Summary,
    execute,
    resolve_start,
)
from remove_empty_folder_options import usage
from remove_empty_folder_theme import DARK, LIGHT, Theme, importance_color, theme_button_label
from remove_empty_folder_version import __VERSION__, APP_NAME_VERBOSE

# the size the window opens with when the settings file carries no geometry.
DEFAULT_GEOMETRY = "960x720"

# the interval of the queue drain and the debounce of the path check, in ms.
DRAIN_INTERVAL = 50
PATH_CHECK_INTERVAL = 200

# the history filters of spec §9; a line whose kind is empty passes everyone.
FILTER_ALL = "All"
FILTER_REMOVED = "Removed"
FILTER_KEPT = "Kept"
FILTER_NOT_REMOVED = "Not removed"
FILTERS = (FILTER_ALL, FILTER_REMOVED, FILTER_KEPT, FILTER_NOT_REMOVED)

# the importance of one history line, spec §7.4; every label is a colour tag of
# the history list and is read by remove_empty_folder_theme.importance_color.
IMPORTANCE_REMOVED = "removed"
IMPORTANCE_DRY = "dry"
IMPORTANCE_KEPT = "kept"
IMPORTANCE_REFUSED = "refused"
IMPORTANCE_ERROR = "error"
IMPORTANCE_NOTE = "note"
IMPORTANCES = (
    IMPORTANCE_REMOVED,
    IMPORTANCE_DRY,
    IMPORTANCE_KEPT,
    IMPORTANCE_REFUSED,
    IMPORTANCE_ERROR,
    IMPORTANCE_NOTE,
)

# the placeholders spec §7.2 shows in the three fields while they hold no text.
PATH_PLACEHOLDER = "folder to scan (default: the current folder)"
EXCLUDES_PLACEHOLDER = (
    "names that are never removed, : separated, * at the end keeps every name starting with it"
)
CURRENT_PLACEHOLDER = "no folder yet"

# the labels of the option checkbuttons and the file dialogs of spec §7.2/§8.
DRY_RUN_LABEL = "Dry run - print the folders that would be removed and remove nothing"
VERBOSE_LABEL = "Verbose - report every kept folder that was left in place"
CHOOSE_FOLDER_TITLE = "Choose folder"

# the icon files of spec §7.1, the largest first.
ICON_NAMES = ("folder_remove_empty-512.png", "folder_remove_empty-32.png")


@dataclass(frozen=True)
class HistoryItem:
    """one line of the history list
    usage: HistoryItem <TEXT> <IMPORTANCE> <KIND>
    returns: the line as the list shows it

    example: HistoryItem("removed: /tmp/tree/a", "removed", "Removed")

    """

    # the line as it is shown.
    text: str
    # the importance that colours the line.
    importance: str
    # the history filter the line belongs to; "" passes every filter.
    kind: str


class GuiObserver(Observer):
    """hand the progress of one run to the window as plain data, spec §7.5
    usage: GuiObserver <UPDATES> <CONTROL>
    returns: the observer that only puts (kind, payload) tuples into the queue

    example: GuiObserver(queue.Queue(), RunControl())

    """

    def __init__(self, updates: queue.Queue[tuple[str, object]], control: RunControl) -> None:
        """remember the queue and the control of the run this observer belongs to
        usage: __init__ <UPDATES> <CONTROL>
        returns: nothing

        example: GuiObserver(queue.Queue(), RunControl())

        """
        self._updates = updates
        self._control = control

    def start(self, start_path: str) -> None:
        """offer the start folder of the run to the window
        usage: start <START_PATH>
        returns: nothing

        example: observer.start("/tmp/tree")

        """
        self._updates.put(("start", start_path))

    def current(self, folder: str) -> None:
        """offer the folder that is rated or removed next to the window
        usage: current <FOLDER>
        returns: nothing

        example: observer.current("/tmp/tree/a")

        """
        self._updates.put(("current", folder))

    def done(self, event: Event) -> None:
        """offer the outcome of one folder to the window
        usage: done <EVENT>
        returns: nothing

        example: observer.done(Event("/tmp/tree/a", Action.REMOVED))

        """
        self._updates.put(("done", event))

    def summary(self, summary: Summary) -> None:
        """offer the closing counters of the run to the window
        usage: summary <SUMMARY>
        returns: nothing

        example: observer.summary(Summary(start_path="/tmp/tree"))

        """
        self._updates.put(("summary", summary))

    def checkpoint(self) -> bool:
        """hold the run while the window is paused and end it when it was stopped
        usage: checkpoint
        returns: False when the run was stopped and must end

        example: observer.checkpoint()

        """
        return self._control.checkpoint()


class MainWindow:
    """the frame of the program: the nine rows of spec §7.2 and the run in flight
    usage: MainWindow <ROOT> <OPTIONS> <SETTINGS>
    returns: the window, built and painted in the light theme

    example: MainWindow(tkinter.Tk(), Options(), SavedSettings())

    """

    def __init__(self, root: tk.Tk, options: Options, settings: SavedSettings) -> None:
        """build the form, the history and the drain loop, spec §7.2/§7.5
        usage: __init__ <ROOT> <OPTIONS> <SETTINGS>
        returns: nothing

        example: MainWindow(tkinter.Tk(), Options(start_path="/tmp/tree"), SavedSettings())

        """
        self.root = root
        self.dark = False
        self.theme: Theme = LIGHT
        self.items: list[HistoryItem] = []
        self.filter = settings.history_filter if settings.history_filter in FILTERS else FILTER_ALL
        self.current_folder = ""
        self.paused = False
        self.dialog: HelpDialog | FolderPicker | None = None
        self.icon: tk.PhotoImage | None = None
        self._closed = False
        self._control: RunControl | None = None
        self._updates: queue.Queue[tuple[str, object]] | None = None
        self._thread: threading.Thread | None = None
        self._generation = 0
        self._after_id: str | None = None
        self._check_after: str | None = None
        self._placeholders: dict[tk.Entry, str] = {}
        self._history_tags = IMPORTANCES
        self._build(options, settings)
        self._apply_theme()
        self.root.protocol("WM_DELETE_WINDOW", self._close_window)
        self._after_id = self.root.after(DRAIN_INTERVAL, self._drain)

    def _build(self, options: Options, settings: SavedSettings) -> None:
        """create every widget of the nine rows in the order of spec §7.2
        usage: _build <OPTIONS> <SETTINGS>
        returns: nothing

        example: window._build(Options(), SavedSettings())

        """
        self.frame = tk.Frame(self.root)
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(8, weight=1)

        # row 1: the start path, its text field and the browse button.
        self.start_label = tk.Label(self.frame, text="Start path")
        self.start_label.grid(row=0, column=0, sticky="w")
        self.path_entry = tk.Entry(self.frame, exportselection=False, highlightthickness=1)
        self.path_entry.grid(row=0, column=1, sticky="ew", padx=8)
        self.path_entry.bind("<KeyRelease>", self._on_path_changed)
        self._add_placeholder(self.path_entry, PATH_PLACEHOLDER)
        self.browse_button = tk.Button(self.frame, text="Browse…", command=self._browse)
        self.browse_button.grid(row=0, column=2, sticky="ew")

        # row 2: the live status line.
        self.status_label = tk.Label(self.frame, text="")
        self.status_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 4))

        # row 3: the two option checkbuttons side by side.
        self.options_frame = tk.Frame(self.frame)
        self.options_frame.grid(row=2, column=0, columnspan=3, sticky="ew")
        self.options_frame.columnconfigure(0, weight=1)
        self.options_frame.columnconfigure(1, weight=1)
        self.dry_run = tk.BooleanVar(value=options.dry_run or settings.dry_run)
        self.verbose = tk.BooleanVar(value=options.verbose or settings.verbose)
        self.dry_run_button = tk.Checkbutton(
            self.options_frame, text=DRY_RUN_LABEL, variable=self.dry_run, anchor="w"
        )
        self.dry_run_button.grid(row=0, column=0, sticky="ew")
        self.verbose_button = tk.Checkbutton(
            self.options_frame, text=VERBOSE_LABEL, variable=self.verbose, anchor="w"
        )
        self.verbose_button.grid(row=0, column=1, sticky="ew")

        # row 4: the extra kept names.
        self.excludes_label = tk.Label(self.frame, text="Extra excludes")
        self.excludes_label.grid(row=3, column=0, sticky="w")
        self.excludes_entry = tk.Entry(self.frame, exportselection=False, highlightthickness=1)
        self.excludes_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=(8, 0))
        self._add_placeholder(self.excludes_entry, EXCLUDES_PLACEHOLDER)
        self._put_value(self.excludes_entry, options.excludes or settings.excludes)

        # row 5: the history filter.
        self.filter_label = tk.Label(self.frame, text="Show in history")
        self.filter_label.grid(row=4, column=0, sticky="w", pady=(6, 0))
        self.filter_frame = tk.Frame(self.frame)
        self.filter_frame.grid(row=4, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(6, 0))
        self.filter_var = tk.StringVar(value=self.filter)
        self.filter_buttons: list[tk.Radiobutton] = []
        for column, name in enumerate(FILTERS):
            button = tk.Radiobutton(
                self.filter_frame,
                text=name,
                value=name,
                variable=self.filter_var,
                command=self._on_filter,
            )
            button.grid(row=0, column=column, sticky="w")
            self.filter_buttons.append(button)

        # row 6: the five buttons, equal weight and an 8-unit gap each.
        self.button_row = tk.Frame(self.frame)
        self.button_row.grid(row=5, column=0, columnspan=3, sticky="ew", pady=8)
        self.help_button = tk.Button(self.button_row, text="Help", command=self.open_help)
        self.theme_button = tk.Button(
            self.button_row, text=theme_button_label(self.dark), command=self.toggle_theme
        )
        self.exit_button = tk.Button(self.button_row, text="Exit", command=self._close_window)
        self.pause_button = tk.Button(
            self.button_row, text="Pause", command=self._toggle_pause, state=tk.DISABLED
        )
        self.start_button = tk.Button(self.button_row, text="Start", command=self._start)
        actions = (
            self.help_button,
            self.theme_button,
            self.exit_button,
            self.pause_button,
            self.start_button,
        )
        for column, action_button in enumerate(actions):
            self.button_row.columnconfigure(column, weight=1)
            action_button.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))

        # row 7: the read-only current folder.
        self.current_label = tk.Label(self.frame, text="Current folder")
        self.current_label.grid(row=6, column=0, sticky="w")
        self.current_entry = tk.Entry(self.frame, state="readonly", highlightthickness=1)
        self.current_entry.grid(row=6, column=1, columnspan=2, sticky="ew", padx=(8, 0))
        self._put_current(CURRENT_PLACEHOLDER)

        # row 8: the bold History heading.
        self.history_label = tk.Label(self.frame, text="History", font=self._bold_font())
        self.history_label.grid(row=7, column=0, columnspan=3, sticky="w", pady=4)

        # row 9: the bordered, scrollable history list.
        self.history_text = scrolledtext.ScrolledText(
            self.frame,
            height=10,
            borderwidth=0,
            highlightthickness=1,
            wrap="word",
            state=tk.DISABLED,
        )
        self.history_text.grid(row=8, column=0, columnspan=3, sticky="nsew")
        for tag in self._history_tags:
            self.history_text.tag_configure(tag, foreground=importance_color(tag, self.dark))

        # a given path is the start path; without one the current folder is
        # shown, so the field always names the folder a run would work in.
        path = options.start_path
        if not path:
            try:
                path = resolve_start("")
            except FolderRemoveEmptyError:
                path = ""
        self._put_value(self.path_entry, path)
        self._check_path()

    def _bold_font(self) -> tuple[str, int, str]:
        """name the font of the bold History heading of spec §7.2
        usage: _bold_font
        returns: the family, size and "bold" weight of the heading

        example: window._bold_font()

        """
        default = tkfont.nametofont("TkDefaultFont")
        return (str(default.actual("family")), int(default.actual("size")), "bold")

    def _add_placeholder(self, entry: tk.Entry, text: str) -> None:
        """show TEXT in grey in ENTRY while it stays empty, spec §7.2
        usage: _add_placeholder <ENTRY> <TEXT>
        returns: nothing

        example: window._add_placeholder(entry, "folder to scan (default: the current folder)")

        """
        self._placeholders[entry] = text
        entry.bind("<FocusIn>", self._placeholder_in)
        entry.bind("<FocusOut>", self._placeholder_out)
        self._show_placeholder(entry)

    def _placeholder_in(self, event: tk.Event[tk.Entry]) -> None:
        """clear the grey placeholder when the field takes the focus, spec §7.2
        usage: _placeholder_in <EVENT>
        returns: nothing

        example: window._placeholder_in(event)

        """
        entry = event.widget
        if entry.get() == self._placeholders.get(entry, ""):
            entry.delete(0, tk.END)
            entry.configure(foreground=self.theme.fg)

    def _placeholder_out(self, event: tk.Event[tk.Entry]) -> None:
        """put the grey placeholder back when the field is left empty, spec §7.2
        usage: _placeholder_out <EVENT>
        returns: nothing

        example: window._placeholder_out(event)

        """
        self._show_placeholder(event.widget)

    def _refresh_placeholders(self) -> None:
        """restore the grey placeholder of every empty field after a theme switch
        usage: _refresh_placeholders
        returns: nothing

        example: window._refresh_placeholders()

        """
        for entry in self._placeholders:
            if not entry.get().strip():
                self._show_placeholder(entry)

    def _show_placeholder(self, entry: tk.Entry) -> None:
        """replace the empty text of ENTRY with its grey placeholder
        usage: _show_placeholder <ENTRY>
        returns: nothing

        example: window._show_placeholder(window.path_entry)

        """
        entry.delete(0, tk.END)
        entry.insert(0, self._placeholders.get(entry, ""))
        entry.configure(foreground=self.theme.border)

    def _put_value(self, entry: tk.Entry, text: str) -> None:
        """replace the text of ENTRY with TEXT and drop a grey placeholder
        usage: _put_value <ENTRY> <TEXT>
        returns: nothing

        example: window._put_value(window.path_entry, "/tmp/tree")

        """
        entry.delete(0, tk.END)
        if not text:
            self._show_placeholder(entry)
            return
        entry.insert(0, text)
        entry.configure(foreground=self.theme.fg)

    def _value(self, entry: tk.Entry) -> str:
        """read the text of ENTRY, empty while its grey placeholder is shown
        usage: _value <ENTRY>
        returns: the text the field means, without the grey placeholder

        example: window._value(window.path_entry)

        """
        text = entry.get()
        return "" if text == self._placeholders.get(entry, "") else text

    def _put_current(self, folder: str) -> None:
        """show FOLDER in the read-only Current folder field, spec §7.3
        usage: _put_current <FOLDER>
        returns: nothing

        example: window._put_current("/tmp/tree/a")

        """
        self.current_folder = "" if folder == CURRENT_PLACEHOLDER else folder
        self.current_entry.configure(state=tk.NORMAL)
        self.current_entry.delete(0, tk.END)
        self.current_entry.insert(0, folder)
        self.current_entry.configure(state="readonly")

    def _set_path(self, path: str) -> None:
        """put PATH into the path field and re-run the status check, spec §7.3
        usage: _set_path <PATH>
        returns: nothing

        example: window._set_path("/tmp/tree")

        """
        self._put_value(self.path_entry, path)
        self._check_path()

    def _on_path_changed(self, event: tk.Event[tk.Entry]) -> None:
        """re-check the path field through the debounce while the user types
        usage: _on_path_changed <EVENT>
        returns: nothing

        example: window._on_path_changed(event)

        """
        if self._check_after is not None:
            self.root.after_cancel(self._check_after)
        self._check_after = self.root.after(PATH_CHECK_INTERVAL, self._check_path)

    def _check_path(self) -> None:
        """report in the status line whether the path field names a usable folder
        usage: _check_path
        returns: nothing

        example: window._check_path()

        """
        try:
            absolute = resolve_start(self._value(self.path_entry).strip())
        except FolderRemoveEmptyError as refusal:
            self.status_label.configure(text=f"ERROR: {refusal}", foreground=self.theme.danger)
            return
        self.status_label.configure(text=f"path exists: {absolute}", foreground=self.theme.success)

    def _widgets(self) -> list[tk.Misc]:
        """collect the window and every widget below it for the theme switch
        usage: _widgets
        returns: the widgets of the window, the root first

        example: window._widgets()

        """
        widgets: list[tk.Misc] = [self.root]
        pending: list[tk.Misc] = [self.root]
        while pending:
            for child in pending.pop().winfo_children():
                widgets.append(child)
                pending.append(child)
        return widgets

    def _apply_theme(self) -> None:
        """paint every widget of the window from its theme, spec §7.7
        usage: _apply_theme
        returns: nothing

        example: window._apply_theme()

        """
        theme = self.theme
        for widget in self._widgets():
            _set_option(widget, "background", theme.bg)
            _set_option(widget, "foreground", theme.fg)
            _set_option(widget, "activeforeground", theme.fg)
            _set_option(widget, "highlightbackground", theme.border)
            _set_option(widget, "highlightcolor", theme.border)
            _set_option(widget, "insertbackground", theme.fg)
            _set_option(widget, "readonlybackground", theme.bg)
            _set_option(widget, "troughcolor", theme.bg)
            # a selected field text is painted inverted (theme foreground
            # behind, theme background in front), never with the accent
            _set_option(widget, "selectbackground", theme.fg)
            _set_option(widget, "selectforeground", theme.bg)
            # the accent is deliberately not painted as a fill: a checkbutton,
            # a radio or a text selection with the accent background shows a
            # purple box (user request 2026-09-27). The indicator box of a
            # checkbutton or radio takes the theme background instead, and only
            # a button gets a hover tint, its border grey.
            hover = theme.border if isinstance(widget, tk.Button) else theme.bg
            _set_option(widget, "activebackground", hover)
            _set_option(widget, "selectcolor", theme.bg)
        for tag in self._history_tags:
            self.history_text.tag_configure(tag, foreground=importance_color(tag, self.dark))
        self.theme_button.configure(text=theme_button_label(self.dark))
        self._refresh_placeholders()
        self._check_path()
        self._render_history()

    def toggle_theme(self) -> None:
        """switch the window between the light and the dark theme, spec §7.3
        usage: toggle_theme
        returns: nothing

        example: window.toggle_theme()

        """
        self.dark = not self.dark
        self.theme = DARK if self.dark else LIGHT
        self._apply_theme()

    def _render_history(self) -> None:
        """redraw the history list from the items the current filter shows, spec §9
        usage: _render_history
        returns: nothing

        example: window._render_history()

        """
        self.history_text.configure(state=tk.NORMAL)
        self.history_text.delete("1.0", tk.END)
        for item in self.items:
            if self._shown(item.kind):
                self.history_text.insert(tk.END, item.text + "\n", (self._tag(item.importance),))
        self.history_text.configure(state=tk.DISABLED)
        self.history_text.see(tk.END)

    def _add_item(self, item: HistoryItem) -> None:
        """append one line to the history and keep the list scrolled to its end
        usage: _add_item <ITEM>
        returns: nothing

        example: window._add_item(HistoryItem("removed: /tmp/tree/a", "removed", "Removed"))

        """
        self.items.append(item)
        if not self._shown(item.kind):
            return
        self.history_text.configure(state=tk.NORMAL)
        self.history_text.insert(tk.END, item.text + "\n", (self._tag(item.importance),))
        self.history_text.configure(state=tk.DISABLED)
        self.history_text.see(tk.END)

    def _shown(self, kind: str) -> bool:
        """report whether a line of KIND passes the selected history filter, spec §9
        usage: _shown <KIND>
        returns: True when the line belongs to the filter or to a run note

        example: window._shown("Kept")

        """
        return self.filter == FILTER_ALL or kind == "" or kind == self.filter

    def _tag(self, importance: str) -> str:
        """name the history colour tag of an importance, the note tag when it is unknown
        usage: _tag <IMPORTANCE>
        returns: the tag the line is inserted with

        example: window._tag("removed")

        """
        return importance if importance in self._history_tags else IMPORTANCE_NOTE

    def _on_filter(self) -> None:
        """re-render the history list after the filter selection changed, spec §9
        usage: _on_filter
        returns: nothing

        example: window._on_filter()

        """
        self.filter = self.filter_var.get()
        self._render_history()

    def _browse(self) -> None:
        """open the standard folder dialog and put its choice into the path field, spec §8.1
        usage: _browse
        returns: nothing

        example: window._browse()

        """
        base = self._value(self.path_entry).strip()
        try:
            start = resolve_start(base)
        except FolderRemoveEmptyError:
            try:
                start = resolve_start("")
            except FolderRemoveEmptyError:
                start = base
        try:
            chosen = filedialog.askdirectory(initialdir=start, title=CHOOSE_FOLDER_TITLE)
        except (AttributeError, tk.TclError):
            self.open_picker(start)
            return
        if chosen:
            self._set_path(chosen)

    def open_picker(self, folder: str) -> None:
        """replace the main content with the built-in folder picker, spec §8.2
        usage: open_picker <FOLDER>
        returns: nothing

        example: window.open_picker("/tmp/tree")

        """
        if self.dialog is not None:
            return
        FolderPicker(self, folder)

    def open_help(self) -> None:
        """replace the main content with the help dialog, spec §7.6
        usage: open_help
        returns: nothing

        example: window.open_help()

        """
        if self.dialog is not None:
            return
        HelpDialog(self)

    def close_dialog(self) -> None:
        """drop the open dialog and bring the main content back
        usage: close_dialog
        returns: nothing

        example: window.close_dialog()

        """
        self.dialog = None
        self.frame.grid()

    def _start(self) -> None:
        """check the path field and start a run, replacing a run in flight, spec §7.3
        usage: _start
        returns: nothing

        example: window._start()

        """
        path = self._value(self.path_entry).strip()
        try:
            resolve_start(path)
        except FolderRemoveEmptyError as refusal:
            self._check_path()
            self._add_item(HistoryItem(f"ERROR: {refusal}", IMPORTANCE_ERROR, FILTER_NOT_REMOVED))
            return
        self._begin_run(
            Options(
                start_path=path,
                dry_run=self.dry_run.get(),
                verbose=self.verbose.get(),
                excludes=self._value(self.excludes_entry).strip(),
            )
        )

    def _begin_run(self, options: Options) -> None:
        """work OPTIONS in one thread and hand the window over to it, spec §7.5
        usage: _begin_run <OPTIONS>
        returns: nothing

        example: window._begin_run(Options(start_path="/tmp/tree"))

        """
        _, updates, control = self._open_run()
        thread = threading.Thread(target=self._job, args=(options, updates, control), daemon=True)
        self._thread = thread
        thread.start()

    def _open_run(self) -> tuple[int, queue.Queue[tuple[str, object]], RunControl]:
        """stop the run in flight and make a fresh generation the owner of the window
        usage: _open_run
        returns: the generation token, the queue and the control of the new run

        example: window._open_run()

        """
        if self._control is not None:
            self._control.stop()
        self._generation += 1
        control = RunControl()
        updates: queue.Queue[tuple[str, object]] = queue.Queue()
        self._control = control
        self._updates = updates
        self.paused = False
        self.pause_button.configure(text="Pause")
        self._set_running(True)
        return self._generation, updates, control

    def _job(
        self,
        options: Options,
        updates: queue.Queue[tuple[str, object]],
        control: RunControl,
    ) -> None:
        """work OPTIONS in its own thread and report through UPDATES, spec §7.5
        usage: _job <OPTIONS> <UPDATES> <CONTROL>
        returns: nothing

        example: window._job(Options(start_path="/tmp/tree"), queue.Queue(), RunControl())

        """
        try:
            execute(options, GuiObserver(updates, control))
        except FolderRemoveEmptyError as refusal:
            updates.put(("error", f"ERROR: {refusal}"))
        except Exception as err:  # a broken worker must not close the window, spec §7.5
            updates.put(("error", f"ERROR: internal failure: {err}"))
        finally:
            updates.put(("finish", None))

    def _drain(self) -> None:
        """apply every queued update of the live run and re-arm the drain, spec §7.5
        usage: _drain
        returns: nothing

        example: window._drain()

        """
        if self._closed:
            return
        generation = self._generation
        updates = self._updates
        if updates is not None:
            while True:
                try:
                    kind, payload = updates.get_nowait()
                except queue.Empty:
                    break
                self._apply(generation, kind, payload)
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(DRAIN_INTERVAL, self._drain)

    def _apply(self, generation: int, kind: str, payload: object) -> None:
        """apply one update of run GENERATION and drop an update of an older run
        usage: _apply <GENERATION> <KIND> <PAYLOAD>
        returns: nothing

        example: window._apply(1, "current", "/tmp/tree/a")

        """
        if self._closed or generation != self._generation:
            return
        if kind == "start":
            self._put_current(str(payload))
            self._add_item(HistoryItem(f"start folder: {payload}", IMPORTANCE_NOTE, ""))
        elif kind == "current":
            self._put_current(str(payload))
        elif kind == "done" and isinstance(payload, Event):
            self._add_item(_item_of(payload))
        elif kind == "summary" and isinstance(payload, Summary):
            for item in _summary_items(payload):
                self._add_item(item)
        elif kind == "error":
            self._add_item(HistoryItem(str(payload), IMPORTANCE_ERROR, FILTER_NOT_REMOVED))
        elif kind == "finish":
            self._finish_run(generation)

    def _finish_run(self, generation: int) -> None:
        """return the window to idle after run GENERATION when it still owns it
        usage: _finish_run <GENERATION>
        returns: nothing

        example: window._finish_run(1)

        """
        if generation != self._generation:
            return
        self._control = None
        self._thread = None
        self._set_running(False)

    def _set_running(self, running: bool) -> None:
        """label the Start and Pause buttons for a run in flight or an idle window
        usage: _set_running <RUNNING>
        returns: nothing

        example: window._set_running(True)

        """
        self.start_button.configure(text="Restart" if running else "Start")
        self.pause_button.configure(state=tk.NORMAL if running else tk.DISABLED)
        if not running:
            self.paused = False
            self.pause_button.configure(text="Pause")

    def _toggle_pause(self) -> None:
        """hold the run in flight in front of the next folder or let it go on, spec §7.3
        usage: _toggle_pause
        returns: nothing

        example: window._toggle_pause()

        """
        control = self._control
        if control is None:
            return
        self.paused = control.pause()
        self.pause_button.configure(text="Resume" if self.paused else "Pause")

    def _close_window(self) -> None:
        """stop the run in flight, remember the window state and destroy the root
        usage: _close_window
        returns: nothing

        example: window._close_window()

        """
        if self._closed:
            return
        self._closed = True
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        if self._check_after is not None:
            self.root.after_cancel(self._check_after)
            self._check_after = None
        if self._control is not None:
            self._control.stop()
            self._control = None
        self._save_settings()
        self.root.destroy()

    def _save_settings(self) -> None:
        """write the window state to the settings file, never blocking the close
        usage: _save_settings
        returns: nothing

        example: window._save_settings()

        """
        settings = SavedSettings(
            geometry=(
                self.root.winfo_width(),
                self.root.winfo_height(),
                self.root.winfo_x(),
                self.root.winfo_y(),
            ),
            dry_run=self.dry_run.get(),
            verbose=self.verbose.get(),
            excludes=self._value(self.excludes_entry),
            history_filter=self.filter,
            dark=self.dark,
        )
        with contextlib.suppress(Exception):  # spec §12: a failed save never blocks the close
            config.save(settings)


class HelpDialog:
    """the help dialog of spec §7.6: the usage text in the same root with an OK button
    usage: HelpDialog <WINDOW>
    returns: the dialog, already shown in place of the main content

    example: HelpDialog(window)

    """

    def __init__(self, window: MainWindow) -> None:
        """build the heading, the bordered usage text and the OK button, spec §7.6
        usage: __init__ <WINDOW>
        returns: nothing

        example: HelpDialog(window)

        """
        self.window = window
        self.frame = tk.Frame(window.root)
        self.heading = tk.Label(self.frame, text="Help", font=window._bold_font())
        self.heading.grid(row=0, column=0, sticky="w")
        self.text = scrolledtext.ScrolledText(
            self.frame, height=20, wrap="none", highlightthickness=1, borderwidth=0
        )
        self.text.grid(row=1, column=0, sticky="nsew")
        self.text.insert("1.0", usage())
        self.text.configure(state=tk.DISABLED)
        self.ok_button = tk.Button(self.frame, text="OK", command=self.close)
        self.ok_button.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.frame.rowconfigure(1, weight=1)
        self.frame.columnconfigure(0, weight=1)
        window.frame.grid_remove()
        self.frame.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        window.dialog = self
        window._apply_theme()

    def close(self) -> None:
        """close the dialog and bring the main content back, spec §7.6
        usage: close
        returns: nothing

        example: dialog.close()

        """
        self.frame.destroy()
        self.window.close_dialog()


class FolderPicker:
    """the built-in folder picker of spec §8.2, the fallback without a standard dialog
    usage: FolderPicker <WINDOW> <FOLDER>
    returns: the picker, already shown in place of the main content

    example: FolderPicker(window, "/tmp/tree")

    """

    def __init__(self, window: MainWindow, folder: str) -> None:
        """build the picker at FOLDER and list its subfolders, spec §8.2
        usage: __init__ <WINDOW> <FOLDER>
        returns: nothing

        example: FolderPicker(window, "/tmp/tree")

        """
        self.window = window
        self.folder = folder
        self.error = ""
        self.frame = tk.Frame(window.root)
        self.heading = tk.Label(self.frame, text=CHOOSE_FOLDER_TITLE, font=window._bold_font())
        self.heading.grid(row=0, column=0, sticky="w")
        self.folder_label = tk.Label(self.frame, text=folder, anchor="w")
        self.folder_label.grid(row=1, column=0, sticky="ew", pady=(2, 2))
        self.error_label = tk.Label(self.frame, text="", anchor="w")
        self.error_label.grid(row=2, column=0, sticky="ew")
        self.up_button = tk.Button(self.frame, text="Up", command=self.up)
        self.up_button.grid(row=3, column=0, sticky="w", pady=(4, 4))
        self.list_holder = tk.Frame(self.frame)
        self.list_holder.grid(row=4, column=0, sticky="nsew")
        self.list_holder.rowconfigure(0, weight=1)
        self.list_holder.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self.list_holder, borderwidth=0, highlightthickness=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = tk.Scrollbar(
            self.list_holder, orient="vertical", command=self.canvas.yview
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.list_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.list_frame.bind("<Configure>", self._scroll_region)
        self.buttons: list[tk.Button] = []
        self.bottom_row = tk.Frame(self.frame)
        self.bottom_row.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        self.bottom_row.columnconfigure(0, weight=1)
        self.bottom_row.columnconfigure(1, weight=1)
        self.select_button = tk.Button(self.bottom_row, text="Select", command=self.select)
        self.select_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.cancel_button = tk.Button(self.bottom_row, text="Cancel", command=self.cancel)
        self.cancel_button.grid(row=0, column=1, sticky="ew")
        self.frame.rowconfigure(4, weight=1)
        self.frame.columnconfigure(0, weight=1)
        self.refresh()
        window.frame.grid_remove()
        self.frame.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        window.dialog = self
        window._apply_theme()

    def _scroll_region(self, event: tk.Event[tk.Frame]) -> None:
        """grow the scroll region of the list to the buttons it holds
        usage: _scroll_region <EVENT>
        returns: nothing

        example: picker._scroll_region(event)

        """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def refresh(self) -> None:
        """list the subfolders of the shown folder in alphabetical order, spec §8.2
        usage: refresh
        returns: nothing

        example: picker.refresh()

        """
        self.folder_label.configure(text=self.folder)
        for button in self.buttons:
            button.destroy()
        self.buttons = []
        try:
            with os.scandir(self.folder) as iterator:
                names = sorted(
                    entry.name for entry in iterator if entry.is_dir(follow_symlinks=False)
                )
        except OSError as err:
            self.error = str(err)
            self.error_label.configure(text=f"ERROR: {self.error}")
        else:
            self.error = ""
            self.error_label.configure(text="")
            for name in names:
                button = tk.Button(
                    self.list_frame,
                    text=name,
                    anchor="w",
                    command=functools.partial(self.descend, name),
                )
                button.pack(fill="x")
                self.buttons.append(button)
        self.window._apply_theme()

    def up(self) -> None:
        """move the picker to the parent folder of the one it shows, spec §8.2
        usage: up
        returns: nothing

        example: picker.up()

        """
        parent = os.path.dirname(self.folder)
        if parent and parent != self.folder:
            self.folder = parent
            self.refresh()

    def descend(self, name: str) -> None:
        """move the picker into the subfolder NAME of the folder it shows, spec §8.2
        usage: descend <NAME>
        returns: nothing

        example: picker.descend("backup")

        """
        self.folder = os.path.join(self.folder, name)
        self.refresh()

    def select(self) -> None:
        """put the shown folder into the path field and close the picker, spec §8.2
        usage: select
        returns: nothing

        example: picker.select()

        """
        self.window._set_path(self.folder)
        self.close()

    def cancel(self) -> None:
        """close the picker without touching the path field, spec §8.2
        usage: cancel
        returns: nothing

        example: picker.cancel()

        """
        self.close()

    def close(self) -> None:
        """close the picker and bring the main content back, spec §8.2
        usage: close
        returns: nothing

        example: picker.close()

        """
        self.frame.destroy()
        self.window.close_dialog()


def _set_option(widget: tk.Misc, option: str, value: str) -> None:
    """set one tk option of WIDGET and ignore a widget that does not support it
    usage: _set_option <WIDGET> <OPTION> <VALUE>
    returns: nothing

    example: _set_option(label, "background", "#ffffff")

    """
    with contextlib.suppress(tk.TclError):
        widget.configure(**{option: value})


def _item_of(event: Event) -> HistoryItem:
    """build the history line of one outcome in its colour and filter, spec §7.4
    usage: _item_of <EVENT>
    returns: the line of the outcome

    example: _item_of(Event("/tmp/tree/a", Action.REMOVED))

    """
    if event.action is Action.REMOVED:
        importance = IMPORTANCE_DRY if event.dry_run else IMPORTANCE_REMOVED
        return HistoryItem(event.text(), importance, FILTER_REMOVED)
    if event.action is Action.FAILED:
        return HistoryItem(event.text(), IMPORTANCE_REFUSED, FILTER_NOT_REMOVED)
    return HistoryItem(event.text(), IMPORTANCE_KEPT, FILTER_KEPT)


def _summary_items(summary: Summary) -> list[HistoryItem]:
    """build the closing lines of a run: the stopped flag, the counters, the refusals
    usage: _summary_items <SUMMARY>
    returns: the closing lines in the order of spec §4

    example: _summary_items(Summary(start_path="/tmp/tree", folders=3, removed=3))

    """
    items: list[HistoryItem] = []
    if summary.stopped:
        items.append(HistoryItem("stopped", IMPORTANCE_NOTE, ""))
    if summary.dry_run:
        text = f"dry run: {summary.removed} of {summary.folders} folder(s) would be removed"
    elif summary.removed == 0:
        text = "no empty folder found"
    else:
        text = f"{summary.removed} empty folder(s) removed"
    items.append(HistoryItem(text, IMPORTANCE_NOTE, ""))
    if summary.failed > 0:
        items.append(HistoryItem(f"{summary.failed} folder(s) kept", IMPORTANCE_NOTE, ""))
    return items


def _set_icon(root: tk.Tk) -> tk.PhotoImage | None:
    """put the application icon of spec §7.1 onto ROOT, the largest file first
    usage: _set_icon <ROOT>
    returns: the image to keep alive, None when no icon file could be read

    example: _set_icon(root)

    """
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons")
    for name in ICON_NAMES:
        try:
            icon = tk.PhotoImage(master=root, file=os.path.join(folder, name))
        except tk.TclError:
            continue
        root.iconphoto(True, icon)
        return icon
    return None


def run_gui(options: Options, getenv: Callable[[str], str | None] | None = None) -> int:
    """open the window of OPTIONS and block until it is closed, spec §7.1
    usage: run_gui <OPTIONS> [GETENV]
    returns: 0 when the window was closed again

    example: run_gui(Options(start_path="/data/archive"))

    """
    root = tk.Tk()
    root.title(f"{APP_NAME_VERBOSE} {__VERSION__}")
    settings = config.load()
    geometry = settings.geometry
    if geometry is None:
        root.geometry(DEFAULT_GEOMETRY)
    else:
        root.geometry(f"{geometry[0]}x{geometry[1]}{geometry[2]:+d}{geometry[3]:+d}")
    window = MainWindow(root, options, settings)
    window.icon = _set_icon(root)  # the window keeps the image that carries its icon alive
    root.mainloop()
    return 0
