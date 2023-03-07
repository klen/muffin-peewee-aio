import sys
from unittest import mock

import muffin
import peewee


async def test_lifespan():
    import muffin_peewee

    app = muffin.Application("peewee", PEEWEE_CONNECTION="sqlite:///:memory:")
    db = muffin_peewee.Plugin(app)

    with mock.patch.object(db.manager.aio_database, "connect") as mock_connect, mock.patch.object(
        db.manager.aio_database, "disconnect",
    ) as mock_disconnect:
        async with app.lifespan:
            assert mock_connect.called
            if sys.version_info > (3, 8):
                assert mock_connect.await_count == 1

        assert mock_disconnect.called
        if sys.version_info > (3, 8):
            assert mock_disconnect.await_count == 1


async def test_auto_connect(tmp_path):
    from muffin_peewee import Plugin

    app = muffin.Application(
        "peewee", PEEWEE_CONNECTION=f"sqlite:///{ tmp_path / 'db.sqlite' }",
    )
    db = Plugin(app)

    assert app.internal_middlewares

    @db.register
    class User(peewee.Model):
        name = peewee.CharField()

    async with db.manager as manager:
        async with manager.connection():
            async with manager.transaction() as trans:
                await manager.create_tables(User)
                user = User(name="test")
                await manager.save(user)
                assert await manager.get(User)
                await trans.commit()

    @app.route("/")
    async def index(request):
        return await manager.count(User.select())

    client = muffin.TestClient(app)
    async with client.lifespan():
        res = await client.get("/")
        assert res.status_code == 200
        assert await res.text() == "1"
