from unittest import mock

import muffin
import peewee

import muffin_peewee


async def test_lifespan():

    app = muffin.Application("peewee", PEEWEE_CONNECTION="sqlite:///:memory:")
    db = muffin_peewee.Plugin(app)

    with (
        mock.patch.object(db.manager, "connect") as mock_connect,
        mock.patch.object(db.manager, "disconnect") as mock_disconnect,
    ):
        async with app.lifespan:
            assert mock_connect.called
            assert mock_connect.await_count == 1

        assert mock_disconnect.called
        assert mock_disconnect.await_count == 1


async def test_replica_config(tmp_path):

    app = muffin.Application(
        "peewee",
        PEEWEE_CONNECTION=f"sqlite:///{tmp_path / 'db.sqlite'}",
        PEEWEE_REPLICAS=[f"sqlite:///{tmp_path / 'replica.sqlite'}"],
    )
    db = muffin_peewee.Plugin(app)

    assert db.manager.replica_backends
    assert len(db.manager.replica_backends) == 1


async def test_replica_context_manager(tmp_path):

    app = muffin.Application(
        "peewee",
        PEEWEE_CONNECTION=f"sqlite:///{tmp_path / 'db.sqlite'}",
        PEEWEE_REPLICAS=[f"sqlite:///{tmp_path / 'replica.sqlite'}"],
    )
    db = muffin_peewee.Plugin(app)

    @db.register
    class User(peewee.Model):
        name = peewee.CharField()

    async with db.manager, db.manager.connection():
        await db.manager.create_tables(User)
        user = User(name="test")
        await db.manager.save(user)

    async with db.replica():
        assert db.manager.current_conn


async def test_auto_connect(tmp_path):

    app = muffin.Application(
        "peewee",
        PEEWEE_CONNECTION=f"sqlite:///{tmp_path / 'db.sqlite'}",
    )
    db = muffin_peewee.Plugin(app)

    assert app.internal_middlewares

    @db.register
    class User(peewee.Model):
        name = peewee.CharField()

    manager = db.manager
    async with manager, manager.connection(), manager.transaction() as trans:
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
