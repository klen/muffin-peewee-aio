"""Setup tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from muffin import Application
    from peewee_aio import AIOModel

    from muffin_peewee import Plugin


@pytest.fixture()
def aiolib():
    # Only asyncio supported for now
    return ("asyncio", {"use_uvloop": False})


@pytest.fixture(scope="session", autouse=True)
def _setup_logging():
    import logging

    logger = logging.getLogger("peewee")
    logger.setLevel(logging.DEBUG)


@pytest.fixture()
def app() -> Application:
    """Create a muffin application."""
    import muffin

    return muffin.Application(peewee_connection="sqlite:///:memory:")


@pytest.fixture()
async def db(app: Application) -> Plugin:
    import muffin_peewee

    return muffin_peewee.Plugin(app)


@pytest.fixture()
def model_cls(db: Plugin) -> AIOModel:
    return db.Model


@pytest.fixture()
async def transaction(db: Plugin):
    """Clean changes after test."""
    async with db.connection():
        async with db.transaction() as trans:
            yield trans
            await trans.rollback()
