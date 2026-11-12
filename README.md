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

You need Deker and Python 3.10 or later installed:


```sh
pip install deker deker-shell
```

Then you may run Deker Shell with storage location as a command line parameter:

```sh
deker file:///tmp/deker
```

To work with a Deker server (`http://` or `https://` uri) install the server adapters as well:

```sh
pip install deker deker-server-adapters deker-shell
deker https://user:password@deker.example.com
```

The command history is kept between sessions in `~/.deker_shell_history`, the oldest commands
are dropped past 1000 entries; see `--history-file` and `--history-size` in `deker --help`.

Please refer to Deker [documentation](https://docs.deker.io) for more details.

## Special Thanks

* [ptpython](https://github.com/prompt-toolkit/ptpython) - a better Python REPL
