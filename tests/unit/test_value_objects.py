"""Tests for domain value objects of the ACTIONS bounded context (A1)."""

import pytest

from hexagents_cloud.domain.actions.value_objects import (
    AssumptionId,
    Diff,
    FixId,
    FixStatus,
    HealthStatus,
    Verdict,
)


def test_fix_id_wraps_value() -> None:
    fix_id = FixId("fix-1")
    assert fix_id.value == "fix-1"


def test_fix_id_string_repr() -> None:
    assert str(FixId("fix-2")) == "fix-2"


def test_assumption_id_wraps_value() -> None:
    assumption_id = AssumptionId("asmp-9")
    assert assumption_id.value == "asmp-9"


def test_diff_description_and_patch() -> None:
    diff = Diff(
        description="add resource limits", patch=["spec:", "  containers[0].resources.limits.cpu"]
    )
    assert diff.description == "add resource limits"
    assert len(diff.patch) == 2


def test_diff_rejects_empty_patch() -> None:
    with pytest.raises(ValueError):
        Diff(description="empty", patch=[])


def test_fix_status_enum_values() -> None:
    assert FixStatus.PROPOSED.value == "proposed"
    assert FixStatus.APPROVED.value == "approved"
    assert FixStatus.APPLIED.value == "applied"
    assert FixStatus.ROLLED_BACK.value == "rolled_back"
    assert FixStatus.REJECTED.value == "rejected"


def test_health_status_enum() -> None:
    assert HealthStatus.HEALTHY.value == "healthy"
    assert HealthStatus.DEGRADED.value == "degraded"


def test_verdict_enum() -> None:
    assert Verdict.OK.value == "ok"
    assert Verdict.REGRESSION.value == "regression"
