"""Tests for RollbackFix use case (A1-4)."""

import pytest

from hexagents_cloud.application.use_cases.actions.rollback_fix import RollbackFix
from hexagents_cloud.domain.actions.auto_fix import FixProposal
from hexagents_cloud.domain.actions.value_objects import (
    AssumptionId,
    Diff,
    FixId,
    FixStatus,
    HealthStatus,
)
from hexagents_cloud.domain.errors import InvalidFixTransition


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
    def __init__(self) -> None:
        self.restored: list[Diff] = []

    def apply(self, diff: Diff) -> None:
        pass

    def verify(self) -> HealthStatus:
        return HealthStatus.HEALTHY

    def restore(self, previous: Diff) -> None:
        self.restored.append(previous)


def make_applied() -> FixProposal:
    proposal = FixProposal(
        fix_id=FixId("fix-1"),
        assumption_id=AssumptionId("asmp-1"),
        diff=Diff(description="limits", patch=["spec:"]),
    )
    return proposal.approve("alice").applied()


def test_rollback_fix_happy_path() -> None:
    store = InMemoryStore()
    audit = RecordingAudit()
    k8s = FakeK8s()
    store.save(make_applied())
    uc = RollbackFix(store, audit, k8s)

    result = uc.execute("fix-1")

    assert result.status == FixStatus.ROLLED_BACK
    assert len(k8s.restored) == 1
    assert any(type(e).__name__ == "FixRolledBack" for e in audit.events)


def test_rollback_fix_not_applied_raises() -> None:
    store = InMemoryStore()
    audit = RecordingAudit()
    k8s = FakeK8s()
    proposal = FixProposal(
        fix_id=FixId("fix-1"),
        assumption_id=AssumptionId("asmp-1"),
        diff=Diff(description="limits", patch=["spec:"]),
    )
    store.save(proposal)
    uc = RollbackFix(store, audit, k8s)

    with pytest.raises(InvalidFixTransition):
        uc.execute("fix-1")
    assert len(k8s.restored) == 0
