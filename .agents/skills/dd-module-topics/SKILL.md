---
name: dd-module-topics
description: Every new or changed function, datastructure, enum or class in this project must go into its own source file under ddpico/ based on its topic.
version: 1.9.20260911232216Z
load: always
---

# dd-module-topics

Rule for the ddpico & ddbusybox project: every function, datastructure, enum
and class must live in the topic-matching source file under `ddpico/`. The
package `ddpico/__init__.py` is the top-level API entry point: it re-exports
public names from topic modules and hosts the CLI dispatcher + script interpreter.

## Topic files (ddpico/)

| File | Contents |
|---|---|
| `internal.py` | Base constants (NL, JOBEXITMESSAGE1, __version__), non-public helpers, stdout-parity reconfigure |
| `general.py` | General datastructures (AnsiColor, LogType, LineKind, DocEntry, LogEntry, ScriptLine, DdError) and `general_*` functions |
| `style.py` | Style/color: `style_apply`, `style_combine`, `dd_fgcolor_*`, `dd_bgcolor_*`, `dd_style_*` wrappers |
| `echo.py` | Output/echo functions and DONE ASCII banners |
| `converter.py` | Number/string conversion helpers |
| `math.py` | Math + random functions (`random_number`, `random_range`, `random_string`) |
| `help.py` | Command registry (COMMANDS, _DOC_SECTIONS), `usage`, `help_detail`, `help_list_functions` |
| `terminal.py` | Terminal size/title/clear helpers |
| `terminal_cursor.py` | ANSI cursor functions |
| `environment.py` | `variable_require`, `environment_check_variable` |
| `string.py` | All `string_*` functions |
| `array.py` | Pure list helpers (`array_*`) |
| `directory.py` | `mdcd` + all `directory_*` functions |
| `logging.py` | Logfile helpers (`log_message`, `log_to_file`) |
| `time.py` | Time helpers (`time_*`) |
| `date.py` | Date + datetime helpers (`date_*`, `datetime_*`) |
| `network.py` | Socket helpers (`net_*`) |
| `files.py` | File operations: `file_copy`, `file_move`, `file_rename` with `FileOverwriteOption`, dry-run, reading/writing, and helpers |
| `bakignore.py` | Unified `.gitignore` and `.bakignore` pattern matching engine |
| `crawler.py` | Filesystem tree crawler fluent builder (`DirectoryCrawler`, `directory_crawl`) |
| `lock.py` | Process-safe directory and file locking (`lock_acquire`, `LockFile` context manager) |
| `status.py` | Terminal width detection and status line `Heartbeat` helpers |
| `fart/` | FART engine subpackage (`main`, `match`, `options`, `replace`, `walk`, `rulefile`, `pdf`, `ebook`, `help`) |
| `ddfart.py` | Standalone ddfart program CLI (`ddfart_main`, doc-flag handling, engine delegation) |
| `ddcrawler.py` | Directory crawler CLI (`crawl_main`, `main`) |
| `ddbusybox.py` | Multi-call BusyBox dispatcher (`ddbusybox`/`ddtoolbox`, applets fart/pyfart, ddpico, ddbak, crawl, ...) |
| `job.py` | Job data/structures: JobStatus, JobState, `_JOB`, `create_job_state`, `error_report` |
| `actions.py` | Job lifecycle actions (`action_start`, `action_running`, `action_end`, `action_error`, `action_aborted_by_*`) |
| `znumber.py` | Base-26 number utilities (`znumber_to_decimal`, `decimal_to_znumber`, `znumber_next`) |
| `eval.py` | Excel/Sheets-style formula evaluator (`eval_formula`, the `eval` command) |
| `programs.py` | Standalone programs specification registry, binary metadata, man/tldr/requirements generators |

## Architectural Guidelines

1. **Topic file for everything.** Any new or changed function, datastructure, enum or class goes into its topic file under `ddpico/`.
2. **`ddpico/__init__.py` stays slim.** Re-exports public API names and hosts the ddpico command dispatcher.
3. **Domain classes and fluent builders are encouraged.** Fluent builders (like `DirectoryCrawler`), context managers (like `LockFile`, `Heartbeat`), and domain models are fully supported alongside plain functional commands.
4. **5-Rule Docstrings.** Every function, class, and method must have docstrings including `usage:`, `returns:`, and `example:`.
