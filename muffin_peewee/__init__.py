"""Support Peewee ORM for Muffin framework."""

from typing import TYPE_CHECKING, Callable, Optional, Type  # py37, py38: Type

from aio_databases.database import ConnectionContext, Database, TransactionContext
from muffin.plugins import BasePlugin
from peewee_aio.manager import Manager
from peewee_migrate import Router

from .fields import Choices, EnumField, JSONField

if TYPE_CHECKING:
    from muffin import Application
    from peewee import Model
    from peewee_aio.model import AIOModel
    from peewee_aio.types import TVModel

__all__ = "Plugin", "JSONField", "Choices", "EnumField"


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

    router: Router
    manager: Manager = Manager(
        "dummy://localhost",
    )  # Dummy manager for support registration
    database: Database

    def setup(self, app: "Application", **options):
        """Init the plugin."""
        super().setup(app, **options)

        # Init manager and rebind models
        manager = Manager(self.cfg.connection, **self.cfg.connection_params)
        for model in list(self.manager):
            manager.register(model)
        self.manager = manager
        self.database = manager.aio_database
        self.Model: Type[AIOModel] = self.manager.Model

        if self.cfg.migrations_enabled:
            router = Router(manager.pw_database, migrate_dir=self.cfg.migrations_path)
            self.router = router

            # Register migration commands
            @app.manage
            def peewee_migrate(name: Optional[str] = None, *, fake: bool = False):
                """Run application's migrations.

                :param name: Choose a migration' name
                :param fake: Run as fake. Update migration history and don't touch the database
                """
                with manager.allow_sync():
                    router.run(name, fake=fake)

            @app.manage
            def peewee_create(name: str = "auto", *, auto: bool = False):
                """Create a migration.

                :param name: Set name of migration [auto]
                :param auto: Track changes and setup migrations automatically
                """
                with manager.allow_sync():
                    router.create(name, auto and list(self.manager.models))

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
            def peewee_merge(name: str = "initial"):
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

    def register(self, model_cls: Type["TVModel"]) -> Type["TVModel"]:
        """Register a model with self manager."""
        return self.manager.register(model_cls)

    def connection(self, *params, **opts) -> ConnectionContext:
        return self.database.connection(*params, **opts)

    def transaction(self, *params, **opts) -> TransactionContext:
        return self.database.transaction(*params, **opts)

    async def create_tables(self, *models_cls: Type["Model"]):
        """Create SQL tables."""
        await self.manager.create_tables(*(models_cls or self.manager.models))

    async def drop_tables(self, *models_cls: Type["Model"]):
        """Drop SQL tables."""
        await self.manager.drop_tables(*(models_cls or self.manager.models))

    def get_middleware(self) -> Callable:
        """Generate a middleware to manage connection/transaction."""

        if self.cfg.auto_transaction:

            async def middleware(handler, request, receive, send):
                async with self.connection():
                    async with self.transaction():
                        return await handler(request, receive, send)

        else:

            async def middleware(handler, request, receive, send):
                async with self.connection():
                    return await handler(request, receive, send)

        return middleware
