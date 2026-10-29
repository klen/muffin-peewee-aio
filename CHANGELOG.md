# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- A disabled plugin no longer installs the request middleware and migration commands.
- Enum fields accept raw values: `Model.select().where(Model.status == "active")`.
- JSON field defaults are deep-copied, so nested lists/dicts are not shared between instances.
- `Plugin.conftest()` drops the tables when a test raises.
- README: the request middleware uses one connection, not two; migrations need a synchronous driver.

### Changed

- Removed dead code (`JSONAsyncSQLiteField`, `TFactory`, `from_isoformat`), unused dev dependencies
  (`types-peewee`, `pytest-cov`) and the removed pytest `log_cli` option.

## [3.0.0] - 2026-06-26

### Changed

- Raised minimum supported Python version from 3.10 to 3.11.
- Updated `requires-python` constraint, package classifiers, CI matrix, and tool configurations to reflect Python 3.11+.
- Used `typing.Self` as the return type of `Plugin.__aenter__()` (Python 3.11+ feature).

## [2.5.2] - 2026-05-08

### Fixed

- Pendulum compatibility.

## [2.5.1] - 2026-05-08

### Changed

- WIP changes.

## [2.5.0] - 2026-04-21

### Added

- Read replica support via aio-databases v1.6.0.

### Fixed

- JSONAsyncPGField: add `python_value` to prevent double encoding.

### Changed

- Refactored migration logic from plugin setup to dedicated module.
- Converted README from RST to Markdown.

## [2.4.6] - 2026-04-19

### Fixed

- SQLite compatibility.

## [2.4.5] - 2026-04-19

### Fixed

- asyncpg compatibility.

## [2.4.4] - 2026-04-18

### Fixed

- Build fixes.

## [2.4.3] - 2026-04-18

### Fixed

- Build fixes.

## [2.4.2] - 2026-04-18

### Fixed

- Build and verification fixes.

## [2.4.1] - 2026-04-18

### Fixed

- Build fixes.

## [2.4.0] - 2025-07-16

### Added

- Postgres-backed backend test runs in CI.
