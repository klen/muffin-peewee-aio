import shutil
from unittest import mock

import muffin
import peewee
import pytest
from aio_databases import ReadOnlyError

import muffin_peewee


async def test_lifespan_calls_connect_and_disconnect():
    app = muffin.Application("peewee", PEEWEE_CONNECTION="sqlite:///:memory:")
    db = muffin_peewee.Plugin(app)

    with (
        mock.patch.object(db.manager, "connect") as mock_connect,
        mock.patch.object(db.manager, "disconnect") as mock_disconnect,
    ):
        async with app.lifespan:
            pass

    assert mock_connect.await_count == 1
    assert mock_disconnect.await_count == 1


async def test_replica_config_registers_replica_backend(tmp_path):
    app = muffin.Application(
        "peewee",
        PEEWEE_CONNECTION=f"sqlite:///{tmp_path / 'db.sqlite'}",
        PEEWEE_REPLICAS=[f"sqlite:///{tmp_path / 'replica.sqlite'}"],
    )
    db = muffin_peewee.Plugin(app)

    assert len(db.manager.replica_backends) == 1


async def test_replica_context_manager_uses_read_only_connection(tmp_path):
    app = muffin.Application(
        "peewee",
        PEEWEE_CONNECTION=f"sqlite:///{tmp_path / 'db.sqlite'}",
        PEEWEE_REPLICAS=[f"sqlite:///{tmp_path / 'replica.sqlite'}"],
    )
    db = muffin_peewee.Plugin(app)

    @db.register
    class User(db.Model):
        name = peewee.CharField()

    async with db.manager:
        await db.manager.create_tables(User)
        await User.create(name="common")
        shutil.copyfile(tmp_path / "db.sqlite", tmp_path / "replica.sqlite")
        await User.create(name="primary")

    async with db.replica():
        assert db.manager.current_conn.read_only
        users = await User.select()
        assert [user.name for user in users] == ["common"]

        with pytest.raises(ReadOnlyError):
            await User.create(name="should_fail")


async def test_middleware_auto_connects_and_serves_requests(tmp_path):
    app = muffin.Application(
        "peewee",
        PEEWEE_CONNECTION=f"sqlite:///{tmp_path / 'db.sqlite'}",
    )
    db = muffin_peewee.Plugin(app)

    @db.register
    class User(peewee.Model):
        name = peewee.CharField()

    manager = db.manager
    async with manager, manager.connection(), manager.transaction() as trans:
        await manager.create_tables(User)
        await manager.save(User(name="test"))
        await trans.commit()

    @app.route("/")
    async def index(request):
        return await manager.count(User.select())

    client = muffin.TestClient(app)
    async with client.lifespan():
        response = await client.get("/")

    assert response.status_code == 200
    assert await response.text() == "1"


async def test_auto_connection_disabled(tmp_path):
    app = muffin.Application(
        "peewee",
        PEEWEE_CONNECTION=f"sqlite:///{tmp_path / 'db.sqlite'}",
        PEEWEE_AUTO_CONNECTION=False,
    )
    muffin_peewee.Plugin(app)

    assert not app.internal_middlewares


async def test_auto_transaction_disabled(tmp_path):
    app = muffin.Application(
        "peewee",
        PEEWEE_CONNECTION=f"sqlite:///{tmp_path / 'db.sqlite'}",
        PEEWEE_AUTO_TRANSACTION=False,
    )
    db = muffin_peewee.Plugin(app)

    @db.register
    class User(peewee.Model):
        name = peewee.CharField()

    manager = db.manager
    async with manager, manager.connection(), manager.transaction() as trans:
        await manager.create_tables(User)
        await manager.save(User(name="test"))
        await trans.commit()

    @app.route("/")
    async def index(request):
        return await manager.count(User.select())

    client = muffin.TestClient(app)
    async with client.lifespan():
        response = await client.get("/")

    assert response.status_code == 200
    assert await response.text() == "1"
