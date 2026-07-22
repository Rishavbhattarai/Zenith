from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from inventory.db import get_pool
from inventory.models import (
    Asset,
    InstallationRequest,
    InstallationResult,
    LoginRequest,
    Part,
    PartUpdateRequest,
    ReorderRequest,
    TokenResponse,
)
from inventory.security import Principal, create_token, current_principal, require_role, verify_password
from inventory.service import record_installation

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest, pool: asyncpg.Pool = Depends(get_pool)) -> TokenResponse:
    row = await pool.fetchrow(
        "SELECT username, password_hash, role FROM users WHERE username = $1", req.username
    )
    if row is None or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return TokenResponse(access_token=create_token(row["username"], row["role"]), role=row["role"])


@router.get("/parts", response_model=list[Part])
async def list_parts(
    pool: asyncpg.Pool = Depends(get_pool),
    _: Principal = Depends(current_principal),
) -> list[Part]:
    rows = await pool.fetch("SELECT * FROM parts ORDER BY part_name")
    return [Part(**dict(r)) for r in rows]


@router.patch("/parts/{part_id}", response_model=Part)
async def update_part(
    part_id: int,
    req: PartUpdateRequest,
    pool: asyncpg.Pool = Depends(get_pool),
    _: Principal = Depends(require_role("admin")),
) -> Part:
    fields = req.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{col} = ${i + 2}" for i, col in enumerate(fields))
    row = await pool.fetchrow(
        f"UPDATE parts SET {set_clause} WHERE id = $1 RETURNING *",
        part_id,
        *fields.values(),
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Part not found")
    return Part(**dict(row))


@router.post("/installations", response_model=InstallationResult)
async def create_installation(
    req: InstallationRequest,
    pool: asyncpg.Pool = Depends(get_pool),
    _: Principal = Depends(current_principal),
) -> InstallationResult:
    async with pool.acquire() as conn:
        return await record_installation(conn, req.asset_id, req.part_name, req.quantity, req.technician)


@router.get("/assets", response_model=list[Asset])
async def list_assets(
    pool: asyncpg.Pool = Depends(get_pool),
    _: Principal = Depends(current_principal),
) -> list[Asset]:
    rows = await pool.fetch("SELECT asset_id, name, location FROM assets ORDER BY asset_id")
    return [Asset(**dict(r)) for r in rows]


@router.get("/reorder-requests", response_model=list[ReorderRequest])
async def list_reorder_requests(
    pool: asyncpg.Pool = Depends(get_pool),
    _: Principal = Depends(current_principal),
) -> list[ReorderRequest]:
    rows = await pool.fetch(
        "SELECT r.id, r.part_id, p.part_name, r.quantity, r.status "
        "FROM reorder_requests r JOIN parts p ON p.id = r.part_id "
        "ORDER BY r.created_at DESC"
    )
    return [ReorderRequest(**dict(r)) for r in rows]
