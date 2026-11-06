from backend.services.event_validator import validate_answer_event, validate_event_fields


def test_rejects_duplicate_event_before_processing():
    valid, reason = validate_answer_event(
        concept_exists=True,
        submitted_stage=1,
        current_stage=1,
        event_exists=True,
    )

    assert not valid
    assert reason == "duplicate_event_id"


def test_rejects_unknown_concept_and_stage_mismatch():
    assert validate_answer_event(concept_exists=False, submitted_stage=0, current_stage=0, event_exists=False) == (False, "unknown_concept")
    assert validate_answer_event(concept_exists=True, submitted_stage=2, current_stage=1, event_exists=False) == (False, "stage_mismatch")


def test_accepts_valid_event_and_reports_missing_fields():
    assert validate_answer_event(concept_exists=True, submitted_stage=2, current_stage=2, event_exists=False) == (True, None)
    assert validate_event_fields({"event_id": "e1"}, {"event_id", "concept_id"}) == (False, "missing_fields:concept_id")