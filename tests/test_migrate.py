from unittest import mock

import pytest


@pytest.fixture
def backend():
    return "aiosqlite"


MIGRATION_COMMANDS = (
    "peewee-create",
    "peewee-migrate",
    "peewee-rollback",
    "peewee-list",
    "peewee-clear",
    "peewee-merge",
)


@pytest.mark.parametrize("command", MIGRATION_COMMANDS)
async def test_migration_command_is_registered(app, db, command):
    assert command in app.manage.commands


async def test_router_is_initialized(db):
    assert db.router


async def test_create_migration(db, tmp_path):
    migrate_dir = tmp_path / "migrations"
    migrate_dir.mkdir()
    db.router.migrate_dir = migrate_dir

    with db.manager.allow_sync():
        name = db.router.create("test")

        assert name == "001_test"
        assert db.router.todo
        assert not db.router.done
        assert db.router.diff


async def test_run_migrations(db, tmp_path):
    migrate_dir = tmp_path / "migrations"
    migrate_dir.mkdir()
    db.router.migrate_dir = migrate_dir

    with db.manager.allow_sync():
        db.router.create("test")
        db.router.run()

        assert db.router.done
        assert not db.router.diff

        name = db.router.create()

        assert name == "002_auto"


async def test_list_migrations_command(db, tmp_path):
    migrate_dir = tmp_path / "migrations"
    migrate_dir.mkdir()
    db.router.migrate_dir = migrate_dir

    with db.manager.allow_sync():
        db.router.create("test")
        db.router.run()

    command = db.app.manage.commands["peewee-list"]
    with (
        mock.patch("muffin_peewee.migrations.click.secho") as mock_secho,
        mock.patch("muffin_peewee.migrations.click.echo") as mock_echo,
    ):
        command()

    assert mock_secho.called
    assert mock_echo.called


async def test_rollback_command(db, tmp_path):
    migrate_dir = tmp_path / "migrations"
    migrate_dir.mkdir()
    db.router.migrate_dir = migrate_dir

    with db.manager.allow_sync():
        db.router.create("test")
        db.router.run()

        assert db.router.done

    command = db.app.manage.commands["peewee-rollback"]
    command()

    with db.manager.allow_sync():
        assert not db.router.done
