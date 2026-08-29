"""Tests for the K8sFixApplier adapter (implements K8sPort)."""

from hexagents_cloud.adapters.secondary.k8s_fix_applier import K8sFixApplier
from hexagents_cloud.domain.actions.value_objects import Diff, HealthStatus


def test_apply_records_diff() -> None:
    applier = K8sFixApplier()
    diff = Diff(description="limits", patch=["spec:"])
    applier.apply(diff)
    assert applier.applied == [diff]


def test_verify_returns_health() -> None:
    applier = K8sFixApplier()
    assert applier.verify() == HealthStatus.HEALTHY


def test_restore_records_previous() -> None:
    applier = K8sFixApplier()
    previous = Diff(description="prev", patch=["spec:"])
    applier.restore(previous)
    assert applier.restored == [previous]


def test_can_force_degraded_health() -> None:
    applier = K8sFixApplier(health=HealthStatus.DEGRADED)
    assert applier.verify() == HealthStatus.DEGRADED
