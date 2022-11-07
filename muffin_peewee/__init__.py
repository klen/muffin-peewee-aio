"""Support Peewee ORM for Muffin framework."""

import typing as t

import muffin
from aio_databases.database import ConnectionContext, Database, TransactionContext
from muffin.plugins import BasePlugin
from peewee import Model
from peewee_aio.manager import TMODEL, Manager
from peewee_aio.model import AIOModel
from peewee_migrate import Router

from .fields import Choices, JSONField

__version__ = "0.6.4"
__project__ = "muffin-peewee-aio"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "MIT"


__all__ = "Plugin", "JSONField", "Choices"


assert JSONField and Choices


class Plugin(BasePlugin):

    """Muffin Peewee Plugin."""

    name = "peewee"
    defaults = {
        # Connection params
        "connection": "sqlite:///db.sqlite",
        "connection_params": {},
        # Manage connections automatically
        "auto_connection": True,
        "auto_transaction": True,
        # Setup migration engine
        "migrations_enabled": True,
        "migrations_path": "migrations",
    }

    router: Router = None
    manager: Manager = Manager(
        "dummy://localhost"
    )  # Dummy manager for support registration
    database: Database

    def setup(self, app: muffin.Application, **options):
        """Init the plugin."""
        super().setup(app, **options)

        # Init manager and rebind models
        manager = Manager(self.cfg.connection, **self.cfg.connection_params)
        for model in list(self.manager):
            manager.register(model)
        self.manager = manager
        self.database = manager.aio_database
        self.Model: t.Type[AIOModel] = self.manager.Model

        if self.cfg.migrations_enabled:
            router = Router(manager.pw_database, migrate_dir=self.cfg.migrations_path)
            self.router = router

            # Register migration commands
            @app.manage
            def peewee_migrate(name: str = None, fake: bool = False):
                """Run application's migrations.

                :param name: Choose a migration' name
                :param fake: Run as fake. Update migration history and don't touch the database
                """
                with manager.allow_sync():
                    router.run(name, fake=fake)

            @app.manage
            def peewee_create(name: str = "auto", auto: bool = False):
                """Create a migration.

                :param name: Set name of migration [auto]
                :param auto: Track changes and setup migrations automatically
                """
                with manager.allow_sync():
                    router.create(name, auto and [m for m in self.manager.models])

            @app.manage
            def peewee_rollback():
                """Rollback the latest migration."""
                with manager.allow_sync():
                    router.rollback()

            @app.manage
            def peewee_list():
                """List migrations."""
                with manager.allow_sync():
                    router.logger.info("Migrations are done:")
                    router.logger.info("\n".join(router.done))
                    router.logger.info("")
                    router.logger.info("Migrations are undone:")
                    router.logger.info("\n".join(router.diff))

            @app.manage
            def peewee_clear():
                """Clear migrations from DB."""
                with manager.allow_sync():
                    self.router.clear()

            @app.manage
            def peewee_merge(name: str = "initial", clear: bool = False):
                """Merge all migrations into one."""
                with manager.allow_sync():
                    self.router.merge(name)

        if self.cfg.auto_connection:
            app.middleware(self.get_middleware(), insert_first=True)

    async def startup(self):
        """Connect to the database (initialize a pool and etc)."""
        await self.database.connect()

    async def shutdown(self):
        """Disconnect from the database (close a pool and etc.)."""
        await self.database.disconnect()

    async def __aenter__(self) -> "Plugin":
        """Connect the database."""
        await self.database.connect()
        return self

    async def __aexit__(self, *_):
        """Disconnect the database."""
        await self.database.disconnect()

    def register(self, Model: t.Type[TMODEL]) -> t.Type[TMODEL]:
        """Register a model with self manager."""
        return self.manager.register(Model)

    def connection(self, *params, **opts) -> ConnectionContext:
        return self.database.connection(*params, **opts)

    def transaction(self, *params, **opts) -> TransactionContext:
        return self.database.transaction(*params, **opts)

    async def create_tables(self, *Models: t.Type[Model]):
        """Create SQL tables."""
        await self.manager.create_tables(*(Models or self.manager.models))

    async def drop_tables(self, *Models: t.Type[Model]):
        """Drop SQL tables."""
        await self.manager.drop_tables(*(Models or self.manager.models))

    def get_middleware(self) -> t.Callable:
        """Generate a middleware to manage connection/transaction."""

        async def middleware(handler, request, receive, send):  # type: ignore
            async with self.connection():
                return await handler(request, receive, send)

        if self.cfg.auto_transaction:

            async def middleware(handler, request, receive, send):  # noqa
                async with self.connection():
                    async with self.transaction():
                        return await handler(request, receive, send)

        return middleware
