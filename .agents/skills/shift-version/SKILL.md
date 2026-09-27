---
name: shift-version
description: Enforces version tracking (Major.Minor.timestamp, using ~/sbin/timestamp) in all bash scripts, SKILL.md files, and Go source files, updated on each change
version: 1.4.20260909054143Z
load: always
---

# shift-version

Enforces the convention that all bash scripts, SKILL.md files, and Go source files in this project must have a version identifier, and this version must be incremented whenever the file is modified.

## Version format

### For bash scripts
`__VERSION__="<major>.<minor>.<YYYYMMDDhhmmss>Z"` (timestamp UTC, trailing Z)

### For SKILL.md files
Add a `version` field in the YAML frontmatter:
```yaml
---
name: my-skill
description: ...
version: 1.0.20260602114105Z
load: always
---
```

### For Go source files
Add a `__VERSION__` constant:
```go
const __VERSION__ = "1.0.20260602114105Z"
```
One constant per package: Go does not allow the same constant in two files of the same package.

- **Major** — incremented for significant rewrites or breaking changes
- **Minor** — incremented for feature additions or fixes
- **YYYYMMDDhhmmss** — the UTC (coordinated universal time) timestamp of the last modification; append a trailing `Z`

## Examples

`__VERSION__="1.0.20260602112238Z"`
`__VERSION__="1.1.20260603143000Z"`
`version: 1.0.20260602114105Z` (in SKILL.md frontmatter)
`const __VERSION__ = "1.0.20260602114105Z"` (in a Go source file)

## When to use

Always. Every bash script, SKILL.md file, and Go source file in this project must have a version identifier.

## Placement

### For bash scripts
The version line goes right after the shebang and any brief description comments, before any `source` or imports.
```bash
#!/bin/bash
# Brief description of the script

__VERSION__="1.0.20260602112238Z"

source "___dd_colors"
```

### For SKILL.md files
The version field goes in the YAML frontmatter, after the description.
```yaml
---
name: my-skill
description: ...
version: 1.0.20260602114105Z
load: always
---
```

### For Go source files
The constant goes right after the package declaration and imports, before any functions. The command's `main.go` holds the version for a command package; the root `main.go` holds it for the library package.
```go
package gofart

import "fmt"

const __VERSION__ = "1.0.20260602114105Z"
```

## Instructions

1. When creating a new bash script, add `__VERSION__="1.0.<current UTC timestamp>Z"` after the shebang and description.
2. When creating or modifying a SKILL.md file, add or update the `version` field in the frontmatter.
3. When modifying any tracked file, update the timestamp to the current UTC time, with a trailing `Z`. Increment the minor version (or major for significant rewrites).
4. Use `~/sbin/timestamp` to get the current UTC timestamp (the utility already emits the trailing `Z`, e.g. `$(~/sbin/timestamp)`).
5. Do not use spaces around the `=` sign for bash scripts.
6. If a file doesn't have a version yet, add it with version `1.0` and the current UTC timestamp + `Z`.
7. When creating or modifying a Go source file, add or update the package's `__VERSION__` constant in its `main.go`.
