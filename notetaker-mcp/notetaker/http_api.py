"""FastAPI transport for the field-app frontend (browsers can't speak MCP's
stdio protocol directly, so this thin wrapper exposes the same core logic
over HTTP)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from notetaker.config import get_llm_client
from notetaker.core import process_field_note
from notetaker.schema import NoteProcessingResult

app = FastAPI(title="Zenith Notetaker")

app.add_middleware(
    CORSMiddleware,
    # Next.js dev picks the first free port starting at 3000, so don't
    # hardcode one — match any localhost dev origin.
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["POST"],
    allow_headers=["*"],
)

_llm = get_llm_client()


class NoteRequest(BaseModel):
    raw_text: str
    asset_id: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/notes", response_model=NoteProcessingResult)
def create_note(req: NoteRequest) -> NoteProcessingResult:
    return process_field_note(req.raw_text, _llm, asset_id=req.asset_id)
