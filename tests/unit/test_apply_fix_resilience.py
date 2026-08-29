"""Tests for the ApplyFix use case resilience edge cases (K8s timeout/retry)."""

import pytest

from hexagents_cloud.application.use_cases.actions.apply_fix import ApplyFix
from hexagents_cloud.domain.actions.auto_fix import FixProposal
from hexagents_cloud.domain.actions.value_objects import (
    AssumptionId,
    Diff,
    FixId,
    HealthStatus,
)
from hexagents_cloud.domain.errors import K8sApplyError


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


class FailingK8s:
    """Always raises K8sApplyError on apply (simulates persistent timeout)."""

    def __init__(self) -> None:
        self.restored: list[Diff] = []

    def apply(self, diff: Diff) -> None:
        raise K8sApplyError("fix-1")

    def verify(self) -> HealthStatus:
        return HealthStatus.HEALTHY

    def restore(self, previous: Diff) -> None:
        self.restored.append(previous)


def make_approved() -> FixProposal:
    proposal = FixProposal(
        fix_id=FixId("fix-1"),
        assumption_id=AssumptionId("asmp-1"),
        diff=Diff(description="limits", patch=["spec:"]),
    )
    return proposal.approve("alice")


def test_apply_fix_append_fix_failed_then_raises() -> None:
    store = InMemoryStore()
    audit = RecordingAudit()
    store.save(make_approved())
    k8s = FailingK8s()
    uc = ApplyFix(store, audit, k8s)

    with pytest.raises(K8sApplyError):
        uc.execute("fix-1")

    failed_events = [e for e in audit.events if type(e).__name__ == "FixFailed"]
    assert len(failed_events) == 1
