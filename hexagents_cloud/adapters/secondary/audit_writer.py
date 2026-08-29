"""AuditWriter adapter — in-memory AuditStorePort implementation.

Forwards every domain event to the public audit store once the harness exposes
it; until then it records events in memory (replayable without an LLM).
"""

from hexagents_cloud.application.ports_closed import AuditStorePort
from hexagents_cloud.domain.actions.events import DomainEvent


class AuditWriter(AuditStorePort):
    """Records domain events in memory (swap for the public AuditStorePort)."""

    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def append(self, event: DomainEvent) -> None:
        self.events.append(event)
