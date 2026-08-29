"""RollbackFix use case (A1-4): revert an applied fix and audit the rollback."""

from hexagents_cloud.application.ports_closed import AuditStorePort, FixProposalStorePort, K8sPort
from hexagents_cloud.domain.actions.auto_fix import FixProposal
from hexagents_cloud.domain.actions.events import FixRolledBack


class RollbackFix:
    """Rollback an APPLIED fix, restoring the previous diff and auditing it."""

    def __init__(
        self,
        proposals: FixProposalStorePort,
        audit: AuditStorePort,
        k8s: K8sPort,
    ) -> None:
        self._proposals = proposals
        self._audit = audit
        self._k8s = k8s

    def execute(self, fix_id: str) -> FixProposal:
        proposal = self._proposals.load(fix_id)
        rolled_back = proposal.rollback()
        self._proposals.save(rolled_back)
        self._k8s.restore(proposal.diff)
        self._audit.append(FixRolledBack(fix_id=proposal.fix_id.value))
        return rolled_back
