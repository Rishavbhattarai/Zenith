from __future__ import annotations

import os
from pathlib import Path

import asyncpg
import pytest
import pytest_asyncio

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://localhost/zenith_test"
)
SCHEMA_PATH = Path(__file__).parent.parent / "db" / "schema.sql"


@pytest_asyncio.fixture(scope="session")
async def _schema_applied():
    conn = await asyncpg.connect(TEST_DATABASE_URL)
    try:
        # Idempotent: schema.sql uses CREATE TABLE IF NOT EXISTS.
        await conn.execute(SCHEMA_PATH.read_text())
    finally:
        await conn.close()


@pytest_asyncio.fixture
async def conn(_schema_applied):
    """A connection wrapped in a transaction that's always rolled back, so
    each test starts from a clean, empty slate regardless of test order."""
    connection = await asyncpg.connect(TEST_DATABASE_URL)
    transaction = connection.transaction()
    await transaction.start()
    try:
        yield connection
    finally:
        await transaction.rollback()
        await connection.close()


@pytest.fixture
def part_factory(conn):
    async def _create(
        part_name="widget",
        unit_price=10,
        stock_quantity=10,
        reorder_threshold=5,
        reorder_quantity=20,
    ):
        row = await conn.fetchrow(
            "INSERT INTO parts (part_name, unit_price, stock_quantity, reorder_threshold, reorder_quantity) "
            "VALUES ($1, $2, $3, $4, $5) RETURNING id",
            part_name,
            unit_price,
            stock_quantity,
            reorder_threshold,
            reorder_quantity,
        )
        return row["id"]

    return _create


@pytest.fixture
def asset_factory(conn):
    async def _create(asset_id="asset-0001"):
        await conn.execute(
            "INSERT INTO assets (asset_id) VALUES ($1) ON CONFLICT DO NOTHING", asset_id
        )
        return asset_id

    return _create


class _ConnAsPool:
    """Adapts a single (transactional, rolled-back-after-test) asyncpg
    Connection to the subset of the asyncpg.Pool interface the app uses, so
    route tests get the same per-test isolation as direct service tests."""

    def __init__(self, connection: asyncpg.Connection):
        self._conn = connection

    def fetchrow(self, *a, **kw):
        return self._conn.fetchrow(*a, **kw)

    def fetch(self, *a, **kw):
        return self._conn.fetch(*a, **kw)

    def fetchval(self, *a, **kw):
        return self._conn.fetchval(*a, **kw)

    def execute(self, *a, **kw):
        return self._conn.execute(*a, **kw)

    def acquire(self):
        conn = self._conn

        class _Ctx:
            async def __aenter__(self):
                return conn

            async def __aexit__(self, *exc):
                return False

        return _Ctx()


@pytest_asyncio.fixture
async def client(conn):
    import httpx

    from inventory.db import get_pool
    from inventory.main import app

    app.dependency_overrides[get_pool] = lambda: _ConnAsPool(conn)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_pool, None)
