import pytest

from inventory.service import record_installation

pytestmark = pytest.mark.asyncio


async def test_record_installation_decrements_stock(conn, part_factory, asset_factory):
    await part_factory(part_name="widget", stock_quantity=10, reorder_threshold=5)
    await asset_factory("asset-0001")

    result = await record_installation(conn, "asset-0001", "widget", 2, "tech-1")

    assert result.matched
    assert result.new_stock == 8
    assert not result.reorder_triggered

    row = await conn.fetchrow("SELECT stock_quantity FROM parts WHERE part_name = 'widget'")
    assert row["stock_quantity"] == 8


async def test_record_installation_triggers_reorder_below_threshold(conn, part_factory, asset_factory):
    await part_factory(part_name="fan", stock_quantity=6, reorder_threshold=5, reorder_quantity=20)
    await asset_factory("asset-0001")

    result = await record_installation(conn, "asset-0001", "fan", 2, "tech-1")

    assert result.new_stock == 4
    assert result.reorder_triggered

    reorder = await conn.fetchrow("SELECT quantity, status FROM reorder_requests")
    assert reorder["quantity"] == 20
    assert reorder["status"] == "pending"


async def test_record_installation_does_not_duplicate_pending_reorder(conn, part_factory, asset_factory):
    part_id = await part_factory(part_name="fan", stock_quantity=5, reorder_threshold=5)
    await asset_factory("asset-0001")

    await record_installation(conn, "asset-0001", "fan", 1, "tech-1")  # 5 -> 4, triggers first reorder
    result = await record_installation(conn, "asset-0001", "fan", 1, "tech-2")  # 4 -> 3, still below threshold

    assert not result.reorder_triggered  # already a pending reorder for this part
    count = await conn.fetchval(
        "SELECT count(*) FROM reorder_requests WHERE part_id = $1", part_id
    )
    assert count == 1


async def test_record_installation_unmatched_part(conn, asset_factory):
    await asset_factory("asset-0001")

    result = await record_installation(conn, "asset-0001", "nonexistent-part", 1, "tech-1")

    assert not result.matched
    assert result.new_stock is None
    assert not result.reorder_triggered
