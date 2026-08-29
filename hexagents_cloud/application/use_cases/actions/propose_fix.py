"""ProposeFix use case (A1-1): scan -> proposal + FixProposed + notification."""

from hexagents_cloud.application.ports_closed import (
    AuditStorePort,
    FixProposalStorePort,
    NotificationPort,
)
from hexagents_cloud.domain.actions.auto_fix import FixProposal
from hexagents_cloud.domain.actions.value_objects import AssumptionId, Diff, FixId


class ProposeFix:
    """Create a FixProposal, persist it, emit FixProposed and notify the approver."""

    def __init__(
        self,
        proposals: FixProposalStorePort,
        audit: AuditStorePort,
        notifier: NotificationPort,
    ) -> None:
        self._proposals = proposals
        self._audit = audit
        self._notifier = notifier

    def execute(self, fix_id: str, assumption_id: str, diff: Diff) -> FixProposal:
        proposal = FixProposal(
            fix_id=FixId(fix_id),
            assumption_id=AssumptionId(assumption_id),
            diff=diff,
        )
        self._proposals.save(proposal)
        for event in proposal.events:
            self._audit.append(event)
        self._notifier.notify(f"Approval required for fix {fix_id}")
        return proposal
