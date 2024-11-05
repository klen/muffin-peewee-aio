"""Support Peewee ORM for Muffin framework."""

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Callable, ClassVar, Optional, Union

import click
import peewee as pw
from aio_databases.database import ConnectionContext, TransactionContext
from muffin.plugins import BasePlugin, PluginNotInstalledError
from peewee_aio.manager import Manager
from peewee_aio.model import AIOModel
from peewee_migrate import Router

from .fields import (
    Choices,
    IntEnumField,
    JSONAsyncPGField,
    JSONLikeField,
    JSONPGField,
    StrEnumField,
    URLField,
)

if TYPE_CHECKING:
    from muffin import Application
    from peewee_aio.types import TVModel

__all__ = (
    "Plugin",
    "Choices",
    "StrEnumField",
    "IntEnumField",
    "EnumField",
    "URLField",
    "JSONLikeField",
    "JSONPGField",
)

EnumField = StrEnumField


class Plugin(BasePlugin):
    """Muffin Peewee Plugin."""

    name = "peewee"
    defaults: ClassVar = {
        # Connection params
        "connection": "sqlite:///db.sqlite",
        "connection_params": {},
        # Manage connections automatically
        "auto_connection": True,
        "auto_transaction": True,
        # Setup migration engine
        "migrations_enabled": True,
        "migrations_path": "migrations",
        # Support pytest
        "pytest_setup_db": True,
    }

    router: Router
    manager: Manager = Manager(
        "dummy://localhost",
    )  # Dummy manager for support registration

    def setup(self, app: "Application", **options):  # noqa: C901
        """Init the plugin."""
        super().setup(app, **options)

        # Init manager and rebind models
        manager = Manager(self.cfg.connection, **self.cfg.connection_params)
        for model in list(self.manager):
            manager.register(model)
        self.manager = manager

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
                    router.create(name, auto=auto and list(self.manager.models))

            @app.manage
            def peewee_rollback():
                """Rollback the latest migration."""
                with manager.allow_sync():
                    router.rollback()

            @app.manage
            def peewee_list():
                """List migrations."""
                click.secho("List of migrations:\n", fg="blue")
                with manager.allow_sync():
                    for migration in router.done:
                        click.echo(f"- [x] {migration}")

                    for migration in router.diff:
                        click.echo(f"- [ ] {migration}")

                    click.secho(
                        f"\nDone: {len(router.done)}, Pending: {len(router.diff)}", fg="blue"
                    )

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
        await self.manager.connect()

    async def shutdown(self):
        """Disconnect from the database (close a pool and etc.)."""
        await self.manager.disconnect()

    async def __aenter__(self) -> "Plugin":  # type: ignore[]
        """Connect the database."""
        await self.manager.connect()
        return self

    async def __aexit__(self, *exit_args):
        """Disconnect the database."""
        await self.manager.disconnect()

    def register(self, model_cls: type["TVModel"]) -> type["TVModel"]:
        """Register a model with self manager."""
        return self.manager.register(model_cls)

    def connection(self, *params, **opts) -> ConnectionContext:
        return self.manager.connection(*params, **opts)

    def transaction(self, *params, **opts) -> TransactionContext:
        return self.manager.transaction(*params, **opts)

    async def create_tables(self, *models_cls: type[pw.Model]):
        """Create SQL tables."""
        await self.manager.create_tables(*(models_cls or self.manager.models))

    async def drop_tables(self, *models_cls: type[pw.Model]):
        """Drop SQL tables."""
        await self.manager.drop_tables(*(models_cls or self.manager.models))

    def get_middleware(self) -> Callable:
        """Generate a middleware to manage connection/transaction."""

        if self.cfg.auto_transaction:

            async def middleware(handler, request, receive, send):
                async with self.connection(), self.transaction():
                    return await handler(request, receive, send)

        else:

            async def middleware(handler, request, receive, send):
                async with self.connection():
                    return await handler(request, receive, send)

        return middleware

    @property
    def Model(self) -> type[AIOModel]:  # noqa: N802
        if self.app is None:
            raise PluginNotInstalledError

        return self.manager.Model

    @property
    def JSONField(self) -> Union[type[JSONLikeField], type[JSONPGField]]:  # noqa: N802
        """Return a JSON field for the current backend."""
        if self.app is None:
            raise PluginNotInstalledError

        backend = self.manager.backend
        if backend.name == "asyncpg":
            return JSONAsyncPGField

        if backend.db_type == "postgresql":
            return JSONPGField

        return JSONLikeField

    @asynccontextmanager
    async def conftest(self):
        """Initialize a database schema for pytest."""
        if self.cfg.pytest_setup_db:
            async with self, self.connection():
                await self.create_tables()
                yield self
                await self.drop_tables()
        else:
            yield self


# ruff: noqa: FA100, FA101, FA102
