import pytest

from inventory.security import create_token, hash_password

pytestmark = pytest.mark.asyncio


async def _make_user(conn, username, role, password="pw"):
    await conn.execute(
        "INSERT INTO users (username, password_hash, role) VALUES ($1, $2, $3)",
        username,
        hash_password(password),
        role,
    )


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_login_succeeds_with_correct_password(client, conn):
    await _make_user(conn, "alice", "admin", password="s3cret")

    resp = await client.post("/auth/login", json={"username": "alice", "password": "s3cret"})

    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"
    assert resp.json()["access_token"]


async def test_login_rejects_wrong_password(client, conn):
    await _make_user(conn, "alice", "admin", password="s3cret")

    resp = await client.post("/auth/login", json={"username": "alice", "password": "wrong"})

    assert resp.status_code == 401


async def test_field_tech_cannot_patch_part_pricing(client, part_factory):
    part_id = await part_factory(part_name="widget", unit_price=10)
    token = create_token("bob", "field_tech")

    resp = await client.patch(
        f"/parts/{part_id}", json={"unit_price": 999}, headers=_auth(token)
    )

    assert resp.status_code == 403


async def test_admin_can_patch_part_pricing(client, part_factory):
    part_id = await part_factory(part_name="widget", unit_price=10)
    token = create_token("carol", "admin")

    resp = await client.patch(
        f"/parts/{part_id}", json={"unit_price": 999}, headers=_auth(token)
    )

    assert resp.status_code == 200
    assert float(resp.json()["unit_price"]) == 999.0


async def test_installations_endpoint_requires_auth(client, part_factory, asset_factory):
    await part_factory(part_name="widget")
    await asset_factory("asset-0001")

    resp = await client.post(
        "/installations",
        json={"asset_id": "asset-0001", "part_name": "widget", "quantity": 1, "technician": "bob"},
    )

    assert resp.status_code == 401  # HTTPBearer: no credentials supplied


async def test_installations_endpoint_works_for_field_tech(client, part_factory, asset_factory):
    await part_factory(part_name="widget", stock_quantity=10, reorder_threshold=2)
    await asset_factory("asset-0001")
    token = create_token("bob", "field_tech")

    resp = await client.post(
        "/installations",
        json={"asset_id": "asset-0001", "part_name": "widget", "quantity": 1, "technician": "bob"},
        headers=_auth(token),
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["matched"]
    assert body["new_stock"] == 9
