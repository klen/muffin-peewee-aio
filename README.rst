Muffin Peewee AIO
#################

.. _description:

**muffin-peewee-aio** -- Peewee_ ORM integration to Muffin_ framework.

.. _badges:

.. image:: https://github.com/klen/muffin-peewee-aio/workflows/tests/badge.svg
    :target: https://github.com/klen/muffin-peewee-aio/actions
    :alt: Tests Status

.. image:: https://img.shields.io/pypi/v/muffin-peewee-aio
    :target: https://pypi.org/project/muffin-peewee-aio/
    :alt: PYPI Version

.. image:: https://img.shields.io/pypi/pyversions/muffin-peewee-aio
    :target: https://pypi.org/project/muffin-peewee-aio/
    :alt: Python Versions

.. _contents:

.. contents::

.. _requirements:

Requirements
=============

- python >= 3.7

.. _installation:

Installation
=============

**Muffin Peewee** should be installed using pip: ::

    $ pip install muffin-peewee-aio

You can install optional database drivers with: ::

    $ pip install muffin-peewee-aio[sqlite]
    $ pip install muffin-peewee-aio[postgresql]
    $ pip install muffin-peewee-aio[mysql]


.. _usage:

Usage
=====

.. code-block:: python

    from muffin import Application
    from muffin_peewee import Plugin as Peewee

    # Create Muffin Application
    app = Application('example')

    # Initialize the plugin
    # As alternative: db = Peewee(app, **options)
    db = Peewee()
    db.setup(app, PEEWEE_CONNECTION='postgresql://postgres:postgres@localhost:5432/database')


Options
-------

=========================== ======================================= =========================== 
Name                        Default value                           Desctiption
--------------------------- --------------------------------------- ---------------------------
**CONNECTION**              ``sqlite:///db.sqlite``                 Database URL
**CONNECTION_PARAMS**       ``{}``                                  Additional params for DB connection
**AUTO_CONNECTION**         ``True``                                Automatically get a connection from db for a request
**AUTO_TRANSACTION**        ``True``                                Automatically wrap a request into a transaction
**MIGRATIONS_ENABLED**      ``True``                                Enable migrations with
**MIGRATIONS_PATH**         ``"migrations"``                        Set path to the migrations folder
=========================== ======================================= =========================== 

You are able to provide the options when you are initiliazing the plugin:

.. code-block:: python

    db.setup(app, connection='DB_URL')


Or setup it inside ``Muffin.Application`` config using the ``PEEWEE_`` prefix:

.. code-block:: python

   PEEWEE_CONNECTION = 'DB_URL'

``Muffin.Application`` configuration options are case insensitive

Queries
-------

.. code-block:: python

    class Test(db.Model):
        data = peewee.CharField()


    @app.route('/')
    async def view(request):
        return [t.data async for t in Test.select()]

Manage connections
------------------

.. code-block:: python

    # Set configuration option `MANAGE_CONNECTIONS` to False

    # Use context manager
    @app.route('/')
    async def view(request):
        # Aquire a connection
        async with db.manager.connection():
            # Work with db
            # ...


Migrations
----------

Create migrations: ::

    $ muffin example:app pw_create [NAME] [--auto]


Run migrations: ::

    $ muffin example:app pw_migrate [NAME] [--fake]


Rollback migrations: ::

    $ muffin example:app pw_rollback [NAME]


List migrations: ::

    $ muffin example:app pw_list


.. _bugtracker:

Bug tracker
===========

If you have any suggestions, bug reports or
annoyances please report them to the issue tracker
at https://github.com/klen/muffin-peewee-aio/issues

.. _contributing:

Contributing
============

Development of Muffin Peewee happens at: https://github.com/klen/muffin-peewee-aio


Contributors
=============

* klen_ (Kirill Klenov)

.. _license:

License
========

Licensed under a `MIT license`_.

.. _links:

.. _MIT license: http://opensource.org/licenses/MIT
.. _Muffin: https://github.com/klen/muffin
.. _Peewee: http://docs.peewee-orm.com/en/latest/
.. _klen: https://github.com/klen
