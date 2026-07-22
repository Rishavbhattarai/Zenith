"""Single source of truth for processing a field note, shared by both
transports (mcp_server.py, http_api.py)."""

from __future__ import annotations

from notetaker.llm.base import LLMClient
from notetaker.safety import IngestionMeshFetcher, TelemetryFetcher, check
from notetaker.schema import NoteProcessingResult


def process_field_note(
    raw_text: str,
    llm: LLMClient,
    asset_id: str | None = None,
    fetcher: TelemetryFetcher | None = None,
) -> NoteProcessingResult:
    extraction = llm.extract(raw_text, asset_id=asset_id)
    safety = check(extraction, fetcher or IngestionMeshFetcher())
    return NoteProcessingResult(extraction=extraction, safety=safety)
