from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class StageThresholds:
    promote_mastery: float = 0.85
    promote_keywords: float = 0.70
    regress_mastery: float = 0.40
    streak: int = 3

    def __post_init__(self) -> None:
        for name, value in (
            ("promote_mastery", self.promote_mastery),
            ("promote_keywords", self.promote_keywords),
            ("regress_mastery", self.regress_mastery),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.streak < 1:
            raise ValueError("streak must be at least 1")


@dataclass(frozen=True)
class StageDecision:
    stage: int
    stage_changed: bool
    vocabulary_support: bool
    reason: str


def next_stage(
    concept_mastery: float,
    keyword_mastery: float,
    recent: Sequence[bool | int],
    current_stage: int,
    thresholds: StageThresholds = StageThresholds(),
) -> StageDecision:
    if not 0 <= concept_mastery <= 1 or not 0 <= keyword_mastery <= 1:
        raise ValueError("mastery values must be between 0 and 1")
    if not 0 <= current_stage <= 4:
        raise ValueError("current_stage must be between 0 and 4")
    if any(answer not in (0, 1, False, True) for answer in recent):
        raise ValueError("recent answers must contain only booleans or 0/1")

    vocabulary_support = (
        concept_mastery >= thresholds.promote_mastery
        and keyword_mastery < thresholds.promote_keywords
    )
    if vocabulary_support:
        return StageDecision(current_stage, False, True, "needs vocabulary support")

    streak = list(recent[-thresholds.streak :])
    if concept_mastery < thresholds.regress_mastery or (
        len(streak) == thresholds.streak and all(answer == 0 for answer in streak)
    ):
        stage = max(0, current_stage - 1)
        return StageDecision(stage, stage != current_stage, False, "regress")

    can_promote = (
        concept_mastery >= thresholds.promote_mastery
        and (current_stage == 0 or keyword_mastery >= thresholds.promote_keywords)
        and len(streak) == thresholds.streak
        and all(answer == 1 for answer in streak)
    )
    if can_promote:
        stage = min(4, current_stage + 1)
        return StageDecision(stage, stage != current_stage, False, "promote")

    return StageDecision(current_stage, False, False, "retain")