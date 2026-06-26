# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
