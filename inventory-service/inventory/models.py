from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    role: str


class Part(BaseModel):
    id: int
    part_name: str
    unit_price: Decimal
    stock_quantity: int
    reorder_threshold: int
    reorder_quantity: int


class PartUpdateRequest(BaseModel):
    unit_price: Decimal | None = None
    reorder_threshold: int | None = None
    reorder_quantity: int | None = None


class InstallationRequest(BaseModel):
    asset_id: str
    part_name: str
    quantity: int = 1
    technician: str


class InstallationResult(BaseModel):
    part_name: str
    matched: bool
    new_stock: int | None = None
    reorder_triggered: bool = False


class Asset(BaseModel):
    asset_id: str
    name: str | None = None
    location: str | None = None


class ReorderRequest(BaseModel):
    id: int
    part_id: int
    part_name: str
    quantity: int
    status: str
