"""ApproveFix use case (A1-2): approve a proposed fix (inbound ApprobationPort)."""

from hexagents_cloud.application.ports_closed import (
    ApprobationPort,
    AuditStorePort,
    FixProposalStorePort,
)
from hexagents_cloud.domain.actions.auto_fix import FixProposal
from hexagents_cloud.domain.actions.events import FixApproved


class ApproveFix:
    """Approve a FixProposal and append a FixApproved event to the audit."""

    def __init__(self, proposals: FixProposalStorePort, audit: AuditStorePort) -> None:
        self._proposals = proposals
        self._audit = audit

    def execute(self, fix_id: str, approver: str = "") -> FixProposal:
        proposal = self._proposals.load(fix_id)
        approved = proposal.approve(approver)
        self._proposals.save(approved)
        self._audit.append(FixApproved(fix_id=approved.fix_id.value, approver=approver))
        return approved

    def approve(self, fix_id: str, approver: str) -> FixProposal:
        return self.execute(fix_id, approver)


class ApprobationPortAdapter(ApprobationPort):
    """Wires the inbound ApprobationPort to the ApproveFix use case."""

    def __init__(self, use_case: ApproveFix) -> None:
        self._use_case = use_case

    def approve(self, fix_id: str, approver: str) -> FixProposal:
        return self._use_case.execute(fix_id, approver)
