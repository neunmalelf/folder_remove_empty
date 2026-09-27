#!/bin/bash
# build_tree.sh - build the scratch tree of the Go reference captures.
#   usage: reference/build_tree.sh TREE
#   arguments:
#     TREE       the folder to create; it must not exist yet
#   Every folder and file it creates is described in cases.md with its intent.
#   The refusal case needs a non-root user: TREE/readonly is chmod 0555, so
#   only a user without write permission there sees the refused removal.

__VERSION__="1.0.20260927131905Z"

set -u

T=${1:?usage: build_tree.sh TREE}
if [ -e "$T" ]; then
	printf 'build_tree.sh: %s already exists\n' "$T" >&2
	exit 1
fi
umask 022

# 1) a chain of nested empty folders: c under b under a, all three are removed
mkdir -p "$T/a/b/c"

# 2) a folder that holds a file: the file blocks it, the folder stays
mkdir -p "$T/withfile"
printf 'reference tree: a file blocks its folder\n' > "$T/withfile/note.txt"

# 3) an empty folder inside a folder that also holds a file: removed, parent stays
mkdir -p "$T/withfile/empty_sub"

# 4) a symlink to a folder: the link is neither followed nor removed, it blocks
#    symlink_holder, while the real folder it points at is a plain empty folder
#    below the root and goes
mkdir -p "$T/symlink_holder/target"
ln -s target "$T/symlink_holder/link_to_target"

# 5) a name of the keep list, with an empty subfolder: the subfolder goes, the
#    kept folder stays because the tree root is never removed
mkdir -p "$T/.cache/inner"

# 6) a name starting with ZZZZ: kept, its empty subfolder goes
mkdir -p "$T/ZZZZ-old/inner"

# 7) a name starting with four digits (a dated folder): kept, its empty subfolder goes
mkdir -p "$T/2026-09-23_backup/inner"

# 8) a name holding "!!! MISSING !!!" in lower case: kept, its empty subfolder goes
mkdir -p "$T/data !!! missing !!! here/inner"

# 9) a name kept only by FOLDER_REMOVE_EMPTY_EXCLUDE='keep-*' (case env_excludes);
#    without that variable the folder is an ordinary empty folder and goes
mkdir -p "$T/keep-me/inner"

# 10) a vacant parent holding nothing but a kept child: the parent goes and drags
#     the kept child with it
mkdir -p "$T/keepboth/.cache"

# 11) a removal that is refused: the parent takes no write permission, so rmdir of
#     the child fails and the parent is skipped as well
mkdir -p "$T/readonly/inner"
chmod 0555 "$T/readonly"

printf 'built %s\n' "$T"
