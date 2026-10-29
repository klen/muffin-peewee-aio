from __future__ import annotations

from typing import TYPE_CHECKING

import peewee
import pytest
from peewee_aio import AIOModel

import muffin_peewee

if TYPE_CHECKING:
    from muffin import Application

    from muffin_peewee import Plugin


async def test_create_tables_and_query(db: Plugin):
    @db.register
    class Test(AIOModel):
        data = peewee.CharField()

    await db.create_tables()
    result = await Test.select()

    assert result == []

    await db.drop_tables()


async def test_plugin_context_manager_connects(app: Application):
    async with muffin_peewee.Plugin(app) as db:
        assert db.manager


async def test_delayed_registration_rebinds_model(app: Application):
    db = muffin_peewee.Plugin()
    original_manager = db.manager

    @db.register
    class TestModel(peewee.Model):
        data = peewee.CharField()

    assert TestModel._manager is original_manager
    assert TestModel._meta.database
    assert not TestModel._meta.database.database

    db.setup(app)

    assert TestModel._manager is not original_manager
    assert TestModel._meta.database.database == ":memory:"


async def test_model_property_returns_manager_model(db: Plugin):
    assert db.Model is db.manager.Model


async def test_conftest_without_setup_db(app: Application):
    db = muffin_peewee.Plugin(app, pytest_setup_db=False)
    async with db.conftest() as plugin:
        assert plugin is db


async def test_disabled_plugin_is_not_wired(app: Application):
    db = muffin_peewee.Plugin(app, disabled=True)

    assert db.cfg.disabled
    assert not app.internal_middlewares
    assert not [name for name in app.manage.commands if name.startswith("peewee-")]


async def test_conftest_drops_tables_after_failure(db: Plugin):
    @db.register
    class Row(peewee.Model):
        name = peewee.CharField()

    async def failing_test():
        async with db.conftest():
            await Row.create(name="left over")
            raise RuntimeError("test failed")

    with pytest.raises(RuntimeError):
        await failing_test()

    async with db, db.connection():
        await db.create_tables(Row)
        assert await db.manager.count(Row.select()) == 0
