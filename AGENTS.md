# AGENTS.md

## Repo at a glance
- This is a Python library, not an app; core behavior is in `muffin_peewee/__init__.py` (`Plugin` setup, middleware, migration CLI commands).
- Backend-specific field behavior (especially JSON and enum handling) is implemented in `muffin_peewee/fields.py`.

## Environment and install
- Use `uv` as the source of truth for local and CI workflows.
- CI-equivalent setup: `uv sync --locked --all-extras --dev`.
- `make`/`make test`/`make lint` bootstrap via `.venv` target (`uv sync` + `uv run pre-commit install`).

## Verification commands
- CI runs checks in this order: `uv run ruff check` -> `uv run pyrefly check` -> `uv run pytest tests`.
- Local shortcuts: `make lint` (runs `make types` then `ruff`) and `make test`.

## Testing gotchas
- `tests/conftest.py` parametrizes `backend` across `aiosqlite`, `aiopg`, and `asyncpg` for most DB tests.
- Full test suite expects Postgres at `localhost:5432`, database `tests`, user/password `test:test` (for `aiopg` + `asyncpg` cases).
- Fast DB-light checks: `uv run pytest tests/test_middleware.py tests/test_migrate.py`.

## Migrations and example app
- Example entrypoint is `example:app` from `example/__init__.py`; example migrations live in `example/migrations`.
- Plugin manage commands are registered during setup (when migrations are enabled): `peewee-create`, `peewee-migrate`, `peewee-rollback`, `peewee-list`, `peewee-clear`, `peewee-merge`.

## Commit/release workflow quirks
- Conventional Commits are enforced by pre-commit using `.git-commits.yaml`.
- Pre-commit checks lockfile freshness via `uv-lock --check`; update `uv.lock` when dependencies change.
- `pre-push` hook runs `poetry run pytest` (not `uv`), so pushes may fail if Poetry is unavailable.
- `make release` assumes `develop` and `master`, bumps with `uvx bump-my-version`, then tags and pushes both branches and tags.
