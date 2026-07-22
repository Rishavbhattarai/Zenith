"""2.3: Intent/safety evaluator. Checks a technician's claimed asset status
against the live telemetry from Phase 1's ingestion mesh, flagging
contradictions before they're trusted as fact — the "closed-loop autonomy"
verification step from the handoff doc's vision.
"""

from __future__ import annotations

from typing import Protocol

import httpx

from notetaker.schema import FieldNoteExtraction, SafetyCheckResult

# Claimed-status words that should agree with the live telemetry status.
# Anything not in this map is left unverified (no contradiction raised) —
# we only flag a mismatch when we're confident the tech's word choice maps
# cleanly onto a telemetry status.
_STATUS_ALIASES = {
    "nominal": "nominal",
    "fixed": "nominal",
    "resolved": "nominal",
    "degraded": "degraded",
    "critical": "critical",
    "failed": "critical",
}


class TelemetryFetcher(Protocol):
    def fetch_status(self, asset_id: str) -> str | None:
        """Return the asset's live status, or None if the asset is unknown."""
        ...


class IngestionMeshFetcher:
    """Fetches live asset state from the Phase 1 Go ingestion mesh."""

    def __init__(self, base_url: str = "http://localhost:8080", timeout: float = 3.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def fetch_status(self, asset_id: str) -> str | None:
        try:
            resp = httpx.get(f"{self._base_url}/assets/{asset_id}", timeout=self._timeout)
        except httpx.HTTPError:
            return None
        if resp.status_code != 200:
            return None
        return resp.json().get("latest", {}).get("status")


def check(extraction: FieldNoteExtraction, fetcher: TelemetryFetcher) -> SafetyCheckResult:
    warnings: list[str] = []

    for annotation in extraction.telemetry_annotations:
        claimed = _STATUS_ALIASES.get(annotation.claimed_status.lower())
        if claimed is None:
            continue  # unverifiable phrasing; not a contradiction

        live_status = fetcher.fetch_status(annotation.asset_id)
        if live_status is None:
            warnings.append(
                f"{annotation.asset_id}: technician claimed '{annotation.claimed_status}' "
                "but this asset has no live telemetry to verify against."
            )
            continue

        if live_status != claimed:
            warnings.append(
                f"{annotation.asset_id}: technician claimed '{annotation.claimed_status}' "
                f"but live telemetry currently reports '{live_status}'."
            )

    return SafetyCheckResult(ok=not warnings, warnings=warnings)
