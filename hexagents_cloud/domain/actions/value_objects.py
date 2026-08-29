"""Value objects for the ACTIONS bounded context (A1).

All value objects are immutable (frozen dataclasses) so they can be shared
and compared by value.
"""

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class FixId:
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class AssumptionId:
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Diff:
    description: str
    patch: list[str]

    def __post_init__(self) -> None:
        if not self.patch:
            raise ValueError("Diff.patch must not be empty")


class FixStatus(Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"


class Verdict(Enum):
    OK = "ok"
    REGRESSION = "regression"
