"""Setup tests."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

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


@pytest.fixture(scope="session", autouse=True)
def _setup_logging():

    logger = logging.getLogger("peewee")
    logger.setLevel(logging.DEBUG)


@pytest.fixture
def app() -> Application:
    """Create a muffin application."""

    return muffin.Application(peewee_connection="sqlite:///:memory:")


@pytest.fixture
async def db(app: Application) -> Plugin:

    return muffin_peewee.Plugin(app)


@pytest.fixture
def model_cls(db: Plugin) -> AIOModel:
    return db.Model


@pytest.fixture
async def transaction(db: Plugin):
    """Clean changes after test."""
    async with db.connection(), db.transaction() as trans:
        yield trans
        await trans.rollback()
