"""Primary adapter registry — wires the private action layer to the harness.

Each ``build_*_adapter`` factory returns a port. By default they use the
in-memory fakes (SANDBOX_MODE); real adapters can be injected in production.

``register()`` builds the A1 use cases (wired to the adapters) and registers
``cloud.actions`` into the public harness extension point when available;
otherwise it degrades gracefully (the private layer still runs standalone
against the fakes).
"""

from hexagents_cloud.adapters.secondary.approval_notifier import ApprovalNotifier
from hexagents_cloud.adapters.secondary.audit_writer import AuditWriter
from hexagents_cloud.adapters.secondary.fakes.fakes import InMemoryFixProposalStore
from hexagents_cloud.adapters.secondary.k8s_fix_applier import K8sFixApplier
from hexagents_cloud.application.ports_closed import (
    ApprobationPort,
    AuditStorePort,
    FixProposalStorePort,
    K8sPort,
    NotificationPort,
)
from hexagents_cloud.application.use_cases.actions.apply_fix import ApplyFix
from hexagents_cloud.application.use_cases.actions.approve_fix import (
    ApprobationPortAdapter,
    ApproveFix,
)
from hexagents_cloud.application.use_cases.actions.propose_fix import ProposeFix
from hexagents_cloud.application.use_cases.actions.rollback_fix import RollbackFix


def build_k8s_adapter() -> K8sPort:
    """Return the K8s outbound adapter (in-memory by default)."""
    return K8sFixApplier()


def build_audit_adapter() -> AuditStorePort:
    """Return the audit outbound adapter (in-memory by default)."""
    return AuditWriter()


def build_notification_adapter() -> NotificationPort:
    """Return the notification outbound adapter (in-memory by default)."""
    return ApprovalNotifier()


def build_proposal_store_adapter() -> FixProposalStorePort:
    """Return the proposal store outbound adapter (in-memory by default)."""
    return InMemoryFixProposalStore()


def build_approbation_adapter() -> ApprobationPort:
    """Return the inbound ApprobationPort wired to the ApproveFix use case."""
    approver = ApproveFix(build_proposal_store_adapter(), build_audit_adapter())
    return ApprobationPortAdapter(approver)


def register() -> dict[str, object]:
    """Build the A1 use cases, wire them to adapters, register cloud.actions.

    Returns the map of registered pack name -> use case object.
    """
    store = build_proposal_store_adapter()
    audit = build_audit_adapter()
    k8s = build_k8s_adapter()
    notifier = build_notification_adapter()

    propose = ProposeFix(store, audit, notifier)
    approver = ApproveFix(store, audit)
    apply = ApplyFix(store, audit, k8s)
    rollback = RollbackFix(store, audit, k8s)

    packs: dict[str, object] = {
        "cloud.actions.propose": propose,
        "cloud.actions.approve": approver,
        "cloud.actions.apply": apply,
        "cloud.actions.rollback": rollback,
    }
    try:
        # The public harness does not expose the extensions.PackRegistry point
        # yet; imported lazily so the private layer still runs standalone
        # against the fakes (circular/optional import escape hatch).
        from hexagents.extensions import PackRegistry  # noqa: hexa-lazy-import

        PackRegistry.register("cloud.actions", approver)
    except ImportError:
        pass
    return packs
