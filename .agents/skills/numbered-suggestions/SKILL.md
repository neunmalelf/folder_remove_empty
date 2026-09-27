---
name: numbered-suggestions
description: Always number followup suggestions with a numeric prefix and append a "99. All of the above" entry
version: 1.2.20260913131846Z
load: always
---

# numbered-suggestions

When using `suggest_followups`, always prefix each suggestion label with a number like `1.`, `2.`, `3.` so the user can easily reference them by number.

## When to use

Always. This skill is active for all conversations.

## Instructions

1. When calling `suggest_followups`, number the suggestions sequentially starting from 1: `1.`, `2.`, `3.`, etc.
2. Put the number in the `label` field only — this is what the user sees on the clickable card (e.g., `"label": "1. Add tests"`). Do **not** include the number in the `prompt` field, since that text gets sent as a user message.
3. Use the format: `N. Short description` for each label.
4. Whenever you present one or more suggestions, always append one extra final entry labeled `99. All of the above`, no matter how many suggestions precede it. Its `label` is exactly `"99. All of the above"`; its `prompt` must tell the agent to execute every preceding suggestion in order (e.g. `"Execute suggestions 1 through 3 above, in order"`). Never reuse number 99 for a regular suggestion.
5. Example:
   ```json
   [
     {"label": "1. Add unit tests", "prompt": "Add unit tests for the new feature"},
     {"label": "2. Update README", "prompt": "Update README for the new feature"},
     {"label": "99. All of the above", "prompt": "Execute suggestions 1 through 2 above, in order"}
   ]
   ```