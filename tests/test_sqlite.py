from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import muffin_peewee

if TYPE_CHECKING:
    from muffin import Application

    from muffin_peewee import Plugin


@pytest.fixture
async def db(app: Application) -> Plugin:
    return muffin_peewee.Plugin(
        app,
        connection="aiosqlite:///file:memdb1?mode=memory&cache=shared",
        connection_params={"uri": True},
    )


async def test_sqlite_backend_name(db):
    assert db.manager.backend.name == "aiosqlite"
