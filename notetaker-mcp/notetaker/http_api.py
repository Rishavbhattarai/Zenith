"""FastAPI transport for the field-app frontend (browsers can't speak MCP's
stdio protocol directly, so this thin wrapper exposes the same core logic
over HTTP)."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from notetaker.config import get_llm_client
from notetaker.core import process_field_note
from notetaker.events import EVENT_LOG, AgentEvent
from notetaker.schema import NoteProcessingResult
from notetaker.support_agent import SupportAnswer, ask_support_agent

app = FastAPI(title="Zenith Notetaker")

# Defaults to any localhost dev port (Next.js picks the first free one
# starting at 3000). In production, set ALLOWED_ORIGIN_REGEX to match your
# deployed frontend's origin(s), e.g. r"https://.*\.vercel\.app".
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=os.environ.get("ALLOWED_ORIGIN_REGEX", r"http://localhost:\d+"),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_llm = get_llm_client()


class NoteRequest(BaseModel):
    raw_text: str
    asset_id: str | None = None
    technician: str = "unspecified"


class SupportRequest(BaseModel):
    question: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/notes", response_model=NoteProcessingResult)
def create_note(req: NoteRequest) -> NoteProcessingResult:
    return process_field_note(req.raw_text, _llm, asset_id=req.asset_id, technician=req.technician)


@app.get("/events", response_model=list[AgentEvent])
def list_events(limit: int = 50) -> list[AgentEvent]:
    return EVENT_LOG.recent(limit=limit)


@app.post("/support/ask", response_model=SupportAnswer)
def support_ask(req: SupportRequest) -> SupportAnswer:
    return ask_support_agent(req.question)
