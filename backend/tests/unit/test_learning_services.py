import pytest

from backend.services.bkt import BKTParameters, update_mastery
from backend.services.stage_controller import StageThresholds, next_stage


def test_bkt_uses_configurable_defaults_and_stays_bounded() -> None:
    parameters = BKTParameters()

    assert parameters.initial_mastery == 0.30
    assert update_mastery(0.30, True, parameters) == pytest.approx(0.6926829268)
    assert 0 <= update_mastery(0.30, False, parameters) <= 1


def test_bkt_rejects_invalid_probability() -> None:
    with pytest.raises(ValueError):
        update_mastery(1.1, True)


def test_stage_promotes_one_stage_after_mastery_and_correct_streak() -> None:
    decision = next_stage(0.90, 0.75, [1, 1, 1], 0)

    assert decision.stage == 1
    assert decision.stage_changed
    assert decision.reason == "promote"


def test_stage_requires_keyword_mastery_after_stage_zero() -> None:
    decision = next_stage(0.90, 0.60, [1, 1, 1], 2)

    assert decision.stage == 2
    assert decision.vocabulary_support
    assert decision.reason == "needs vocabulary support"


def test_high_concept_mastery_and_low_keyword_mastery_flags_support_without_regression() -> None:
    decision = next_stage(0.90, 0.50, [0, 0, 0], 2)

    assert decision.stage == 2
    assert decision.vocabulary_support
    assert decision.reason == "needs vocabulary support"


def test_stage_regresses_for_low_mastery_or_incorrect_streak() -> None:
    assert next_stage(0.39, 0.90, [1, 1, 1], 2).stage == 1
    assert next_stage(0.60, 0.80, [0, 0, 0], 2).stage == 1


def test_stage_stays_within_zero_to_four() -> None:
    assert next_stage(0.10, 0.10, [], 0).stage == 0
    assert next_stage(0.99, 0.99, [1, 1, 1], 4).stage == 4


def test_thresholds_are_validated() -> None:
    with pytest.raises(ValueError):
        StageThresholds(promote_mastery=1.2)


def test_simulated_learner_reaches_stage_two_in_twelve_answers() -> None:
    concept_mastery = 0.30
    keyword_mastery = 0.30
    stage = 0
    recent = []
    reached_stages = [stage]
    parameters = BKTParameters()
    thresholds = StageThresholds()

    for index in range(12):
        if index % 2 == 0:
            concept_mastery = update_mastery(concept_mastery, True, parameters)
        else:
            keyword_mastery = update_mastery(keyword_mastery, True, parameters)
        recent = (recent + [1])[-5:]
        stage = next_stage(concept_mastery, keyword_mastery, recent, stage, thresholds).stage
        reached_stages.append(stage)

    assert 2 in reached_stages