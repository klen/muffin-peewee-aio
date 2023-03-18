from __future__ import annotations

from typing import TYPE_CHECKING

import peewee
import pytest
from peewee_aio import AIOModel

if TYPE_CHECKING:
    from aio_databases.backends import ABCTransaction
    from muffin import Application

    from muffin_peewee import Plugin


async def test_conftest(db: Plugin, transaction: ABCTransaction):
    @db.register
    class Test(AIOModel):
        data = peewee.CharField()

    with pytest.raises(peewee.DatabaseError):
        assert await Test.select() == []

    await db.create_tables()
    assert await Test.select() == []
    await db.drop_tables()


async def test_context_manager(app: Application):
    import muffin_peewee

    async with muffin_peewee.Plugin(app) as db:
        assert db


async def test_delayed_registration(app: Application):
    import muffin_peewee

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
