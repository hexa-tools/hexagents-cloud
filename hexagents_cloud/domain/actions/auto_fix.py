"""FixProposal aggregate — the ACTIONS (A1) bounded context.

The aggregate carries the business invariants:
  * a proposal always references an assumption (never orphaned);
  * no apply without an explicit approval (``FixNotApproved``);
  * transitions are only legal from a specific state (``InvalidFixTransition``).

It is immutable: each transition returns a new ``FixProposal``. Events are
accumulated on the instance and consumed by the use case, which forwards them
to the AuditStorePort. The domain never depends on any port or adapter.
"""

from dataclasses import dataclass, replace

from hexagents_cloud.domain.actions.events import (
    DomainEvent,
    FixApplied,
    FixApproved,
    FixProposed,
    FixRejected,
    FixRolledBack,
)
from hexagents_cloud.domain.actions.value_objects import (
    AssumptionId,
    Diff,
    FixId,
    FixStatus,
)
from hexagents_cloud.domain.errors import FixNotApproved, InvalidFixTransition


@dataclass(frozen=True)
class FixProposal:
    fix_id: FixId
    assumption_id: AssumptionId
    diff: Diff
    status: FixStatus = FixStatus.PROPOSED
    events: tuple[DomainEvent, ...] = ()

    def __post_init__(self) -> None:
        if not self.events:
            object.__setattr__(
                self,
                "events",
                (FixProposed(self.fix_id.value, self.assumption_id.value, self.diff.patch),),
            )

    def _with(self, status: FixStatus, event: DomainEvent) -> "FixProposal":
        return replace(self, status=status, events=(*self.events, event))

    def approve(self, approver: str = "") -> "FixProposal":
        if self.status != FixStatus.PROPOSED:
            raise InvalidFixTransition(self.status.value)
        return self._with(FixStatus.APPROVED, FixApproved(self.fix_id.value, approver))

    def applied(self) -> "FixProposal":
        if self.status == FixStatus.PROPOSED:
            raise FixNotApproved(self.fix_id.value)
        if self.status != FixStatus.APPROVED:
            raise InvalidFixTransition(self.status.value)
        return self._with(
            FixStatus.APPLIED,
            FixApplied(self.fix_id.value, self.assumption_id.value),
        )

    def rollback(self) -> "FixProposal":
        if self.status != FixStatus.APPLIED:
            raise InvalidFixTransition(self.status.value)
        return self._with(FixStatus.ROLLED_BACK, FixRolledBack(self.fix_id.value))

    def reject(self, reason: str) -> "FixProposal":
        if self.status != FixStatus.PROPOSED:
            raise InvalidFixTransition(self.status.value)
        return self._with(FixStatus.REJECTED, FixRejected(self.fix_id.value, reason))
