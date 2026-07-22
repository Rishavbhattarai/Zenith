"""Seeds demo users, a starter parts catalog, and sample assets.

Usage: python -m db.seed [--database-url ...]

Credentials are clearly-labeled demo values -- do not reuse in any
non-local environment.
"""

from __future__ import annotations

import asyncio
import os
import sys

import asyncpg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inventory.security import hash_password  # noqa: E402

DEMO_USERS = [
    ("admin", "admin-demo-pw", "admin"),
    ("field-tech-service", "field-tech-demo-pw", "field_tech"),
]

# Stock/threshold values chosen so a field note replacing one of these
# parts will plausibly push stock below the reorder threshold, making the
# autonomous re-order behavior (3.2) easy to demonstrate.
DEMO_PARTS = [
    ("power supply", 89.99, 3, 5, 10),
    ("fan", 12.50, 8, 5, 20),
    ("cpu temp sensor", 24.00, 6, 5, 15),
    ("network card", 45.00, 4, 3, 10),
    ("battery pack", 150.00, 2, 3, 5),
]

DEMO_ASSETS = [
    ("asset-0001", "Node 0001", "us-east-1"),
    ("asset-0042", "Node 0042", "us-east-1"),
    ("asset-1817", "Node 1817", "us-west-2"),
]


async def seed(database_url: str) -> None:
    conn = await asyncpg.connect(database_url)
    try:
        for username, password, role in DEMO_USERS:
            await conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES ($1, $2, $3) "
                "ON CONFLICT (username) DO NOTHING",
                username,
                hash_password(password),
                role,
            )

        for part_name, unit_price, stock, threshold, reorder_qty in DEMO_PARTS:
            await conn.execute(
                "INSERT INTO parts (part_name, unit_price, stock_quantity, reorder_threshold, reorder_quantity) "
                "VALUES ($1, $2, $3, $4, $5) ON CONFLICT (part_name) DO NOTHING",
                part_name,
                unit_price,
                stock,
                threshold,
                reorder_qty,
            )

        for asset_id, name, location in DEMO_ASSETS:
            await conn.execute(
                "INSERT INTO assets (asset_id, name, location) VALUES ($1, $2, $3) "
                "ON CONFLICT (asset_id) DO NOTHING",
                asset_id,
                name,
                location,
            )
    finally:
        await conn.close()


if __name__ == "__main__":
    url = os.environ.get("DATABASE_URL", "postgresql://localhost/zenith")
    asyncio.run(seed(url))
    print(f"Seeded {url}")
