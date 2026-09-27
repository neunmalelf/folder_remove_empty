---
name: update-tests
description: Perform a thorough test coverage audit across the entire codebase and output recommendations to tests_suggestions.md without modifying source or test code.
version: 1.1.20260830232840Z
load: always
---

# update-tests

## Overview
Perform a thorough test coverage audit across the entire codebase and output comprehensive recommendations to `tests_suggestions.md`.

## Audit Requirements

1. **Scope:**    - Inspect all modules, submodules, classes, data structures, and functions in the project (`ddpico/*.py`).

2. **Analysis:**
   - Cross-reference each component against the existing test suite in the `tests/` directory.
   - Evaluate test completeness, missing edge cases, boundary values, failure states, and uncovered components.

3. **Report Generation:**
   Create `tests_suggestions.md` containing:
   - **Missing Tests:** Functions, classes, or data structures with zero or inadequate test coverage.
   - **Test Improvements:** Existing tests requiring modification, refactoring, or expanded assertions/edge cases.
   - **Proposed Test Cases:** Concrete suggestions for new test scenarios (including input/output behavior, mocks, and failure paths).

## Execution Constraints

- **Planning Mode Only:** Write *only* to `tests_suggestions.md`.
- **No Implementation:** Do **not** modify source code, edit existing test files, or generate new test code until explicitly reviewed and approved by the user.
- **Notification:** Notify the user when `tests_suggestions.md` is complete and await further instructions.
