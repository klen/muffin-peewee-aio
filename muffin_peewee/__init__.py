"""Support Peewee ORM for Muffin framework."""

import typing as t

import muffin
from muffin.plugins import BasePlugin
from peewee import Model
from peewee_migrate import Router
from peewee_aio.model import AIOModel
from peewee_aio.manager import Manager, cached_property

from .fields import JSONField, Choices


__version__ = "0.2.0"
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
        'connection': 'sqlite:///db.sqlite',
        'connection_params': {},

        # Manage connections automatically
        'auto_connection': True,
        'auto_transaction': True,

        # Setup migration engine
        'migrations_enabled': True,
        'migrations_path': 'migrations',
    }

    router: t.Optional[Router] = None
    manager: Manager = Manager('dummy://localhost')  # Dummy manager for support registration

    def setup(self, app: muffin.Application, **options):
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
        await self.manager.aio_database.connect()
        return self

    async def __aexit__(self, *args):
        """Disconnect the database."""
        await self.manager.aio_database.disconnect()

    def __getattr__(self, name: str) -> t.Any:
        """Proxy attrs to self database."""
        return getattr(self.manager, name)

    async def create_tables(self, *Models: Model):
        """Create SQL tables."""
        await self.manager.create_tables(*(Models or list(self.manager)))

    async def drop_tables(self, *Models: Model):
        """Drop SQL tables."""
        await self.manager.drop_tables(*(Models or list(self.manager)))

    def get_middleware(self) -> t.Callable:
        """Generate a middleware to manage connection/transaction."""

        async def middleware(handler, request, receive, send):
            async with self.manager.connection():
                return await handler(request, receive, send)

        if self.cfg.auto_transaction:

            async def middleware(handler, request, receive, send):  # noqa
                async with self.manager.connection():
                    async with self.manager.transaction():
                        return await handler(request, receive, send)

        return middleware

    @cached_property
    def Model(self) -> AIOModel:
        """Generate base async model class."""
        return self.manager.Model
