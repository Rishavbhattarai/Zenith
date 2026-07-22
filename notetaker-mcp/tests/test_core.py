from notetaker.core import process_field_note
from notetaker.llm.mock import MockClient
from notetaker.schema import InventoryUpdate


class FakeFetcher:
    def __init__(self, statuses: dict[str, str | None]):
        self._statuses = statuses

    def fetch_status(self, asset_id: str) -> str | None:
        return self._statuses.get(asset_id)


class FakeInventoryClient:
    def __init__(self, responses: dict[str, InventoryUpdate] | None = None):
        self._responses = responses or {}
        self.calls: list[tuple[str, str, int, str]] = []

    def record(self, asset_id: str, part_name: str, quantity: int, technician: str) -> InventoryUpdate:
        self.calls.append((asset_id, part_name, quantity, technician))
        return self._responses.get(
            part_name, InventoryUpdate(part_name=part_name, matched=True, new_stock=1)
        )


def test_process_field_note_end_to_end_with_mock():
    raw_text = "Replaced the power supply on asset-0042, running fine now."
    result = process_field_note(
        raw_text,
        MockClient(),
        fetcher=FakeFetcher({"asset-0042": "nominal"}),
        inventory=FakeInventoryClient(),
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
        inventory=FakeInventoryClient(),
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
        inventory=FakeInventoryClient(),
    )

    assert result.extraction.telemetry_annotations[0].asset_id == "asset-0007"
    assert result.safety.ok


def test_process_field_note_records_parts_used_against_inventory():
    raw_text = "Replaced the power supply on asset-0042, running fine now."
    fake_inventory = FakeInventoryClient(
        {"power supply": InventoryUpdate(part_name="power supply", matched=True, new_stock=2, reorder_triggered=True)}
    )

    result = process_field_note(
        raw_text,
        MockClient(),
        technician="tech-bob",
        fetcher=FakeFetcher({"asset-0042": "nominal"}),
        inventory=fake_inventory,
    )

    assert fake_inventory.calls == [("asset-0042", "power supply", 1, "tech-bob")]
    assert result.inventory == [
        InventoryUpdate(part_name="power supply", matched=True, new_stock=2, reorder_triggered=True)
    ]


def test_process_field_note_skips_inventory_when_no_asset_context():
    raw_text = "Replaced the fan, running fine now."
    fake_inventory = FakeInventoryClient()

    result = process_field_note(
        raw_text,
        MockClient(),
        fetcher=FakeFetcher({}),
        inventory=fake_inventory,
    )

    assert fake_inventory.calls == []
    assert result.inventory == []
