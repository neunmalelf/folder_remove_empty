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
.PHONY: help test test-quick run man tldr icons screenshots install uninstall clean final

# Print the target list.
help:
	@echo "folder_remove_empty - make targets"
	@echo ""
	@echo "  make test         run the whole check (pytest + ruff + mypy) via ./_tests"
	@echo "  make test-quick   run the test suite only (./_tests --quick)"
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
# Redraw the two documentation screenshots of the window (needs Xvfb).
screenshots:
	@bash $(SHOT_SCRIPT)

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

# The release check: the whole suite, both generated pages and the two
# repository validators.
final: test man tldr
	@./_check_version
	@./_skill_sync --check
