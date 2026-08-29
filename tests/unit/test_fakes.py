"""Tests for the in-memory fakes (adapters/secondary/fakes)."""

import pytest

from hexagents_cloud.adapters.secondary.fakes.fakes import (
    InMemoryAuditStore,
    InMemoryFixProposalStore,
    InMemoryK8s,
    InMemoryNotification,
)
from hexagents_cloud.domain.actions.auto_fix import FixProposal
from hexagents_cloud.domain.actions.events import FixApproved, FixProposed
from hexagents_cloud.domain.actions.value_objects import AssumptionId, Diff, FixId, HealthStatus
from hexagents_cloud.domain.errors import FixNotFound


def make_proposal() -> FixProposal:
    return FixProposal(
        fix_id=FixId("fix-1"),
        assumption_id=AssumptionId("asmp-1"),
        diff=Diff(description="limits", patch=["spec:"]),
    )


def test_store_save_and_load() -> None:
    store = InMemoryFixProposalStore()
    store.save(make_proposal())
    assert store.load("fix-1").fix_id.value == "fix-1"


def test_store_load_missing_raises() -> None:
    store = InMemoryFixProposalStore()
    with pytest.raises(FixNotFound):
        store.load("fix-999")


def test_k8s_apply_verify_restore() -> None:
    k8s = InMemoryK8s()
    k8s.apply(make_proposal().diff)
    assert k8s.verify() == HealthStatus.HEALTHY
    k8s.restore(make_proposal().diff)
    assert len(k8s.applied) == 1
    assert len(k8s.restored) == 1


def test_k8s_degraded() -> None:
    k8s = InMemoryK8s(health=HealthStatus.DEGRADED)
    assert k8s.verify() == HealthStatus.DEGRADED


def test_audit_records_events() -> None:
    audit = InMemoryAuditStore()
    audit.append(FixProposed(fix_id="fix-1", assumption_id="asmp-1", diff=["spec:"]))
    audit.append(FixApproved(fix_id="fix-1", approver="alice"))
    assert len(audit.events) == 2


def test_notification_records_messages() -> None:
    notif = InMemoryNotification()
    notif.notify("hi")
    assert notif.messages == ["hi"]
