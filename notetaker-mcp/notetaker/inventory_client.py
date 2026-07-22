"""Records parts_used from an extraction against the Phase 3
inventory-service, so a part mentioned in a field note actually decrements
stock and can trigger an autonomous re-order. Follows the same
inject-a-client pattern as notetaker.safety's TelemetryFetcher.
"""

from __future__ import annotations

import os
from typing import Protocol

import httpx

from notetaker.schema import InventoryUpdate


class InventoryRecorder(Protocol):
    def record(self, asset_id: str, part_name: str, quantity: int, technician: str) -> InventoryUpdate: ...


class InventoryClient:
    """Authenticates once as the seeded field-tech service account and
    reuses the JWT for subsequent /installations calls."""

    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: float = 3.0,
    ) -> None:
        self._base_url = (base_url or os.environ.get("INVENTORY_SERVICE_URL", "http://localhost:8001")).rstrip("/")
        self._username = username or os.environ.get("FIELD_SERVICE_USERNAME", "field-tech-service")
        self._password = password or os.environ.get("FIELD_SERVICE_PASSWORD", "field-tech-demo-pw")
        self._timeout = timeout
        self._token: str | None = None

    def _login(self) -> str:
        resp = httpx.post(
            f"{self._base_url}/auth/login",
            json={"username": self._username, "password": self._password},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def record(self, asset_id: str, part_name: str, quantity: int, technician: str) -> InventoryUpdate:
        try:
            if self._token is None:
                self._token = self._login()

            resp = httpx.post(
                f"{self._base_url}/installations",
                json={
                    "asset_id": asset_id,
                    "part_name": part_name,
                    "quantity": quantity,
                    "technician": technician,
                },
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=self._timeout,
            )
            if resp.status_code == 401:
                # Token may have expired; retry once with a fresh login.
                self._token = self._login()
                resp = httpx.post(
                    f"{self._base_url}/installations",
                    json={
                        "asset_id": asset_id,
                        "part_name": part_name,
                        "quantity": quantity,
                        "technician": technician,
                    },
                    headers={"Authorization": f"Bearer {self._token}"},
                    timeout=self._timeout,
                )
            resp.raise_for_status()
            return InventoryUpdate(**resp.json())
        except httpx.HTTPError:
            # Inventory service unreachable/erroring shouldn't break note
            # processing -- surface as unmatched so the caller can see the
            # part wasn't actually recorded.
            return InventoryUpdate(part_name=part_name, matched=False)
