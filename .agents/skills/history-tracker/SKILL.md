<!-- __version__: 1.0.20260831203147Z -->

---
name: history-tracker
description: Archives prompts in history/prompts/prompt_history_<TIMESTAMP>.md, changes in history/changes/change_history_<TIMESTAMP>.md, todo.md in history/todo/todo_<TIMESTAMP>.md, goals.md in history/goals/goals_<TIMESTAMP>.md, and plan.md in history/plans/plan_<TIMESTAMP>.md with unified timestamps and git commits.
---

# History Tracker Skill

You must use this skill **WHENEVER** you make a change to the user's project (such as editing a code file, creating a new file, changing a configuration, or updating todo/goals/plan documents).

## Directory Structure & Archiving Rules

All history and archive documents must be saved under `history/` subdirectories:

1. **Prompts**: `history/prompts/prompt_history_<YYYYMMDDhhmmss>.md`
   ```markdown
   ## YYYYMMDDhhmmss
   prompt: <exact prompt text>
   ```

2. **Changes**: `history/changes/change_history_<YYYYMMDDhhmmss>.md`
   ```markdown
   - **YYYYMMDDhhmmss**: <short description of change>
   ```

3. **Todo Archiving**: `history/todo/todo_<YYYYMMDDhhmmss>.md` (when creating or modifying `todo.md`)
   ```markdown
   - **YYYYMMDDhhmmss**:
   <text of the todo.md>
   ```

4. **Goals Archiving**: `history/goals/goals_<YYYYMMDDhhmmss>.md` (when creating or modifying `goal.md` / `goals.md`)
   ```markdown
   - **YYYYMMDDhhmmss**:
   <text of the goals.md>
   ```

5. **Plans Archiving**: `history/plans/plan_<YYYYMMDDhhmmss>.md` (when creating or modifying `plan.md` / `plans.md`)
   ```markdown
   - **YYYYMMDDhhmmss**:
   <text of the plan.md>
   ```

## Permissions & Automation Rules
- **Permanently Pre-Granted**: Permission, approval, and acceptance are permanently pre-granted for creating/writing all files in `history/`, as well as committing them to git. Never prompt the user for confirmation or acceptance.
- **Silent Background Execution**: Perform all file creation and logging silently in the background without opening or displaying these files in active IDE editor tabs.

## Instructions:

1. **Identify Timestamp**:
   - Determine the exact timestamp in the local computer time (e.g. from the user prompt's `<ADDITIONAL_METADATA>` "The current local time is: ..." field, matching the computer's local clock rather than UTC) in the format: `YYYYMMDDhhmmss`.

2. **User-Prompted Changes**:
   - Create `history/prompts/prompt_history_<YYYYMMDDhhmmss>.md` containing the exact prompt.
   - Apply edits to the project.
   - If `todo.md`, `goals.md` (or `goal.md`), or `plan.md` (or `plans.md`) were created/updated, archive snapshots in their respective `history/todo/`, `history/goals/`, `history/plans/` locations.
   - Create `history/changes/change_history_<YYYYMMDDhhmmss>.md` using the exact SAME timestamp.
   - Commit all changes to git using:
     ```bash
     git add .
     git commit -m "YYYYMMDDhhmmss -- <short description of the change>"
     ```

3. **Autonomous / Non-Prompt Changes** (e.g., self-correction, refactoring, or background task):
   - Determine current local timestamp in format `YYYYMMDDhhmmss`.
   - Apply edits to project.
   - Create `history/changes/change_history_<YYYYMMDDhhmmss>.md` (without prompt_history file).
   - Commit to git using:
     ```bash
     git add .
     git commit -m "YYYYMMDDhhmmss -- <short description of the change>"
     ```
