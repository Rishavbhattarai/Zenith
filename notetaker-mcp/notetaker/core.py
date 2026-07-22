"""Single source of truth for processing a field note, shared by both
transports (mcp_server.py, http_api.py)."""

from __future__ import annotations

from notetaker.inventory_client import InventoryClient, InventoryRecorder
from notetaker.llm.base import LLMClient
from notetaker.safety import IngestionMeshFetcher, TelemetryFetcher, check
from notetaker.schema import InventoryUpdate, NoteProcessingResult


def process_field_note(
    raw_text: str,
    llm: LLMClient,
    asset_id: str | None = None,
    technician: str = "unspecified",
    fetcher: TelemetryFetcher | None = None,
    inventory: InventoryRecorder | None = None,
) -> NoteProcessingResult:
    extraction = llm.extract(raw_text, asset_id=asset_id)
    safety = check(extraction, fetcher or IngestionMeshFetcher())

    inventory_client = inventory or InventoryClient()
    inventory_updates: list[InventoryUpdate] = []
    for part in extraction.parts_used:
        target_asset = asset_id or (
            extraction.telemetry_annotations[0].asset_id if extraction.telemetry_annotations else None
        )
        if target_asset is None:
            continue  # no asset context to attribute the install to
        inventory_updates.append(
            inventory_client.record(target_asset, part.part_name, part.quantity, technician)
        )

    return NoteProcessingResult(extraction=extraction, safety=safety, inventory=inventory_updates)
