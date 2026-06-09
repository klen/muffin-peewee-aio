"""Migration commands."""

from typing import TYPE_CHECKING

import click
from peewee_migrate import Router

if TYPE_CHECKING:
    from muffin import Application
    from peewee_aio.manager import Manager

    from . import Plugin


def setup_migrations(plugin: "Plugin", app: "Application", manager: "Manager") -> None:
    """Initialize migration router and register CLI commands."""
    if not plugin.cfg.migrations_enabled:
        return

    router = Router(manager.pw_database, migrate_dir=plugin.cfg.migrations_path)
    plugin.router = router

    @app.manage
    def peewee_migrate(name: str = "", *, fake: bool = False):
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
            router.create(name, auto=auto and list(manager.models))

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

            click.secho(f"\nDone: {len(router.done)}, Pending: {len(router.diff)}", fg="blue")

    @app.manage
    def peewee_clear():
        """Clear migrations from DB."""
        with manager.allow_sync():
            plugin.router.clear()

    @app.manage
    def peewee_merge(name: str = "initial"):
        """Merge all migrations into one."""
        with manager.allow_sync():
            plugin.router.merge(name)
