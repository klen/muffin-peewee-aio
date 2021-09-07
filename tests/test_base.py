import peewee
import pytest


async def test_example():
    from muffin import TestClient
    from example import app, db

    assert app
    assert db

    client = TestClient(app)

    async with client.lifespan():
        res = await client.get('/')
        assert res.status_code == 200


async def test_conftest(db, transaction):

    @db.register
    class Test(peewee.Model):
        data = peewee.CharField()

    with pytest.raises(peewee.DatabaseError):
        assert await db.manager.run(Test.select()) == []

    await db.conftest()
    assert await db.manager.run(Test.select()) == []
