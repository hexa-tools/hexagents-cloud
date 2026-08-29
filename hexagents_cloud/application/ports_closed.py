"""Closed (inbound + outbound) ports for the hexagents-cloud action layer.

The application core depends only on these abstractions. Adapters implement
them; the core never imports a concrete adapter.

Inbound
    ApprobationPort — external trigger for approving a proposal (mobile, ticket 08).

Outbound
    FixProposalStorePort — load/save a FixProposal aggregate.
    K8sPort           — apply/verify/restore a manifest diff.
    AuditStorePort    — append a domain event (public, replayable without LLM).
    NotificationPort  — push a notification to the approver.
"""

from abc import ABC, abstractmethod

from hexagents_cloud.domain.actions.auto_fix import FixProposal
from hexagents_cloud.domain.actions.events import DomainEvent
from hexagents_cloud.domain.actions.value_objects import Diff, HealthStatus

# ─────────────────────────────────────────────
# Inbound ports
# ─────────────────────────────────────────────


class ApprobationPort(ABC):
    """Contract for approving a proposed fix (inbound, driven by mobile)."""

    @abstractmethod
    def approve(self, fix_id: str, approver: str) -> FixProposal:
        """Approve the fix ``fix_id`` on behalf of ``approver``."""


# ─────────────────────────────────────────────
# Outbound ports
# ─────────────────────────────────────────────


class FixProposalStorePort(ABC):
    """Persistence port for the FixProposal aggregate."""

    @abstractmethod
    def load(self, fix_id: str) -> FixProposal:
        """Return the proposal for ``fix_id`` or raise ``FixNotFound``."""

    @abstractmethod
    def save(self, proposal: FixProposal) -> None:
        """Persist ``proposal``."""


class K8sPort(ABC):
    """Kubernetes application port used to apply/verify/restore a diff."""

    @abstractmethod
    def apply(self, diff: Diff) -> None:
        """Apply ``diff`` to the cluster."""

    @abstractmethod
    def verify(self) -> HealthStatus:
        """Check cluster health after an apply."""

    @abstractmethod
    def restore(self, previous: Diff) -> None:
        """Rollback to ``previous`` diff."""


class AuditStorePort(ABC):
    """Event-sourced audit append port (public harness, replayable)."""

    @abstractmethod
    def append(self, event: DomainEvent) -> None:
        """Append ``event`` to the audit store."""


class NotificationPort(ABC):
    """Notification push port for approval requests (ticket 08)."""

    @abstractmethod
    def notify(self, message: str) -> None:
        """Send a push notification to the approver."""
