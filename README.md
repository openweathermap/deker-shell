# Deker Shell

Deker Shell is an interactive REPL based management interface for
[Deker](https://github.com/openweathermap/deker) storage engine.

## Features

* Autocompletion
* Syntax highlighting
* `client` and `collections` variables initialized at start
* Shortcut `use` function to change current `collection`
* Imported at start: `numpy` as `np`, `datetime` and all `deker` public classes
* Running `asyncio` loop (thus, enabling you to use `async` and `await`)
* All the `ptpython` features

## Quick Start

You need Deker and Python 3.9 or later installed:


```sh
pip install deker deker-shell
```

Then you may run Deker Shell with storage location as a command line parameter:

```sh
deker file:///tmp/deker
```

Please refer to Deker [documentation](https://docs.deker.io) for more details.

## Special Thanks

* [ptpython](https://github.com/prompt-toolkit/ptpython) - a better Python REPL
