---
name: quota-status
description: >-
  Displays the current session and weekly quota status formatted as (model [effort] ) s: xx% (hh:mm) | w: xx% (d hh:mm) with color-coded percentages (green, yellow, red).
version: 1.3.20260913085347Z
load: on-demand
---

# Quota Status Skill

Formats and reports the active session and weekly quotas with color-coded percentages.

## Output Format
`(model [effort] ) s: <session_quota>% (<session_reset_hh:mm>) | w: <weekly_quota>% (<weekly_reset_days_hours_minutes>) `

Percentages are color-coded:
- **Green** (`\033[32m`): >= 50% quota remaining
- **Yellow** (`\033[33m`): 20% - 49% quota remaining
- **Red** (`\033[31m`): < 20% quota remaining

> [!NOTE]
> There is a trailing space at the end of the line so that when integrated into shell prompts (`PS1`) before `$`, it renders with a single space before the prompt's `$` sign: `(model ) s: xx% (hh:mm) | w: xx% (d hh:mm) $ `.

## Instructions
1. Inspect the active model name and real quota via `~/sbin/gemini-quota` (or `~/sbin/gemini-quota-status`).
2. Read the session remaining percentage `s` and reset window `(hh:mm)`.
3. Read the weekly remaining percentage `w` and reset window `(d hh:mm)`.
4. Output the formatted status line cleanly to stdout or the chat transcript with a trailing space before `$`.
