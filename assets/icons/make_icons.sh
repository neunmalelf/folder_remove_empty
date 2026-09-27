#!/usr/bin/env bash
#
# Draw the app icon of folder_remove_empty and write it in the sizes a desktop
# asks for: a purple rectangle with the white letters "fr" in the middle. Every
# size is drawn at its own resolution, so the small ones stay sharp instead of
# being blurred down from a big drawing.
#
# Usage:
#   icons/make_icons.sh
#
# Outputs:
#   Writes folder_remove_empty-<pixels>.png for 16, 24, 32, 48, 64, 128, 256
#   and 512 pixels into the folder of this script, overwriting what is there,
#   and names the written sizes on stdout.
#
# Environment Variables:
#   None. The drawing, the font and the sizes are set in this script.
#
# Exit Codes:
#   0   every size was drawn
#   1   ImageMagick is missing, or a drawing failed
#
# Needs ImageMagick 7 (magick) and a DejaVu font (dejavu-sans-fonts); without a
# font ImageMagick writes the files without the letters. The drawn files are
# committed, so this script only runs when the icon changes.

__VERSION__="0.3.20260923194014"

set -euo pipefail

ICON_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
NAME="folder_remove_empty"
# The purple of the background and the font of the two letters.
PURPLE="#6a1b9a"
FONT="DejaVu-Sans-Bold"
# The letters take 60% of the icon, so "fr" fills the middle without touching
# the edges. Every size is drawn at its own resolution, which stays sharp on a
# panel icon that the desktop scales down no further.
LETTER_SHARE=60
SIZES=(16 24 32 48 64 128 256 512)

for size in "${SIZES[@]}"; do
    magick -size "${size}x${size}" "xc:${PURPLE}" \
        -fill white -font "$FONT" -pointsize "$((size * LETTER_SHARE / 100))" \
        -gravity center -annotate 0 'fr' "${ICON_DIR}/${NAME}-${size}.png"
done

echo "wrote ${#SIZES[@]} icons (${SIZES[*]}) into ${ICON_DIR}"
