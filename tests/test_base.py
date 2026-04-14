from __future__ import annotations

from typing import TYPE_CHECKING

import peewee
from peewee_aio import AIOModel

import muffin_peewee

if TYPE_CHECKING:
    from muffin import Application

    from muffin_peewee import Plugin


async def test_conftest(db: Plugin):
    @db.register
    class Test(AIOModel):
        data = peewee.CharField()

    await db.create_tables()
    assert await Test.select() == []
    await db.drop_tables()


async def test_context_manager(app: Application):

    async with muffin_peewee.Plugin(app) as db:
        assert db


async def test_delayed_registration(app: Application):
    db = muffin_peewee.Plugin()
    assert db
    assert db.manager

    @db.register
    class TestModel(peewee.Model):
        data = peewee.CharField()

    assert TestModel._manager
    assert TestModel._meta.database
    assert not TestModel._meta.database.database

    manager = TestModel._manager

    db.setup(app)

    assert TestModel._manager is not manager
    assert TestModel._meta.database
    assert TestModel._meta.database.database == ":memory:"
