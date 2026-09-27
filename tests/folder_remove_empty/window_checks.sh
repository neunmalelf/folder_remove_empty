#!/usr/bin/env bash
# window_checks.sh - run the window test modules of folder_remove_empty.
#   usage: tests/folder_remove_empty/window_checks.sh [options]
#   options:
#     -h, --help        show this help and exit
#     --version         show the version and exit
#     --list            print the test modules it runs and exit
#     --assert-private  refuse to run unless the display is a private one
#
# The module list lives here, so `make check-gui`, the private re-run of the
# display guard and a hand-run check all use the same one. Moving the run to a
# private display is the caller's job
# (`python3 -m remove_empty_folder_display --wrap-sh '... window_checks.sh'`);
# with --assert-private this script refuses a session display by itself.
#
# The window tests need a display; without one pytest skips them and says so.

__VERSION__="1.0.20260927223500Z"

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON="${PYTHON:-python3}"

MODULES=(
    "tests/folder_remove_empty/test_gui.py"
    "tests/folder_remove_empty/test_gui_reference.py"
)

ASSERT_PRIVATE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h | --help)
            sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        --version)
            echo "window_checks.sh v${__VERSION__}"
            exit 0
            ;;
        --list)
            printf '%s\n' "${MODULES[@]}"
            exit 0
            ;;
        --assert-private)
            ASSERT_PRIVATE=1
            shift
            ;;
        *)
            echo "window_checks.sh: unknown option '$1' (try --help)" >&2
            exit 2
            ;;
    esac
done

if [[ "$ASSERT_PRIVATE" == "1" ]]; then
    display="$("$PYTHON" -m remove_empty_folder_display --print)"
    case "$display" in
        private\ display*) ;;
        *)
            printf 'window_checks.sh: refusing %s (the window checks need a private display)\n' "$display" >&2
            exit 1
            ;;
    esac
fi

cd "$ROOT"
exec "$PYTHON" -m pytest -q "${MODULES[@]}"
