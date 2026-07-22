"""LLMClient interface — any backend (Gemini, mock, later Claude/Ollama) that
can turn raw field-note text into a FieldNoteExtraction implements this."""

from __future__ import annotations

from typing import Protocol

from notetaker.schema import FieldNoteExtraction


class LLMClient(Protocol):
    def extract(self, raw_text: str, asset_id: str | None = None) -> FieldNoteExtraction:
        """Extract structured data from a raw field note. `asset_id`, when
        given, is the asset the technician was physically working on (e.g.
        selected in the field app) and should be used for telemetry
        annotations when the note doesn't explicitly name a different
        asset."""
        ...
