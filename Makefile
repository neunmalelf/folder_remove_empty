# Makefile for the folder_remove_empty tool.
#
# The tool is a Gio window, so the build needs cgo and the Wayland/X11/EGL
# development files. Every step runs with one worker and under nice/ionice, so
# the machine stays usable while it builds: raise BUILD_JOBS only when a faster
# build is asked for.

APP         := folder_remove_empty
GO          ?= go
BIN_DIR     := bin
DEST_DIR    ?= $(HOME)/sbin
DATA_DIR    ?= $(HOME)/.local/share
ICON_DIR    := icons
BUILD_JOBS  ?= 1
NICE        ?= nice -n 19 ionice -c3

# The window is started, never debugged: -s -w drop the symbol table and the
# DWARF data and -trimpath drops the local paths. That takes about a quarter off
# the plain Gio cgo build.
BUILD_FLAGS ?= -trimpath -ldflags "-s -w"

# The module asks for Go 1.27.1. Fedora's go ships GOTOOLCHAIN=local, which
# forbids the automatic toolchain switch, so the build pins the toolchain it
# needs. Set GOTOOLCHAIN=local on the command line to build with the installed
# go instead.
GOTOOLCHAIN ?= go1.27.1
export GOTOOLCHAIN

GOBUILD := $(NICE) $(GO) build -p $(BUILD_JOBS) $(BUILD_FLAGS)
GOTEST  := $(NICE) $(GO) test -p $(BUILD_JOBS)

.PHONY: all build final install uninstall clean test vet fmt fmt-check run man tldr icons

all: final

# Build the window binary into bin/.
build:
	@mkdir -p $(BIN_DIR)
	$(GOBUILD) -o $(BIN_DIR)/$(APP) ./cmd/$(APP)

# The release build: formatting, vet, the test suite, the binary and the two
# generated pages. Nothing is installed here, that is what install is for.
final: fmt-check vet test build man tldr
	@$(BIN_DIR)/$(APP) --version

# Install the binary, ~/sbin by default, and the app icon in every drawn size
# below the icon folder of the desktop: DEST_DIR=/somewhere make install.
install: build
	@mkdir -p "$(DEST_DIR)"
	install -m 0755 $(BIN_DIR)/$(APP) "$(DEST_DIR)/$(APP)"
	@for icon in $(ICON_DIR)/$(APP)-*.png; do \
		size="$${icon##*-}"; size="$${size%.png}"; \
		target="$(DATA_DIR)/icons/hicolor/$${size}x$${size}/apps"; \
		mkdir -p "$$target"; \
		install -m 0644 "$$icon" "$$target/$(APP).png"; \
	done
	@echo "installed: $(DEST_DIR)/$(APP)"
	@echo "installed: the icon set below $(DATA_DIR)/icons/hicolor"

# Remove the installed binary and the installed icons again.
uninstall:
	rm -f "$(DEST_DIR)/$(APP)"
	rm -f "$(DATA_DIR)"/icons/hicolor/*/apps/$(APP).png

# Draw the app icon set again: a purple rectangle with the white letters "fr".
# Needs ImageMagick 7 and a DejaVu font; the drawn files are committed, so this
# target only runs when the icon changes.
icons:
	bash $(ICON_DIR)/make_icons.sh

# Run the test suite.
test:
	$(GOTEST) ./...

# Run go vet.
vet:
	$(NICE) $(GO) vet -p $(BUILD_JOBS) ./...

# Format the Go sources in place.
fmt:
	$(GO) fmt ./...

# Fail when a Go source is not formatted.
fmt-check:
	@files="$$(gofmt -l .)"; \
	if [ -n "$$files" ]; then \
		echo "gofmt found unformatted files:" >&2; \
		echo "$$files" >&2; \
		exit 1; \
	fi; \
	echo "gofmt: clean"

# Run the built window.
run: build
	$(BIN_DIR)/$(APP)

# Generate the man page and the tldr page from the binary, so the pages can
# never drift from the program.
man: build
	@mkdir -p man
	$(BIN_DIR)/$(APP) --print-man > man/$(APP).1

tldr: build
	@mkdir -p tldr
	$(BIN_DIR)/$(APP) --print-tldr > tldr/$(APP).page.md

# Remove every build output.
clean:
	rm -rf $(BIN_DIR)
	rm -f $(APP) $(APP).exe
