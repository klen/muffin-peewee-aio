"""Support Peewee ORM for Muffin framework."""

import typing as t

import muffin
from muffin.plugins import BasePlugin
from peewee_migrate import Router
from peewee_aio.model import AIOModel
from peewee_aio.manager import Manager, cached_property

from .fields import JSONField, Choices


__version__ = "0.0.6"
__project__ = "muffin-peewee-aio"
__author__ = "Kirill Klenov <horneds@gmail.com>"
__license__ = "MIT"


__all__ = 'Plugin', 'JSONField', 'Choices'


assert JSONField and Choices


class Plugin(BasePlugin):

    """Muffin Peewee Plugin."""

    name = "peewee"
    defaults = {

        # Connection params
        'connection': 'sqlite+async:///db.sqlite',
        'connection_params': {},

        # Manage connections automatically
        'auto_connection': True,
        'auto_transaction': True,

        # Setup migration engine
        'migrations_enabled': True,
        'migrations_path': 'migrations',
    }

    router: t.Optional[Router] = None
    manager: t.Optional[Manager] = None

    def setup(self, app: muffin.Application, **options):
        """Init the plugin."""
        super().setup(app, **options)
        self.manager = manager = Manager(self.cfg.connection, **self.cfg.connection_params)

        if self.cfg.migrations_enabled:
            router = Router(self.manager.pw_database, migrate_dir=self.cfg.migrations_path)
            self.router = router

            # Register migration commands
            @app.manage
            def pw_migrate(name: str = None, fake: bool = False):
                """Run application's migrations.

                :param name: Choose a migration' name
                :param fake: Run as fake. Update migration history and don't touch the database
                """
                with manager.allow_sync():
                    router.run(name, fake=fake)

            @app.manage
            def pw_create(name: str = 'auto', auto: bool = False):
                """Create a migration.

                :param name: Set name of migration [auto]
                :param auto: Track changes and setup migrations automatically
                """
                with manager.allow_sync():
                    router.create(name, auto and [m for m in self.models.values()])

            @app.manage
            def pw_rollback(name: str = None):
                """Rollback a migration.

                :param name: Migration name (actually it always should be a last one)
                """
                with manager.allow_sync():
                    router.rollback(name)

            @app.manage
            def pw_list():
                """List migrations."""
                with manager.allow_sync():
                    router.logger.info('Migrations are done:')
                    router.logger.info('\n'.join(self.router.done))
                    router.logger.info('')
                    router.logger.info('Migrations are undone:')
                    router.logger.info('\n'.join(self.router.diff))

        if self.cfg.auto_connection:
            app.middleware(self.get_middleware(), insert_first=True)

    async def startup(self):
        """Connect to the database (initialize a pool and etc)."""
        await self.manager.connect()

    async def shutdown(self):
        """Disconnect from the database (close a pool and etc.)."""
        await self.manager.disconnect()

    async def __aenter__(self) -> 'Plugin':
        """Connect the database."""
        manager = t.cast(Manager, self.manager)
        await manager.aio_database.connect()
        return self

    async def __aexit__(self, *args):
        """Disconnect the database."""
        await self.manager.aio_database.disconnect()

    @cached_property
    def Model(self) -> AIOModel:
        """Generate base async model class."""
        manager = t.cast(Manager, self.manager)
        return manager.Model

    def __getattr__(self, name: str) -> t.Any:
        """Proxy attrs to self database."""
        return getattr(self.manager, name)

    def get_middleware(self) -> t.Callable:
        """Generate a middleware to manage connection/transaction."""

        async def middleware(handler, request, receive, send):
            async with self.manager.connection(True):
                return await handler(request, receive, send)

        if self.cfg.auto_transaction:

            async def middleware(handler, request, receive, send):  # noqa
                async with self.manager.connection(True):
                    async with self.manager.transaction():
                        return await handler(request, receive, send)

        return middleware

    async def conftest(self):
        """Prepare database tables for tests."""
        await self.manager.create_tables(*self.manager)
