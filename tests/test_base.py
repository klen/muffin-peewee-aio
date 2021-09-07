import peewee
import pytest


async def test_conftest(db, transaction):

    @db.register
    class Test(peewee.Model):
        data = peewee.CharField()

    with pytest.raises(peewee.DatabaseError):
        assert await db.manager.run(Test.select()) == []

    await db.conftest()
    assert await db.manager.run(Test.select()) == []


async def test_context_manager(app):
    import muffin_peewee

    async with muffin_peewee.Plugin(app) as db:
        assert db
