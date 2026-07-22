"""Deterministic LLMClient used in tests and as a no-key fallback. Does
simple keyword extraction rather than real NLU — good enough to exercise
the rest of the pipeline (safety checks, transports) without network calls.
"""

from __future__ import annotations

import re

from notetaker.schema import (
    FieldNoteExtraction,
    NoteType,
    PartUsed,
    TelemetryAnnotation,
)

_ASSET_RE = re.compile(r"\basset-\d+\b", re.IGNORECASE)
_STATUS_WORDS = {
    "nominal": ["fixed", "nominal", "resolved", "back up", "running fine", "good now"],
    "critical": ["still down", "critical", "failed", "not working", "still broken"],
    "degraded": ["degraded", "intermittent", "partially"],
}


class MockClient:
    def extract(self, raw_text: str, asset_id: str | None = None) -> FieldNoteExtraction:
        lower = raw_text.lower()

        note_type = NoteType.GENERAL
        if any(w in lower for w in ["fail", "postmortem", "root cause", "outage"]):
            note_type = NoteType.FAILURE_POSTMORTEM
        elif any(w in lower for w in ["site visit", "inspection", "routine"]):
            note_type = NoteType.SITE_REPORT

        asset_ids = sorted(set(m.group(0).lower() for m in _ASSET_RE.finditer(raw_text)))
        if not asset_ids and asset_id:
            asset_ids = [asset_id.lower()]

        claimed_status = "unspecified"
        for status, words in _STATUS_WORDS.items():
            if any(w in lower for w in words):
                claimed_status = status
                break

        telemetry_annotations = [
            TelemetryAnnotation(asset_id=aid, claimed_status=claimed_status, notes=raw_text[:120])
            for aid in asset_ids
        ]

        parts_used = []
        for match in re.finditer(r"replaced (?:the )?([a-zA-Z ]+?)(?:\.|,| on| for|$)", lower):
            part = match.group(1).strip()
            if part:
                parts_used.append(PartUsed(part_name=part, quantity=1))

        action_items = []
        if "need to" in lower or "follow up" in lower or "should" in lower:
            action_items.append("Follow up per technician note")

        return FieldNoteExtraction(
            note_type=note_type,
            summary=raw_text.strip()[:200],
            action_items=action_items,
            parts_used=parts_used,
            telemetry_annotations=telemetry_annotations,
        )
