"""Gemini-backed LLMClient: extracts structured field-note data using
Gemini's JSON structured-output mode against the FieldNoteExtraction schema.
"""

from __future__ import annotations

from google import genai
from google.genai import types

from notetaker.schema import FieldNoteExtraction

DEFAULT_MODEL = "gemini-2.0-flash"

SYSTEM_INSTRUCTION = """You are a field-service notetaker for critical infrastructure \
(data centers, satellite ground stations, retail networks). You read raw, informal \
notes dictated or typed by field technicians and extract a structured record.

Rules:
- action_items: concrete follow-up tasks implied by the note (empty list if none).
- parts_used: any physical components the technician says they installed, replaced, \
or consumed, with quantity (default 1 if unstated).
- telemetry_annotations: whenever the technician makes a claim about an asset's \
operating state (e.g. "it's fine now", "still throwing errors", "replaced the PSU, \
seems nominal"), extract one entry per asset_id mentioned with your best reading of \
their claimed_status ('nominal', 'degraded', or 'critical' where the note supports \
one of those; otherwise short free text) and a one-line notes field. If the tech \
doesn't reference an asset by ID and none is given as context, do not guess one.
- note_type: 'failure_postmortem' if the note centers on diagnosing/explaining a \
failure, 'site_report' for routine visit/status notes, else 'general'.
- summary: one or two sentences capturing the note's substance.
"""


class GeminiClient:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def extract(self, raw_text: str, asset_id: str | None = None) -> FieldNoteExtraction:
        contents = raw_text
        if asset_id:
            contents = (
                f"The technician is physically working on {asset_id}. Use this as the "
                f"asset_id for any telemetry_annotations unless the note clearly refers "
                f"to a different asset.\n\nNote:\n{raw_text}"
            )
        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=FieldNoteExtraction,
            ),
        )
        return FieldNoteExtraction.model_validate_json(response.text)
