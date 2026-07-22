"""Agent Thought Log: an in-memory trace of processing stages, so the
Phase 4 dashboard can show what the notetaker and support agent are
actually doing, not just their final outputs."""

from __future__ import annotations

import threading
from collections import deque
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class AgentEvent(BaseModel):
    note_id: str
    stage: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventLog:
    def __init__(self, capacity: int = 200) -> None:
        self._events: deque[AgentEvent] = deque(maxlen=capacity)
        self._lock = threading.Lock()

    def emit(self, note_id: str, stage: str, message: str) -> None:
        with self._lock:
            self._events.append(AgentEvent(note_id=note_id, stage=stage, message=message))

    def recent(self, limit: int = 50) -> list[AgentEvent]:
        with self._lock:
            snapshot = list(self._events)
        return snapshot[-limit:][::-1]  # newest first


EVENT_LOG = EventLog()
