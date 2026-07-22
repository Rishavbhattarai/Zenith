from notetaker.events import EventLog


def test_emit_and_recent_returns_newest_first():
    log = EventLog()
    log.emit("note-1", "received", "first")
    log.emit("note-1", "extracted", "second")

    events = log.recent()

    assert [e.message for e in events] == ["second", "first"]
    assert all(e.note_id == "note-1" for e in events)


def test_recent_respects_limit():
    log = EventLog()
    for i in range(5):
        log.emit("note-1", "stage", f"msg-{i}")

    events = log.recent(limit=2)

    assert [e.message for e in events] == ["msg-4", "msg-3"]


def test_capacity_trims_oldest_events():
    log = EventLog(capacity=3)
    for i in range(5):
        log.emit("note-1", "stage", f"msg-{i}")

    events = log.recent(limit=10)

    assert [e.message for e in events] == ["msg-4", "msg-3", "msg-2"]
