# FOLDER_REMOVE_EMPTY

FOLDER_REMOVE_EMPTY removes every empty folder below a start folder, deepest
first. The start folder itself is never removed, only the folders below it.

One run removes a whole chain of nested empty folders: a folder is rated empty
as soon as its last empty subfolder is gone, so the deepest folder goes first
and its parent follows in the same run.

## 

The icon is a purple rectangle with the white letters "fr" in the middle, drawn
in every size a desktop asks for (16, 24, 32, 48, 64, 128, 256 and 512 pixels)
below `icons/`. All sizes are embedded in the binary; the largest one goes to
the window manager, the whole set is installed into the icon folder of the
desktop by `make install`.

`make icons` draws the set again. It needs ImageMagick 7 (`magick`) and a
DejaVu font:

```bash
sudo dnf install ImageMagick dejavu-sans-fonts
```

## Development

Every version is logged in [ChangeLog.md](ChangeLog.md), the user-facing
highlights of a release are in [NEWS](NEWS).

The code is one library package plus the thin command in `cmd/`. The core is
free of any user interface: `ScanTree` rates the folders, `MarkDeletes` marks
what goes and `Execute` works the job against an `Observer`. The window and the
terminal reporter are two implementations of that interface, so the rules are
covered by tests without a window.

```bash
make test                       # the suite, including the window tests
go test ./...                   # without the Makefile
```

The window tests run headless: Gio widgets work without a window, so the state
and the layout are checked without opening one. `TestUILayoutDrawsTheWindow`
draws the whole window headless after a run.

## License

MIT, see [LICENSE](LICENSE).
