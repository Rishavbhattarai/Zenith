"""3.2: core inventory logic. record_installation is the single place that
decrements stock and decides whether a re-order is needed -- called both
by the /installations route and directly in tests."""

from __future__ import annotations

import asyncpg

from inventory.models import InstallationResult


async def record_installation(
    conn: asyncpg.Connection,
    asset_id: str,
    part_name: str,
    quantity: int,
    technician: str,
) -> InstallationResult:
    async with conn.transaction():
        part = await conn.fetchrow(
            "SELECT id, stock_quantity, reorder_threshold, reorder_quantity "
            "FROM parts WHERE lower(part_name) = lower($1)",
            part_name,
        )
        if part is None:
            return InstallationResult(part_name=part_name, matched=False)

        new_stock = part["stock_quantity"] - quantity
        await conn.execute(
            "UPDATE parts SET stock_quantity = $1 WHERE id = $2",
            new_stock,
            part["id"],
        )
        await conn.execute(
            "INSERT INTO part_installations (asset_id, part_id, quantity, technician) "
            "VALUES ($1, $2, $3, $4)",
            asset_id,
            part["id"],
            quantity,
            technician,
        )

        reorder_triggered = False
        if new_stock < part["reorder_threshold"]:
            result = await conn.execute(
                "INSERT INTO reorder_requests (part_id, quantity) VALUES ($1, $2) "
                "ON CONFLICT (part_id) WHERE status = 'pending' DO NOTHING",
                part["id"],
                part["reorder_quantity"],
            )
            # asyncpg returns "INSERT 0 1" on success, "INSERT 0 0" if the
            # partial unique index deduped it against an existing pending row.
            reorder_triggered = result.endswith(" 1")

        return InstallationResult(
            part_name=part_name,
            matched=True,
            new_stock=new_stock,
            reorder_triggered=reorder_triggered,
        )
