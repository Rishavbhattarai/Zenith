import pytest
from pydantic import ValidationError

from notetaker.schema import FieldNoteExtraction, NoteType, PartUsed


def test_minimal_extraction_defaults():
    extraction = FieldNoteExtraction(note_type=NoteType.GENERAL, summary="ok")
    assert extraction.action_items == []
    assert extraction.parts_used == []
    assert extraction.telemetry_annotations == []


def test_part_used_requires_positive_quantity():
    with pytest.raises(ValidationError):
        PartUsed(part_name="fan", quantity=0)
