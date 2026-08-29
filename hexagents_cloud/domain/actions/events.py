"""Domain events for the ACTIONS bounded context (A1).

Events are emitted by the aggregate (via ``FixProposal.events``) and are the
source of truth for the audit store — replayable without any LLM.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DomainEvent:
    event_type: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_type", self.__class__.__name__)


@dataclass(frozen=True)
class FixProposed(DomainEvent):
    fix_id: str
    assumption_id: str
    diff: list[str]


@dataclass(frozen=True)
class FixApproved(DomainEvent):
    fix_id: str
    approver: str


@dataclass(frozen=True)
class FixApplied(DomainEvent):
    fix_id: str
    assumption_id: str


@dataclass(frozen=True)
class FixRolledBack(DomainEvent):
    fix_id: str


@dataclass(frozen=True)
class FixRejected(DomainEvent):
    fix_id: str
    reason: str


@dataclass(frozen=True)
class FixFailed(DomainEvent):
    fix_id: str
    reason: str
