# Muffin Peewee AIO

**muffin-peewee-aio** — Asynchronous [Peewee](http://docs.peewee-orm.com/en/latest/) ORM integration for the [Muffin](https://github.com/klen/muffin) framework.

[![Tests Status](https://github.com/klen/muffin-peewee-aio/workflows/tests/badge.svg)](https://github.com/klen/muffin-peewee-aio/actions)
[![PYPI Version](https://img.shields.io/pypi/v/muffin-peewee-aio)](https://pypi.org/project/muffin-peewee-aio/)
[![Python Versions](https://img.shields.io/pypi/pyversions/muffin-peewee-aio)](https://pypi.org/project/muffin-peewee-aio/)

## Requirements

- Python >= 3.11 (CI runs 3.11 - 3.14)

## Installation

Install via pip:

```bash
$ pip install muffin-peewee-aio
```

The package does not install a database driver; add the extra for the driver you use:

```bash
$ pip install muffin-peewee-aio[aiosqlite]
$ pip install muffin-peewee-aio[aiopg]
$ pip install muffin-peewee-aio[asyncpg]
$ pip install muffin-peewee-aio[aiomysql]
```

## Usage

```python
from muffin import Application
from muffin_peewee import Plugin as Peewee

# Create the application
app = Application("example")

# Initialize the plugin
db = Peewee()
db.setup(app, connection="postgresql://postgres:postgres@localhost:5432/database")

# Or: db = Peewee(app, connection="postgresql://...")
```

Options passed to `Plugin(...)`/`Plugin.setup(...)` are written without a prefix. The `PEEWEE_`
prefix is used only when the option comes from the application config (see
[Configuration](#configuration)).

```python
class Test(db.Model):
    data = peewee.CharField()
```

## Configuration

You can provide options at initialization, through the application config or through the
environment.

| Name                   | Default               | Description                                                      |
| ---------------------- | --------------------- | ---------------------------------------------------------------- |
| **CONNECTION**         | `aiosqlite:///db.sqlite` | Database URL passed to `aio-databases`                        |
| **CONNECTION_PARAMS**  | `{}`                  | Extra options passed to the backend (and every replica backend)   |
| **REPLICAS**           | `None`                | List of read-replica connection URLs                             |
| **AUTO_CONNECTION**    | `True`                | Acquire a DB connection per HTTP request (installs a middleware)  |
| **AUTO_TRANSACTION**   | `True`                | Also wrap each request in a transaction (requires `AUTO_CONNECTION`) |
| **MIGRATIONS_ENABLED** | `True`                | Create the migration router and register the CLI commands         |
| **MIGRATIONS_PATH**    | `"migrations"`        | Directory with migration files                                   |
| **PYTEST_SETUP_DB**    | `True`                | Let `conftest()` create and drop tables                          |

Only these keys are read. Unknown or mistyped option names are silently ignored — the plugin
keeps its default instead of failing — so a typo in a name goes unnoticed.

Values are taken from the following sources (highest priority first):

1. Options passed to `Plugin(...)`/`Plugin.setup(...)`, without a prefix: `connection="..."`.
2. The application config with the `PEEWEE_` prefix (case-insensitive), e.g.
   `PEEWEE_CONNECTION` in a config module or `Application(..., PEEWEE_CONNECTION="...")`.
3. Environment variables with the `{NAME}_PEEWEE_` prefix, where `{NAME}` is the application's
   `NAME` config (`muffin` by default). Values are parsed as JSON, so booleans and lists work:
   `MUFFIN_PEEWEE_AUTO_TRANSACTION=false`, `MUFFIN_PEEWEE_REPLICAS='["..."]'`.
4. The defaults above.

```python
# config.py
NAME = "myapp"
PEEWEE_CONNECTION = "postgresql://..."
```

With the config above, `MYAPP_PEEWEE_CONNECTION=postgresql://...` overrides the URL, while an
explicit `Plugin(app, connection="...")` overrides both.

## Models and Queries

`db.Model` is a `peewee_aio.AIOModel` subclass already bound to the plugin's database, and its
class methods and queries are awaitable:

```python
class Test(db.Model):
    data = peewee.CharField()


await Test.create(data="value")
await Test.get(Test.data == "value")
await Test.select().where(Test.data == "value")
[t.data async for t in Test.select()]
```

Models declared with `db.Model` are bound to the database but are not added to the manager's model
registry. Bulk operations (`db.create_tables()`, `db.drop_tables()`, `db.conftest()` without
arguments) work on registered models only, so register the models you want to manage:

```python
@db.register
class Test(db.Model):
    data = peewee.CharField()
```

or call `db.register(Test)` later. Models may also be registered before `db.setup(app)`: setup
re-binds them to the real manager and database.

`db.Model` requires the plugin to be installed on an application and raises
`PluginNotInstalledError` otherwise.

## JSON fields

`db.JSONField(default, *, null=False, **options)` returns a JSON field matching the current
backend, so the same model code works on SQLite and PostgreSQL:

```python
class Article(db.Model):
    data = db.JSONField({"tags": []})


await Article.create(data={"tags": ["sql"], "meta": {"lang": "en", "views": 1}})
```

`default` is required. A `dict` or `list` default is copied for every row, so instances never share
the same object (other mutable defaults are not copied). Fields are `NOT NULL` by default; pass
`null=True` when the column should accept `NULL`.

The field class is chosen when the field is declared (when the model class body runs), from the
plugin's primary backend. Replicas do not affect the choice, and the class is not re-selected later.

| Backend (`manager.backend.name`) | Field class        | Column                             |
| -------------------------------- | ------------------ | ---------------------------------- |
| `aiosqlite` (also `sqlite://`)   | `JSONSQLiteField`  | `TEXT`                             |
| `aiopg`, `aiopg+pool`            | `JSONPGField`      | `JSON`/`JSONB` chosen by Peewee    |
| `asyncpg`, `asyncpg+pool`        | `JSONAsyncPGField` | `JSON`/`JSONB` chosen by Peewee    |
| anything else (e.g. `aiomysql`)  | `JSONLikeField`    | `TEXT`                             |

The classes themselves live in `muffin_peewee.fields`.

**PostgreSQL via aiopg.** The field inherits `playhouse.postgres_ext.JSONField`. Writes are passed
through psycopg2's `Json` adapter (a `json.dumps` of the value), reads are returned by psycopg2 as
Python objects. The column type is Peewee's mapping of its `JSON` field type: `JSONB` with the
Peewee version pinned in `uv.lock`, plain `JSON` with newer Peewee releases.

**PostgreSQL via asyncpg.** Same Peewee field, adapted for asyncpg: `db_value()`/`python_value()`
are identity functions and query values are wrapped into `peewee.Value`, because asyncpg must do
the serialization itself. asyncpg has no JSON codec by default, so enable it:

```python
db = Peewee(app, connection="asyncpg://...", connection_params={"json": True})
```

Without that option, JSON columns are read as `str` and passing a `dict` to a query fails with
`DataError: expected str, got dict`.

**SQLite.** The field inherits `playhouse.sqlite_ext.JSONField`: the column is `TEXT`, writes are
wrapped into `json('...')` (SQLite validates the document), reads are parsed with `json.loads`. If
a value is not valid JSON (possible only when written by raw SQL), it is returned unchanged as a
string.

**Other backends.** `JSONLikeField` is a plain `TEXT` field using `json.dumps`/`json.loads`; custom
`json_dumps`/`json_loads` callables are accepted. It has no JSON lookup operators.

`None` stays `None` in both directions. Objects that cannot be serialized are not silently
stringified: aiopg and SQLite raise `TypeError` from `json.dumps`, asyncpg raises `DataError` when
binding the parameter.

### Querying nested keys

`field["key"]` works on PostgreSQL and SQLite:

```python
await Article.select().where(Article.data["meta"]["lang"] == "en")
```

On PostgreSQL the lookup translates to `->`/`->>` and returns text, so comparing a number needs a
string or a cast:

```python
await Article.select().where(Article.data["meta"]["views"].cast("int") > 10)
```

On SQLite it translates to `json_extract`, which keeps JSON types, so `== 1` works directly.

The available helpers differ by backend:

- PostgreSQL: `path(*keys)`, `extract(*path)`, `append()`, `update()` (from `playhouse`'s JSON
  field).
- SQLite: `extract()`, `extract_text()`, `append()`, `insert()`, `set()`, `replace()`,
  `update()`, `json_type()`.
- `JSONLikeField` (MySQL or an unknown backend) supports none of these.

The plugin does not expose Peewee's `BinaryJSONField` (`jsonb`) helpers. There is no `has_key()`,
`contained_by()` or `contains_any()`, and `.contains()` is not JSON containment: it is Peewee's
generic `Field.contains()` and produces a plain `LIKE`/`ILIKE` substring match over the serialized
document (the exact pattern differs by driver). There are no GIN index helpers either; add indexes
in a migration with raw SQL if you need them.

## Automatic connections and transactions

With the defaults (`AUTO_CONNECTION=True`, `AUTO_TRANSACTION=True`) the plugin installs a middleware
at the outermost position. For every HTTP request it:

- acquires a database connection;
- opens a transaction;
- commits when the handler returns normally;
- rolls back and re-raises when the handler raises, so Muffin still answers with a 500.

Views do not need `async with db.connection()`: queries pick up the request connection
automatically, and a request is atomic by default.

`AUTO_CONNECTION=False` removes the middleware completely; `AUTO_TRANSACTION` is ignored in that
case because there is nothing to wrap. Without the middleware every query borrows and releases a
connection by itself, and nothing is committed as a unit.

`AUTO_TRANSACTION=False` keeps the connection middleware but loses atomicity: each statement is
committed as it goes (the SQLite backend commits on connection release, PostgreSQL drivers run
outside an explicit transaction). A handler that fails halfway leaves its earlier writes in place.

A `db.transaction()` opened inside a request that already has a transaction does not fail: it runs
on the same connection as a `SAVEPOINT`, so an inner rollback undoes only the inner block:

```python
@app.route("/")
async def view(request):
    await Log.create(message="started")
    try:
        async with db.transaction():
            await do_something()
            raise ValueError  # only do_something() is rolled back
    except ValueError:
        pass
    return "ok"
```

Request-independent code (CLI commands, background jobs) is not wrapped by the middleware. Open the
contexts explicitly:

```python
async with db:  # connect / disconnect
    async with db.connection():
        async with db.transaction():
            await do_work()
```

Synchronous Peewee APIs (used by `peewee-migrate`) run under `db.manager.allow_sync()`.

## Connection Management

`db.connection(**options)` is an async context manager yielding an `aio-databases` connection. A
connection is taken from the pool and released on exit.

- `create=True` (default): always a fresh connection, even if another one is current.
- `create=False`: reuse the current connection when it is acquired, and do not release it on exit.

All options are keywords; the underlying `Database.connection()` is keyword-only.

`db.transaction(**options)` is an async context manager yielding a transaction object with
`commit()` and `rollback()`. It commits on a normal exit, and rolls back and re-raises on an
exception.

- `create=False` (default): use the current connection, creating one if there is none.
- `create=True`: take a separate connection for the transaction.
- `silent=True`: do not raise when committing/rolling back a connection that is already closed.
- A transaction opened on a connection that already has one becomes a `SAVEPOINT`.

Chaining them as `async with db.connection(), db.transaction()` uses a single connection: the
connection is acquired before the transaction is created, so the transaction reuses it.

```python
@app.route("/")
async def view(request):
    async with db.connection(), db.transaction():
        ...
```

## Read Replicas

Replicas are configured with `REPLICAS`:

```python
db = Peewee(
    app,
    connection="postgresql://primary/...",
    replicas=[
        "postgresql://replica1/...",
        "postgresql://replica2/...",
    ],
)
```

`CONNECTION_PARAMS` is applied to every replica backend too.

`db.replica()` opens a **new** connection to one of the replicas (it does not reuse the request's
connection) and yields it. With a plain `asyncpg://` or `aiopg://` URL every call opens and closes a
driver connection; use the pooled schemes (`asyncpg+pool://`, `aiopg+pool://`) for replicas unless
they are rarely read. The replica is picked with `random.choice`: it is not round-robin, there
are no health checks and no automatic read/write splitting. The connection is flagged read-only, so
writes raise `aio_databases.ReadOnlyError`.

```python
@app.route("/")
async def view(request):
    async with db.replica():
        return [t.data async for t in Test.select()]
```

Without `REPLICAS`, `db.replica()` raises `RuntimeError("No replicas configured for this
database")`. Only code inside `async with db.replica()` reads from a replica; everything else keeps
using the primary connection.

## Migrations

The plugin creates a `peewee_migrate.Router` during `setup()` (available as `db.router`) and
registers the CLI commands when `MIGRATIONS_ENABLED` is true. Set it to `False` to skip both.

The commands run Peewee's synchronous API (`manager.allow_sync()`), which needs a synchronous driver
next to the asynchronous one: `psycopg2` for PostgreSQL and `pymysql` for MySQL. The `aiopg` extra
installs `psycopg2`; the `asyncpg` and `aiomysql` extras do not, so add it yourself.

Create a migration:

```bash
$ muffin example:app peewee-create [NAME] [--auto]
```

Run migrations:

```bash
$ muffin example:app peewee-migrate [NAME] [--fake]
```

Rollback the latest migration:

```bash
$ muffin example:app peewee-rollback
```

List all migrations:

```bash
$ muffin example:app peewee-list
```

Clear migration history from the database:

```bash
$ muffin example:app peewee-clear
```

Merge all migrations into one:

```bash
$ muffin example:app peewee-merge
```

The commands execute the synchronous router under `db.manager.allow_sync()`.

## Testing Support

`db.conftest()` prepares the schema for a test:

```python
import pytest


@pytest.fixture
async def db(...):
    ...
    async with plugin.conftest():
        yield plugin
```

With `PYTEST_SETUP_DB=True` (default) it connects to the database, creates tables for all
registered models, yields the plugin, drops those tables and disconnects. Tables are dropped only on
a normal exit: if the test raises, cleanup is skipped. Models must be registered (`@db.register`)
for their tables to be created — or create them yourself with `db.create_tables(Model)`.

With `PYTEST_SETUP_DB=False` the context manager only yields the plugin: no connection, no schema
management.

## API

### `Plugin.connection(**options)`

Returns an async context manager yielding an `aio-databases` connection. `create` controls whether
the current connection is reused; other keywords go to the connection constructor (`read_only`,
`reconnect`; unknown keywords are ignored). Use it for code that runs outside a request or for a
connection that must not be shared.

### `Plugin.transaction(**options)`

Returns an async context manager yielding a transaction with `commit()`/`rollback()`. Commits on
normal exit, rolls back on an exception (the exception is re-raised). Reuses the current connection
by default, so nested transactions become savepoints. See
[Connection Management](#connection-management).

### `Plugin.replica(**options)`

Returns an async context manager yielding a read-only connection to a randomly chosen replica.
Raises `RuntimeError` when no replicas are configured. Writes raise `ReadOnlyError`. See
[Read Replicas](#read-replicas).

### `Plugin.Model`

Property returning the `peewee_aio.AIOModel` subclass bound to the plugin's manager. Raises
`PluginNotInstalledError` when the plugin is not installed on an application.

### `Plugin.manager`

The `peewee_aio.manager.Manager`: `execute()`, `fetchall()`/`fetchone()`/`fetchval()`,
`count()`, `get()`/`get_or_none()`/`create()`/`save()`, `create_tables()`/`drop_tables()`,
`allow_sync()`, `current_conn`, `backend`, `models`, `register()`, `Model`. Before `setup()` it is a
dummy manager; models registered on it are moved to the real manager during setup.

### `Plugin.register(model)`

Binds a model to the plugin's manager and database and adds it to the model registry. Returns the
model, so it can be used as a decorator. Also works before `setup()`.

### `Plugin.create_tables(*models)` / `Plugin.drop_tables(*models)`

Coroutines creating or dropping the given models' tables (`IF NOT EXISTS` / `IF EXISTS` by
default). Without arguments they use every registered model.

### `Plugin.JSONField(default, *, null=False, **options)`

Returns a backend-specific JSON field. See [JSON fields](#json-fields).

### `Plugin.conftest()`

Async context manager for tests. See [Testing Support](#testing-support).

### Lifecycle

`await db.startup()` / `await db.shutdown()` connect and disconnect the manager; Muffin calls them
with the application lifespan. Standalone they can be replaced with `async with db:`.

## Bug Tracker

Found a bug or have a suggestion? Please open an issue at:
https://github.com/klen/muffin-peewee-aio/issues

## Contributing

Development takes place at: https://github.com/klen/muffin-peewee-aio
Pull requests are welcome!

## Contributors

- [klen](https://github.com/klen) (Kirill Klenov)

## License

This project is licensed under the [MIT license](http://opensource.org/licenses/MIT).
