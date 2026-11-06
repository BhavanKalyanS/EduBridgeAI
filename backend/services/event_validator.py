from collections.abc import Mapping


def validate_answer_event(
    *,
    concept_exists: bool,
    submitted_stage: int,
    current_stage: int | None,
    event_exists: bool,
) -> tuple[bool, str | None]:
    if event_exists:
        return False, "duplicate_event_id"
    if not concept_exists:
        return False, "unknown_concept"
    if current_stage is None or submitted_stage != current_stage:
        return False, "stage_mismatch"
    return True, None


def validate_event_fields(payload: Mapping[str, object], required: set[str]) -> tuple[bool, str | None]:
    missing = required.difference(payload)
    if missing:
        return False, "missing_fields:" + ",".join(sorted(missing))
    return True, None