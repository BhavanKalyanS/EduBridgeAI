from dataclasses import dataclass


@dataclass(frozen=True)
class BKTParameters:
    initial_mastery: float = 0.30
    learning_rate: float = 0.10
    guess: float = 0.20
    slip: float = 0.10

    def __post_init__(self) -> None:
        for name, value in (
            ("initial_mastery", self.initial_mastery),
            ("learning_rate", self.learning_rate),
            ("guess", self.guess),
            ("slip", self.slip),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")


def update_mastery(
    mastery: float,
    correct: bool,
    parameters: BKTParameters = BKTParameters(),
) -> float:
    if not 0 <= mastery <= 1:
        raise ValueError("mastery must be between 0 and 1")

    if correct:
        known = mastery * (1 - parameters.slip)
        denominator = known + (1 - mastery) * parameters.guess
    else:
        known = mastery * parameters.slip
        denominator = known + (1 - mastery) * (1 - parameters.guess)

    posterior = known / denominator if denominator else mastery
    return posterior + (1 - posterior) * parameters.learning_rate