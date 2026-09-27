# folder_remove_empty

> Remove every empty folder below a start folder, deepest first.
> The start folder itself is never removed, only the folders below it.
> More information: <https://github.com/neunmalelf/folder_remove_empty>.

- Remove the empty folders below the current folder, in the window:

  `folder_remove_empty`

- Remove them on the terminal, with every removed folder named:

  `folder_remove_empty --no-gui /data/archive`

- Look first, remove nothing:

  `folder_remove_empty --dry-run --verbose /data/archive`

- Report every kept folder that was left in place:

  `folder_remove_empty --verbose /data/archive`

- Keep every folder whose name matches an extra pattern as well:

  `FOLDER_REMOVE_EMPTY_EXCLUDE='keep-*:downloads*' folder_remove_empty --no-gui /data/archive`

- Print the usage text:

  `folder_remove_empty --help`

- Print the version:

  `folder_remove_empty --version`

- Read the exit code of a refused path:

  `folder_remove_empty --no-gui /data/does-not-exist; echo $?`
