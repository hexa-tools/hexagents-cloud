"""In-memory fake adapters for the closed ports (SANDBOX_MODE / tests).

These are deterministic stand-ins. They live only in adapters/secondary/fakes/
and are never hardcoded into a use case — the use case receives a port.
"""

from hexagents_cloud.application.ports_closed import (
    AuditStorePort,
    FixProposalStorePort,
    K8sPort,
    NotificationPort,
)
from hexagents_cloud.domain.actions.auto_fix import FixProposal
from hexagents_cloud.domain.actions.events import DomainEvent
from hexagents_cloud.domain.actions.value_objects import Diff, HealthStatus
from hexagents_cloud.domain.errors import FixNotFound


class InMemoryFixProposalStore(FixProposalStorePort):
    """Stores FixProposal aggregates in a dict keyed by fix id."""

    def __init__(self) -> None:
        self.by_id: dict[str, FixProposal] = {}

    def load(self, fix_id: str) -> FixProposal:
        if fix_id not in self.by_id:
            raise FixNotFound(fix_id)
        return self.by_id[fix_id]

    def save(self, proposal: FixProposal) -> None:
        self.by_id[proposal.fix_id.value] = proposal


class InMemoryK8s(K8sPort):
    """Applies/restores diffs in memory with a configurable health status."""

    def __init__(self, health: HealthStatus = HealthStatus.HEALTHY) -> None:
        self.health = health
        self.applied: list[Diff] = []
        self.restored: list[Diff] = []

    def apply(self, diff: Diff) -> None:
        self.applied.append(diff)

    def verify(self) -> HealthStatus:
        return self.health

    def restore(self, previous: Diff) -> None:
        self.restored.append(previous)


class InMemoryAuditStore(AuditStorePort):
    """Records domain events in memory."""

    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def append(self, event: DomainEvent) -> None:
        self.events.append(event)


class InMemoryNotification(NotificationPort):
    """Records notification messages in memory."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def notify(self, message: str) -> None:
        self.messages.append(message)
