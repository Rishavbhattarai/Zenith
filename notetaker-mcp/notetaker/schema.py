"""Structured data contract for the AI notetaker.

This is the shared shape produced by any LLMClient implementation
(notetaker.llm.*) and consumed by both transports (mcp_server, http_api).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class NoteType(str, Enum):
    SITE_REPORT = "site_report"
    FAILURE_POSTMORTEM = "failure_postmortem"
    GENERAL = "general"


class PartUsed(BaseModel):
    part_name: str
    quantity: int = Field(ge=1)


class TelemetryAnnotation(BaseModel):
    """A technician's claim about an asset's state, to be checked against
    live telemetry by notetaker.safety."""

    asset_id: str
    claimed_status: str = Field(description="e.g. 'nominal', 'degraded', 'critical', or free text")
    notes: str = ""


class FieldNoteExtraction(BaseModel):
    note_type: NoteType
    summary: str
    action_items: list[str] = Field(default_factory=list)
    parts_used: list[PartUsed] = Field(default_factory=list)
    telemetry_annotations: list[TelemetryAnnotation] = Field(default_factory=list)


class SafetyCheckResult(BaseModel):
    ok: bool
    warnings: list[str] = Field(default_factory=list)


class InventoryUpdate(BaseModel):
    """Outcome of recording one parts_used entry against the Phase 3
    inventory-service, from notetaker.inventory_client."""

    part_name: str
    matched: bool
    new_stock: int | None = None
    reorder_triggered: bool = False


class NoteProcessingResult(BaseModel):
    extraction: FieldNoteExtraction
    safety: SafetyCheckResult
    inventory: list[InventoryUpdate] = Field(default_factory=list)
