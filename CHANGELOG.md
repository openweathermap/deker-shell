# Changelog

All notable changes to deker-shell, the interactive shell of [DEKER™](https://github.com/openweathermap/deker),
are listed here, release by release, newest first. Only production releases are listed. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), the versions follow
[Semantic Versioning](https://semver.org/).

## [2.0.0]

Released together with DEKER™ 2.0.0.

### Added

- `https://` URIs, along with `http://` and `file://`. The adapters package of the scheme is
  checked before the shell starts; when it is missing, the shell prints one line with the
  install command instead of a traceback.
- The command history is kept between the sessions: `--history-file` and `--history-size` set
  the file and its limit; the history is searched with the arrow keys and completed fuzzily.
- `use(` completes the names of the collections; the private names are hidden until `_` is typed.

### Changed

- The completion does not rely on the private classes of ptpython anymore and does not break its
  settings.
- The namespace of the REPL lives in a module of its own.
- The command line options do not overwrite each other.

### Internals and tooling

- The build moved from poetry to uv, ruff and pydoclint replace black, flake8, isort and darglint;
  `make ci`, `make test-matrix`, `make install-matrix`; `py.typed`, no type-check suppressions; the
  tests grew from 7 to 64, 100% coverage required; the tests run against the sibling repositories;
  the documentation links lead to docs.deker.io.

## [1.2.0] - 2026-11-11

### Added

- Python 3.13 and 3.14 are supported.

### Changed

- `click>=8.5,<9` and `ptpython>=3.0.32,<4` (were pinned to 8.1.7 and 3.0.23); the dev and docs
  tooling is updated.
- CI runs the tests on every supported Python.

### Removed

- Python 3.9. Pin `deker-shell<1.2` to stay on it.

## [1.1.0] - 2024-01-04

### Added

- The command line is built on click: the client settings (`--workers`, `--write-lock-timeout`,
  `--write-lock-check-interval`, `--loglevel`, `--memory-limit`) are options of the `deker`
  command, and unknown options are passed to the client as keyword arguments.

## [1.0.1] - 2023-08-18

### Fixed

- The client is closed when the shell exits.

### Changed

- All the configuration lives in `pyproject.toml`; the CI workflows moved to deker-actions; the
  README is rewritten.

## [1.0.0] - 2023-08-01

The pilot release of deker-shell.

[2.0.0]: https://github.com/openweathermap/deker-shell/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/openweathermap/deker-shell/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/openweathermap/deker-shell/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/openweathermap/deker-shell/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/openweathermap/deker-shell/releases/tag/v1.0.0
