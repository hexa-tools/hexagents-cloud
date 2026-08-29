"""Tests for ApplyFix use case (A1-3)."""

import pytest

from hexagents_cloud.application.use_cases.actions.apply_fix import ApplyFix
from hexagents_cloud.domain.actions.auto_fix import FixProposal
from hexagents_cloud.domain.actions.value_objects import (
    AssumptionId,
    Diff,
    FixId,
    FixStatus,
    HealthStatus,
)
from hexagents_cloud.domain.errors import FixNotApproved


class InMemoryStore:
    def __init__(self) -> None:
        self.by_id: dict[str, FixProposal] = {}

    def load(self, fix_id: str) -> FixProposal:
        return self.by_id[fix_id]

    def save(self, proposal: FixProposal) -> None:
        self.by_id[proposal.fix_id.value] = proposal


class RecordingAudit:
    def __init__(self) -> None:
        self.events = []

    def append(self, event) -> None:
        self.events.append(event)


class FakeK8s:
    def __init__(self, health: HealthStatus = HealthStatus.HEALTHY) -> None:
        self.health = health
        self.applied: list[Diff] = []
        self.restored: list[Diff] = []
        self.verify_calls = 0

    def apply(self, diff: Diff) -> None:
        self.applied.append(diff)

    def verify(self) -> HealthStatus:
        self.verify_calls += 1
        return self.health

    def restore(self, previous: Diff) -> None:
        self.restored.append(previous)


def make_fixture():
    store = InMemoryStore()
    audit = RecordingAudit()
    k8s = FakeK8s()
    proposal = FixProposal(
        fix_id=FixId("fix-1"),
        assumption_id=AssumptionId("asmp-1"),
        diff=Diff(description="limits", patch=["spec:"]),
    )
    approved = proposal.approve("alice")
    store.save(approved)
    return store, audit, k8s, approved


def test_apply_fix_moves_to_applied() -> None:
    store, audit, k8s, _ = make_fixture()
    uc = ApplyFix(store, audit, k8s)

    result = uc.execute("fix-1")

    assert result.status == FixStatus.APPLIED
    assert len(k8s.applied) == 1
    assert any(type(e).__name__ == "FixApplied" for e in audit.events)


def test_apply_fix_without_approval_raises() -> None:
    store = InMemoryStore()
    audit = RecordingAudit()
    k8s = FakeK8s()
    proposal = FixProposal(
        fix_id=FixId("fix-1"),
        assumption_id=AssumptionId("asmp-1"),
        diff=Diff(description="limits", patch=["spec:"]),
    )
    store.save(proposal)
    uc = ApplyFix(store, audit, k8s)

    with pytest.raises(FixNotApproved):
        uc.execute("fix-1")
    assert len(k8s.applied) == 0


def test_apply_fix_regression_triggers_restore() -> None:
    store, audit, k8s, approved = make_fixture()
    k8s.health = HealthStatus.DEGRADED
    uc = ApplyFix(store, audit, k8s)

    result = uc.execute("fix-1")

    assert result.status == FixStatus.ROLLED_BACK
    assert len(k8s.restored) == 1
    assert any(type(e).__name__ == "FixRolledBack" for e in audit.events)
