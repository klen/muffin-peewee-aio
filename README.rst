Muffin Peewee AIO
#################

**muffin-peewee-aio** — Asynchronous Peewee_ ORM integration for the Muffin_ framework.

.. image:: https://github.com/klen/muffin-peewee-aio/workflows/tests/badge.svg
    :target: https://github.com/klen/muffin-peewee-aio/actions
    :alt: Tests Status

.. image:: https://img.shields.io/pypi/v/muffin-peewee-aio
    :target: https://pypi.org/project/muffin-peewee-aio/
    :alt: PYPI Version

.. image:: https://img.shields.io/pypi/pyversions/muffin-peewee-aio
    :target: https://pypi.org/project/muffin-peewee-aio/
    :alt: Python Versions

.. contents::

Requirements
============

- Python >= 3.10

Installation
============

Install via pip: ::

    $ pip install muffin-peewee-aio

You can include an async database driver as needed: ::

    $ pip install muffin-peewee-aio[aiosqlite]
    $ pip install muffin-peewee-aio[aiopg]
    $ pip install muffin-peewee-aio[asyncpg]
    $ pip install muffin-peewee-aio[aiomysql]

Usage
=====

.. code-block:: python

    from muffin import Application
    from muffin_peewee import Plugin as Peewee

    # Create the application
    app = Application("example")

    # Initialize the plugin
    db = Peewee()
    db.setup(app, PEEWEE_CONNECTION="postgresql://postgres:postgres@localhost:5432/database")

    # Or: db = Peewee(app, **options)


Configuration
=============

You can provide options either at initialization or through the application config.

+------------------------+-----------------------------------------+----------------------------------------------------+
| Name                   | Default                                 | Description                                        |
+========================+=========================================+====================================================+
| **CONNECTION**         | ``sqlite:///db.sqlite``                 | Database connection URL                            |
+------------------------+-----------------------------------------+----------------------------------------------------+
| **CONNECTION_PARAMS**  | ``{}``                                  | Extra options passed to the database backend       |
+------------------------+-----------------------------------------+----------------------------------------------------+
| **AUTO_CONNECTION**    | ``True``                                | Automatically acquire a DB connection per request  |
+------------------------+-----------------------------------------+----------------------------------------------------+
| **AUTO_TRANSACTION**   | ``True``                                | Automatically wrap each request in a transaction   |
+------------------------+-----------------------------------------+----------------------------------------------------+
| **MIGRATIONS_ENABLED** | ``True``                                | Enable the migration engine                        |
+------------------------+-----------------------------------------+----------------------------------------------------+
| **MIGRATIONS_PATH**    | ``"migrations"``                        | Path to store migration files                      |
+------------------------+-----------------------------------------+----------------------------------------------------+
| **PYTEST_SETUP_DB**    | ``True``                                | Manage DB setup and teardown in pytest             |
+------------------------+-----------------------------------------+----------------------------------------------------+

You can also define options in the `Application` config using the `PEEWEE_` prefix: ::

    PEEWEE_CONNECTION = "postgresql://..."

Note: Muffin application config is case-insensitive.

Models and Queries
==================

Define your model:

.. code-block:: python

    class Test(db.Model):
        data = peewee.CharField()

Query the database:

.. code-block:: python

    @app.route("/")
    async def view(request):
        return [t.data async for t in Test.select()]

Connection Management
=====================

By default, connections and transactions are managed automatically.
To manage them manually, disable the config flags and use context managers:

.. code-block:: python

    @app.route("/")
    async def view(request):
        async with db.connection():
            async with db.transaction():
                # Perform DB operations here
                ...

Migrations
==========

Create a migration: ::

    $ muffin example:app peewee-create [NAME] [--auto]

Run migrations: ::

    $ muffin example:app peewee-migrate [NAME] [--fake]

Rollback the latest migration: ::

    $ muffin example:app peewee-rollback

List all migrations: ::

    $ muffin example:app peewee-list

Clear migration history from the database: ::

    $ muffin example:app peewee-clear

Merge all migrations into one: ::

    $ muffin example:app peewee-merge

Testing Support
===============

You can use the `conftest()` context manager to auto-manage schema setup and teardown during testing:

.. code-block:: python

    import pytest

    @pytest.mark.asyncio
    async def test_example():
        async with db.conftest():
            # Tables are created and dropped automatically
            ...

Bug Tracker
===========

Found a bug or have a suggestion? Please open an issue at:
https://github.com/klen/muffin-peewee-aio/issues

Contributing
============

Development takes place at: https://github.com/klen/muffin-peewee-aio
Pull requests are welcome!

Contributors
============

* `klen`_ (Kirill Klenov)

License
=======

This project is licensed under the `MIT license`_.

.. _links:

.. _MIT license: http://opensource.org/licenses/MIT
.. _Muffin: https://github.com/klen/muffin
.. _Peewee: http://docs.peewee-orm.com/en/latest/
.. _klen: https://github.com/klen
