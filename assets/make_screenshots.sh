#!/bin/bash
# make_screenshots.sh - draw the two documentation screenshots of the window.
#
#   usage: assets/make_screenshots.sh [OUT_DIR]
#   arguments:
#     [OUT_DIR]  where window-light.png and window-dark.png are written
#                (default: assets)
#
# Both shots are taken on a private Xvfb display, so nothing of the real desktop
# ends up in them. The light one is the running program with a scratch settings
# file that fixes the geometry (the crop offsets are known from it). The window
# always starts in the light theme (spec §7.1), so the dark one opens the window
# through the module and switches the theme once before the capture.
#
# Needs Xvfb, xvfb-run and ImageMagick. The generated PNGs are committed, so this
# script only runs when the window changes.
#
# The private display is not a nicety here: the wrapper (`--wrap`) moves the
# capture to one, and the child refuses anything but a private display, so a
# capture can never take over the screen you are working on. The window geometry
# of the private server is the wrapper's (the policy module owns it).

__VERSION__="1.1.20260927201306Z"

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-$ROOT/assets}"
WIDTH=960
HEIGHT=720
OFFSET_X=160
OFFSET_Y=150

for tool in xvfb-run import magick python3; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        printf 'make_screenshots.sh: %s is missing (needs Xvfb, xvfb-run and ImageMagick)\n' "$tool" >&2
        exit 1
    fi
done

mkdir -p "$OUT_DIR"
# a fixed scratch root keeps the generated PNGs byte-identical between runs: the
# status line of the window names the folder it is checking
SCRATCH="${TMPDIR:-/tmp}/folder_remove_empty-shots"
rm -rf "$SCRATCH"
mkdir -p "$SCRATCH"
trap 'rm -rf "$SCRATCH"' EXIT

# a small tree with one empty chain, so the status line shows a usable folder
mkdir -p "$SCRATCH/tree/a/b"
mkdir -p "$SCRATCH/home/.config/folder_remove_empty"
printf '[window]\nwidth = %s\nheight = %s\nx = %s\ny = %s\n' \
    "$WIDTH" "$HEIGHT" "$OFFSET_X" "$OFFSET_Y" \
    > "$SCRATCH/home/.config/folder_remove_empty/folder_remove_empty.conf"

# the dark shot needs the window module and one theme switch
cat > "$SCRATCH/dark_shot.py" <<'PYEOF'
"""open the window, switch it to the dark palette and hold it open."""
import sys
import tkinter as tk

from remove_empty_folder_config import SavedSettings
from remove_empty_folder_core import Options
from remove_empty_folder_gui import MainWindow
from remove_empty_folder_version import APP_NAME_VERBOSE, __VERSION__

tree = sys.argv[1]
root = tk.Tk()
root.title(f"{APP_NAME_VERBOSE} {__VERSION__}")
root.geometry("960x720+160+150")
window = MainWindow(root, Options(start_path=tree), SavedSettings())
window.toggle_theme()
root.after(20000, root.destroy)
root.mainloop()
PYEOF

python3 -m remove_empty_folder_display --wrap bash -s -- \
    "$SCRATCH" "$OUT_DIR" "$ROOT" "$WIDTH" "$HEIGHT" "$OFFSET_X" "$OFFSET_Y" <<'CHILD'
set -euo pipefail

# The shots need a private display unconditionally (a clean desktop is the whole
# point), so a session display is refused even when GUI_DISPLAY=session asks for
# it elsewhere.
display="$(python3 -m remove_empty_folder_display --print)"
case "$display" in
    private\ display*) ;;
    *)
        printf 'make_screenshots.sh: refusing %s (the shots need a private display)\n' "$display" >&2
        exit 1
        ;;
esac

scratch="$1"
out="$2"
root="$3"
width="$4"
height="$5"
offset_x="$6"
offset_y="$7"
export PYTHONPATH="$root${PYTHONPATH:+:$PYTHONPATH}"

crop() {
    magick "$1" -crop "${width}x${height}+${offset_x}+${offset_y}" +repage -strip "$2"
}

# the light shot: the program itself, its geometry coming from the scratch config
HOME="$scratch/home" python3 -m folder_remove_empty "$scratch/tree" >/dev/null 2>&1 &
app=$!
sleep 4
import -window root "$scratch/light.png"
kill "$app" 2>/dev/null || true
wait "$app" 2>/dev/null || true
sleep 1
crop "$scratch/light.png" "$out/window-light.png"

# the dark shot: the same window with the dark palette
python3 "$scratch/dark_shot.py" "$scratch/tree" >/dev/null 2>&1 &
app=$!
sleep 5
import -window root "$scratch/dark.png"
kill "$app" 2>/dev/null || true
wait "$app" 2>/dev/null || true
crop "$scratch/dark.png" "$out/window-dark.png"
CHILD

identify "$OUT_DIR/window-light.png" "$OUT_DIR/window-dark.png"
printf 'wrote %s/window-light.png and %s/window-dark.png\n' "$OUT_DIR" "$OUT_DIR"
