# Changelog

All notable changes to this project. Newest first.

## 2026-11-03

- Support Python 3.15 (classifiers and CI matrix); `CPY001` is ignored since the project has no copyright headers.
- A disabled plugin no longer installs the request middleware and migration commands.
- Enum fields accept raw values: `Model.select().where(Model.status == "active")`.
- JSON field defaults are deep-copied, so nested lists/dicts are not shared between instances.
- `Plugin.conftest()` drops the tables when a test raises.
- `Plugin.setup()` matches the `BasePlugin.setup()` signature of muffin 3.2+ (`name` keyword, `bool` result).
- README: the request middleware uses one connection, not two; migrations need a synchronous driver.
- Removed the `Choices` helper. Use `enum.Enum` (and `StrEnumField`/`IntEnumField`) instead.
- Removed dead code (`JSONAsyncSQLiteField`, `TFactory`, `from_isoformat`), unused dev dependencies
  (`types-peewee`, `pytest-cov`) and the removed pytest `log_cli` option.

## 2026-06-26

- Raised minimum supported Python version from 3.10 to 3.11.
- Updated `requires-python` constraint, package classifiers, CI matrix, and tool configurations to reflect Python 3.11+.
- Used `typing.Self` as the return type of `Plugin.__aenter__()` (Python 3.11+ feature).

## 2026-05-08

- Pendulum compatibility.
- WIP changes.

## 2026-04-21

- Read replica support via aio-databases v1.6.0.
- JSONAsyncPGField: add `python_value` to prevent double encoding.
- Refactored migration logic from plugin setup to dedicated module.
- Converted README from RST to Markdown.

## 2026-04-19

- SQLite compatibility.
- asyncpg compatibility.

## 2026-04-18

- Build fixes.

## 2025-07-16

- Postgres-backed backend test runs in CI.
