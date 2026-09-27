# Change log

All notable changes to this project are documented in this file, newest first.
A version is the UTC timestamp of its change, `x.x.YYYYMMDDhhmmss`, the output of
`~/sbin/timestamp`. The user-facing highlights per release, in prose, are in
`NEWS`.

## 0.5.20260923194832 - 2026-09-23

### Added

- `tldr_test.go`: `TestTldrPageKeepsTheRenderableShape` (every example is a
  description line, an empty line and a backticked command indented by two
  spaces) and `TestTldrPageNamesTheProgram` (the head of the page, every command
  calls the program and stays on one line).
- The button border is checked in `TestUIOrdersTheButtons`: every cell of the
  row has to hold a button and a rectangle whose stroke is the border color of
  the theme.

### Changed

- The button row is framed like the other controls: `head` wraps each of the
  five buttons in `ui.frame`, so `[Help] [Light mode/Dark mode] [Exit] [Pause]
  [Start]` carry the clear grey border in both themes instead of relying on
  their fill alone.
- `TldrPage` builds the page from `tldrExamples`, one description and one
  command per job, and writes each command as `` `command` `` indented by two
  spaces below an empty line. `tldr folder_remove_empty` renders every command
  now; with the bare indented form tealdeer 1.7.3 showed the descriptions and
  dropped the commands (measured with test pages on 2026-09-23).
- The global skill `tldr-page-naming` gained the section "The form the readers
  show" with that measurement, and `~/.local/share/tealdeer/pages` carries the
  page of this program (`_tldr_update`).

