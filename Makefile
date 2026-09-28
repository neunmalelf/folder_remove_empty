# Makefile for the folder_remove_empty tool.
#
# folder_remove_empty is a stdlib-only Python 3.13 program, so every target
# runs through python3. The heavier machinery (the standalone packaging, the
# editable install) stays in the repository scripts; this Makefile is the thin
# entry point for tests, the generated pages, the desktop installation and the
# release check. Run `make` or `make help` for the target list.

SHELL := /bin/bash

APP        := folder_remove_empty
PYTHON     ?= python3
DEST_DIR   ?= $(HOME)/sbin
DATA_DIR   ?= $(HOME)/.local/share
ICON_DIR   := assets/icons
SHOT_SCRIPT := assets/make_screenshots.sh
DESKTOP_IN := assets/folder_remove_empty.desktop
MAN_DIR    := man
TLDR_DIR   := tldr

.DEFAULT_GOAL := help
.PHONY: help test test-quick check-gui check-313 check-all pins run man tldr icons screenshots install uninstall clean final

# Print the target list.
help:
	@echo "folder_remove_empty - make targets"
	@echo ""
	@echo "  make test         the check entry point (./_tests: pytest + ruff + mypy)"
	@echo "  make test-quick   run the test suite only (./_tests --quick)"
	@echo "  make check-gui    ./_tests --gui: the window checks (=session asks for your screen)"
	@echo "  make check-313    run the whole check and the window checks on Python 3.13 (podman)"
	@echo "  make check-all    the pre-push set: final + check-gui + check-313"
	@echo "  make pins         fail when the installed dev tools drift from requirements-dev.txt"
	@echo "  make run          start the program (python3 -m folder_remove_empty)"
	@echo "  make man          write the man page into $(MAN_DIR)/"
	@echo "  make tldr         write the tldr page into $(TLDR_DIR)/"
	@echo "  make icons        redraw the app icon set (assets/icons/make_icons.sh)"
	@echo "  make screenshots  redraw the two window screenshots (assets/make_screenshots.sh)"
	@echo "  make install      install the launcher, the icons and the .desktop file"
	@echo "  make uninstall    remove what make install put there"
	@echo "  make clean        remove caches, build/, dist/ and *.egg-info"
	@echo "  make final        test + man + tldr + ./_check_version + ./_skill_sync --check"
	@echo ""
	@echo "  install folders:  DEST_DIR=$(DEST_DIR)  DATA_DIR=$(DATA_DIR)"

# Fail when the working interpreter or the CI install does not match the pins.
pins:
	@./_check_pins --strict --ci

# Run the full check: pytest, ruff and mypy, all from ./_tests.
test:
	@./_tests

# Run the test suite alone, without ruff and mypy.
test-quick:
	@./_tests --quick

# Start the program: the window by default, a terminal run with --no-gui.
run:
	@$(PYTHON) -m $(APP)

# The two page generators land in phase 4 of todo/goal.md; until they are
# written, `--print-man` and `--print-tldr` still raise NotImplementedError, so
# these targets only turn green in that phase.
man:
	@mkdir -p $(MAN_DIR)
	$(PYTHON) -m $(APP) --print-man > $(MAN_DIR)/$(APP).1

tldr:
	@mkdir -p $(TLDR_DIR)
	$(PYTHON) -m $(APP) --print-tldr > $(TLDR_DIR)/$(APP).page.md

# Draw the icon set again: a purple rectangle with the white letters "fr".
# Needs ImageMagick 7 and a DejaVu font; the drawn files are committed, so this
# target only runs when the icon changes.
icons:
	@bash $(ICON_DIR)/make_icons.sh

# Install the launcher into $(DEST_DIR), the eight icon sizes into the hicolor
# theme below $(DATA_DIR) and the .desktop file into the applications folder of
# the desktop. The desktop file is validated when desktop-file-validate is
# installed. Override the folders with DEST_DIR=... / DATA_DIR=...
install:
	@mkdir -p "$(DEST_DIR)"
	@printf '#!/bin/bash\ncd %s && exec %s -m %s "$$@"\n' "$(CURDIR)" "$(PYTHON)" "$(APP)" > "$(DEST_DIR)/$(APP)"
	@chmod 0755 "$(DEST_DIR)/$(APP)"
	@for icon in $(ICON_DIR)/$(APP)-*.png; do \
		size="$${icon##*-}"; size="$${size%.png}"; \
		target="$(DATA_DIR)/icons/hicolor/$${size}x$${size}/apps"; \
		mkdir -p "$$target"; \
		install -m 0644 "$$icon" "$$target/$(APP).png"; \
	done
	@mkdir -p "$(DATA_DIR)/applications"
	install -m 0644 "$(DESKTOP_IN)" "$(DATA_DIR)/applications/$(APP).desktop"
	@if command -v desktop-file-validate >/dev/null 2>&1; then \
		desktop-file-validate "$(DATA_DIR)/applications/$(APP).desktop"; \
	fi
	@echo "installed: $(DEST_DIR)/$(APP)"
	@echo "installed: the icon set below $(DATA_DIR)/icons/hicolor"
	@echo "installed: $(DATA_DIR)/applications/$(APP).desktop"

# Remove the launcher, the installed icon sizes and the .desktop file again.
uninstall:
	rm -f "$(DEST_DIR)/$(APP)"
	rm -f "$(DATA_DIR)"/icons/hicolor/*/apps/$(APP).png
	rm -f "$(DATA_DIR)/applications/$(APP).desktop"
	@echo "uninstalled: $(APP)"

# Remove every build output and cache of the project.
# The window checks: `./_tests --gui` owns them (the policy module decides where
# they run, a private display by default; FOLDER_REMOVE_EMPTY_GUI_DISPLAY=session
# asks for yours, and window_checks.sh owns the module list).
check-gui:
	@./_tests --gui

# Verify the declared floor on demand: the whole check plus the window checks
# on Python 3.13 inside a container (the CI interpreter). The repository is
# mounted read-only and copied inside, so the container can never rewrite your
# tree; a leftover diff from the regenerated pages is reported as a failure.
check-313:
	@if ! command -v podman >/dev/null 2>&1; then \
		echo "check-313: podman is missing - SKIPPED (needs 'dnf install podman')"; \
		exit 0; \
	fi
	@python3 -m remove_empty_folder_display --wrap \
		podman run --rm -v "$(CURDIR):/src:ro,z" python:3.13-slim bash -lc '\
		set -e; \
		python3 --version; \
		apt-get update -qq >/dev/null && apt-get install -y -qq python3-tk xvfb git make >/dev/null; \
		cp -a /src /w && cd /w; \
		git config --global --add safe.directory /w; \
		git status --porcelain > /tmp/before; \
		python3 -m pip install -q -r requirements-dev.txt && python3 -m pip install -q -e .; \
		make final; \
		make check-gui; \
		git status --porcelain > /tmp/after; \
		if ! diff -q /tmp/before /tmp/after >/dev/null; then \
			echo "check-313: the container changed the tree:"; diff /tmp/before /tmp/after; exit 1; \
		fi; \
		echo "check-313: Python 3.13 agrees with this tree"'

# Redraw the two documentation screenshots of the window (needs Xvfb).
screenshots:
	@bash $(SHOT_SCRIPT)

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

# The release check: the whole suite, both generated pages, the two repository
# validators and the pinned toolchain a release has to be cut in.
final: test man tldr pins

# The pre-push set: everything `final` runs, the window checks on a private
# display and the same checks again on Python 3.13 in a container (the slow one).
check-all: final check-gui check-313
	@./_check_version
	@./_skill_sync --check
