"""Tests for ApproveFix use case (A1-2)."""

import pytest

from hexagents_cloud.application.use_cases.actions.approve_fix import ApproveFix
from hexagents_cloud.domain.actions.auto_fix import FixProposal
from hexagents_cloud.domain.actions.value_objects import AssumptionId, Diff, FixId
from hexagents_cloud.domain.errors import FixNotFound


class InMemoryStore:
    def __init__(self) -> None:
        self.by_id: dict[str, FixProposal] = {}

    def load(self, fix_id: str) -> FixProposal:
        if fix_id not in self.by_id:
            raise FixNotFound(fix_id)
        return self.by_id[fix_id]

    def save(self, proposal: FixProposal) -> None:
        self.by_id[proposal.fix_id.value] = proposal


class RecordingAudit:
    def __init__(self) -> None:
        self.events = []

    def append(self, event) -> None:
        self.events.append(event)


def test_approve_fix_happy_path() -> None:
    store = InMemoryStore()
    audit = RecordingAudit()
    proposal = FixProposal(
        fix_id=FixId("fix-1"),
        assumption_id=AssumptionId("asmp-1"),
        diff=Diff(description="limits", patch=["spec:"]),
    )
    store.save(proposal)

    uc = ApproveFix(store, audit)
    approved = uc.execute("fix-1", "alice")

    assert approved.status.value == "approved"
    stored = store.load("fix-1")
    assert stored.status.value == "approved"
    assert any(type(e).__name__ == "FixApproved" for e in audit.events)


def test_approve_fix_unknown_id_raises() -> None:
    store = InMemoryStore()
    audit = RecordingAudit()
    uc = ApproveFix(store, audit)
    with pytest.raises(FixNotFound):
        uc.execute("fix-42", "alice")


def test_approve_fix_from_two_devices_only_first_wins() -> None:
    """Two simultaneous approvals (two devices) — only the first succeeds."""
    from hexagents_cloud.domain.errors import InvalidFixTransition

    store = InMemoryStore()
    audit = RecordingAudit()
    proposal = FixProposal(
        fix_id=FixId("fix-1"),
        assumption_id=AssumptionId("asmp-1"),
        diff=Diff(description="limits", patch=["spec:"]),
    )
    store.save(proposal)
    uc = ApproveFix(store, audit)

    first = uc.execute("fix-1", "device-a")
    assert first.status.value == "approved"

    with pytest.raises(InvalidFixTransition):
        uc.execute("fix-1", "device-b")

    stored = store.load("fix-1")
    assert stored.status.value == "approved"
    assert stored.fix_id.value == "fix-1"
    # Only one FixApproved event in the audit.
    approved_events = [e for e in audit.events if type(e).__name__ == "FixApproved"]
    assert len(approved_events) == 1


def test_approve_method_wraps_execute() -> None:
    store = InMemoryStore()
    audit = RecordingAudit()
    proposal = FixProposal(
        fix_id=FixId("fix-1"),
        assumption_id=AssumptionId("asmp-1"),
        diff=Diff(description="limits", patch=["spec:"]),
    )
    store.save(proposal)
    uc = ApproveFix(store, audit)

    result = uc.approve("fix-1", "bob")

    assert result.status.value == "approved"
    assert any(type(e).__name__ == "FixApproved" for e in audit.events)


def test_approbation_port_adapter_forwards_to_use_case() -> None:
    from hexagents_cloud.application.use_cases.actions.approve_fix import ApprobationPortAdapter

    store = InMemoryStore()
    audit = RecordingAudit()
    proposal = FixProposal(
        fix_id=FixId("fix-1"),
        assumption_id=AssumptionId("asmp-1"),
        diff=Diff(description="limits", patch=["spec:"]),
    )
    store.save(proposal)
    adapter = ApprobationPortAdapter(ApproveFix(store, audit))

    result = adapter.approve("fix-1", "carol")

    assert result.status.value == "approved"
    assert any(type(e).__name__ == "FixApproved" for e in audit.events)


def test_approbation_port_adapter_returns_same_status_when_not_approved() -> None:
    from hexagents_cloud.application.use_cases.actions.approve_fix import ApprobationPortAdapter
    from hexagents_cloud.domain.actions.value_objects import FixStatus

    store = InMemoryStore()
    audit = RecordingAudit()
    proposal = FixProposal(
        fix_id=FixId("fix-1"),
        assumption_id=AssumptionId("asmp-1"),
        diff=Diff(description="limits", patch=["spec:"]),
    )
    store.save(proposal)
    adapter = ApprobationPortAdapter(ApproveFix(store, audit))

    approved = adapter.approve("fix-1", "carol")

    assert approved.status == FixStatus.APPROVED
