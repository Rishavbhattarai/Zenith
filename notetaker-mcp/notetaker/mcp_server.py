"""Real MCP server (stdio transport) exposing the field-note processing
pipeline as a tool, usable by any MCP client (Claude Code/Desktop, or later
the Phase 4 dashboard)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from notetaker.config import get_llm_client
from notetaker.core import process_field_note
from notetaker.schema import NoteProcessingResult
from notetaker.support_agent import SupportAnswer, ask_support_agent

mcp = FastMCP("zenith-notetaker")
_llm = get_llm_client()


@mcp.tool()
def process_field_note_tool(
    raw_text: str, asset_id: str | None = None, technician: str = "unspecified"
) -> NoteProcessingResult:
    """Extract structured data (action items, parts used, telemetry claims)
    from a field technician's raw note, flag any contradictions between the
    technician's claims and the asset's live telemetry, and record any
    parts used against the inventory system.

    Args:
        raw_text: The raw field note, as typed or transcribed from voice.
        asset_id: The asset the technician was physically working on, if known.
        technician: Identifier for the technician filing the note.
    """
    return process_field_note(raw_text, _llm, asset_id=asset_id, technician=technician)


@mcp.tool()
def ask_support_agent_tool(question: str) -> SupportAnswer:
    """Answer an operations question grounded in Zenith's internal runbooks
    (power supply failures, network degradation, escalation policy,
    inventory reorder policy). Cites which doc(s) the answer came from.

    Args:
        question: The operator's question.
    """
    return ask_support_agent(question)


if __name__ == "__main__":
    mcp.run()
