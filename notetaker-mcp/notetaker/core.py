"""Single source of truth for processing a field note, shared by both
transports (mcp_server.py, http_api.py)."""

from __future__ import annotations

import uuid

from notetaker.events import EVENT_LOG
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
    note_id = uuid.uuid4().hex[:8]
    EVENT_LOG.emit(note_id, "received", f"Field note received (asset hint: {asset_id or 'none'})")

    extraction = llm.extract(raw_text, asset_id=asset_id)
    EVENT_LOG.emit(
        note_id,
        "extracted",
        f"Extracted {len(extraction.action_items)} action item(s), "
        f"{len(extraction.parts_used)} part(s), {len(extraction.telemetry_annotations)} telemetry claim(s)",
    )

    safety = check(extraction, fetcher or IngestionMeshFetcher())
    EVENT_LOG.emit(
        note_id,
        "safety_checked",
        "Consistent with live telemetry" if safety.ok else f"{len(safety.warnings)} contradiction(s) flagged",
    )

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

    if inventory_updates:
        reorders = sum(1 for u in inventory_updates if u.reorder_triggered)
        EVENT_LOG.emit(
            note_id,
            "inventory_recorded",
            f"Recorded {len(inventory_updates)} part(s) against inventory, {reorders} reorder(s) triggered",
        )

    EVENT_LOG.emit(note_id, "complete", "Note processing complete")

    return NoteProcessingResult(extraction=extraction, safety=safety, inventory=inventory_updates)
