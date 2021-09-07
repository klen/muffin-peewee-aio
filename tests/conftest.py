"""Setup tests."""

import pytest


@pytest.fixture
def aiolib():
    # Only asyncio supported for now
    return ('asyncio', {'use_uvloop': False})


@pytest.fixture(scope='session', autouse=True)
def setup_logging():
    import logging

    logger = logging.getLogger('peewee')
    logger.setLevel(logging.DEBUG)


@pytest.fixture
def app():
    """Create a muffin application."""
    import muffin

    return muffin.Application(peewee_connection='sqlite:///:memory:')


@pytest.fixture
async def db(app):
    import muffin_peewee

    return muffin_peewee.Plugin(app)


@pytest.fixture
async def transaction(db):
    """Clean changes after test."""
    async with db.connection():
        async with db.transaction() as trans:
            yield trans
            await trans.rollback()
