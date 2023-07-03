import pytest as pytest

from db.pool import init_db
from db.pool import pool


@pytest.fixture()
async def conn():
    await pool.open(wait=True)
    async with pool.connection() as conn:
        yield conn


@pytest.fixture(name='init_db', autouse=True)
async def _init_db():
    await init_db()
