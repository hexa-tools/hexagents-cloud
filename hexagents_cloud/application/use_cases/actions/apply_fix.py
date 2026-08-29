"""ApplyFix use case (A1-3): apply an approved fix, verify, rollback on regression."""

from hexagents_cloud.application.ports_closed import AuditStorePort, FixProposalStorePort, K8sPort
from hexagents_cloud.domain.actions.auto_fix import FixProposal
from hexagents_cloud.domain.actions.events import FixFailed, FixRolledBack
from hexagents_cloud.domain.actions.value_objects import HealthStatus


class ApplyFix:
    """Apply an APPROVED fix, then verify cluster health and rollback on regression.

    A failure while applying is audited via ``FixFailed`` (the K8s adapter is
    responsible for its own bounded retries) and then re-raised so the caller
    sees a declared failure.
    """

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
        applied = proposal.applied()
        self._proposals.save(applied)

        try:
            self._k8s.apply(applied.diff)
        except Exception as exc:  # infra failure → audit a declared failure
            failed = FixFailed(fix_id=applied.fix_id.value, reason=str(exc))
            self._audit.append(failed)
            raise

        self._audit.append(applied.events[-1])

        if self._k8s.verify() == HealthStatus.HEALTHY:
            return applied

        rolled_back = applied.rollback()
        self._proposals.save(rolled_back)
        self._k8s.restore(proposal.diff)
        self._audit.append(FixRolledBack(fix_id=applied.fix_id.value))
        return rolled_back
