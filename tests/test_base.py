import peewee
import pytest


async def test_conftest(db, transaction):

    @db.register
    class Test(db.Model):
        data = peewee.CharField()

    with pytest.raises(peewee.DatabaseError):
        assert await Test.select() == []

    await db.create_tables()
    assert await Test.select() == []
    await db.drop_tables()


async def test_context_manager(app):
    import muffin_peewee

    async with muffin_peewee.Plugin(app) as db:
        assert db


async def test_delayed_registration(app):
    import muffin_peewee

    db = muffin_peewee.Plugin()
    assert db
    assert db.manager

    @db.register
    class TestModel(peewee.Model):
        data = peewee.CharField()

    assert TestModel._manager
    assert TestModel._meta.database
    assert TestModel._meta.database.database == ""

    manager = TestModel._manager

    db.setup(app)

    assert TestModel._manager is not manager
    assert TestModel._meta.database
    assert TestModel._meta.database.database == ":memory:"
