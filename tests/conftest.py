"""Setup tests."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import uuid4

import muffin
import pytest

import muffin_peewee

if TYPE_CHECKING:
    from muffin import Application
    from peewee_aio import AIOModel

    from muffin_peewee import Plugin


@pytest.fixture
def aiolib():
    # Only asyncio supported for now
    return ("asyncio", {"loop_factory": None})


BACKEND_URLS: dict[str, str] = {
    "aiosqlite": "aiosqlite:///:memory:",
    "aiopg": "aiopg://test:test@localhost:5432/tests",
    "asyncpg": "asyncpg://test:test@localhost:5432/tests",
}

BACKEND_PARAMS = {
    "asyncpg": {"json": True},
}


@pytest.fixture(scope="session", params=["aiosqlite", *BACKEND_URLS])
def backend(request):
    return request.param


@pytest.fixture(scope="session", autouse=True)
def _setup_logging():

    logger = logging.getLogger("peewee")
    logger.setLevel(logging.DEBUG)


@pytest.fixture
def app() -> Application:
    """Create a muffin application."""

    return muffin.Application(peewee_connection="sqlite:///:memory:")


@pytest.fixture
async def db(app: Application, backend, tmp_path) -> Plugin:
    if backend == "aiosqlite":
        url = f"aiosqlite:///{tmp_path}-test-aio-db-{uuid4().hex}.sqlite"
    else:
        url = BACKEND_URLS[backend]

    params = BACKEND_PARAMS.get(backend, {})
    return muffin_peewee.Plugin(app, connection=url, connection_params=params)


@pytest.fixture
def model_cls(db: Plugin) -> AIOModel:
    return db.Model


@pytest.fixture
async def transaction(db: Plugin):
    """Clean changes after test."""
    async with db.connection(), db.transaction() as trans:
        yield trans
        await trans.rollback()
