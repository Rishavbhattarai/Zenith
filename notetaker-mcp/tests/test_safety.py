from notetaker.safety import check
from notetaker.schema import FieldNoteExtraction, NoteType, TelemetryAnnotation


class FakeFetcher:
    def __init__(self, statuses: dict[str, str | None]):
        self._statuses = statuses

    def fetch_status(self, asset_id: str) -> str | None:
        return self._statuses.get(asset_id)


def _extraction(claimed_status: str, asset_id: str = "asset-0001") -> FieldNoteExtraction:
    return FieldNoteExtraction(
        note_type=NoteType.SITE_REPORT,
        summary="s",
        telemetry_annotations=[
            TelemetryAnnotation(asset_id=asset_id, claimed_status=claimed_status, notes="n")
        ],
    )


def test_no_contradiction_when_statuses_agree():
    result = check(_extraction("nominal"), FakeFetcher({"asset-0001": "nominal"}))
    assert result.ok
    assert result.warnings == []


def test_contradiction_flagged_when_statuses_disagree():
    result = check(_extraction("fixed"), FakeFetcher({"asset-0001": "critical"}))
    assert not result.ok
    assert "asset-0001" in result.warnings[0]
    assert "critical" in result.warnings[0]


def test_unknown_asset_flagged():
    result = check(_extraction("nominal"), FakeFetcher({}))
    assert not result.ok
    assert "no live telemetry" in result.warnings[0]


def test_unverifiable_phrasing_not_flagged():
    result = check(_extraction("kind of okay I guess"), FakeFetcher({"asset-0001": "critical"}))
    assert result.ok
    assert result.warnings == []
