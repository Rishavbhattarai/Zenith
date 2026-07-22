from notetaker.core import process_field_note
from notetaker.llm.mock import MockClient


class FakeFetcher:
    def __init__(self, statuses: dict[str, str | None]):
        self._statuses = statuses

    def fetch_status(self, asset_id: str) -> str | None:
        return self._statuses.get(asset_id)


def test_process_field_note_end_to_end_with_mock():
    raw_text = "Replaced the power supply on asset-0042, running fine now."
    result = process_field_note(
        raw_text,
        MockClient(),
        fetcher=FakeFetcher({"asset-0042": "nominal"}),
    )

    assert result.extraction.telemetry_annotations[0].asset_id == "asset-0042"
    assert any("power supply" in p.part_name for p in result.extraction.parts_used)
    assert result.safety.ok


def test_process_field_note_flags_contradiction_with_mock():
    raw_text = "Replaced the fan on asset-0099, running fine now."
    result = process_field_note(
        raw_text,
        MockClient(),
        fetcher=FakeFetcher({"asset-0099": "critical"}),
    )

    assert not result.safety.ok
    assert "asset-0099" in result.safety.warnings[0]


def test_process_field_note_uses_context_asset_id_when_note_has_none():
    raw_text = "Fixed it, seems nominal now."
    result = process_field_note(
        raw_text,
        MockClient(),
        asset_id="asset-0007",
        fetcher=FakeFetcher({"asset-0007": "nominal"}),
    )

    assert result.extraction.telemetry_annotations[0].asset_id == "asset-0007"
    assert result.safety.ok
