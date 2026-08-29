"""Tests for domain errors of the ACTIONS bounded context (A1)."""

from hexagents_cloud.domain.errors import (
    FixNotApproved,
    FixNotFound,
    HexagentsCloudError,
    InvalidFixTransition,
    K8sApplyError,
)


def test_all_errors_inherit_base() -> None:
    assert issubclass(InvalidFixTransition, HexagentsCloudError)
    assert issubclass(FixNotApproved, HexagentsCloudError)
    assert issubclass(FixNotFound, HexagentsCloudError)
    assert issubclass(K8sApplyError, HexagentsCloudError)


def test_hexagents_cloud_error_is_exception() -> None:
    assert issubclass(HexagentsCloudError, Exception)


def test_invalid_fix_transition_carries_status() -> None:
    error = InvalidFixTransition("proposed")
    assert "proposed" in str(error)


def test_fix_not_approved_carries_fix_id() -> None:
    error = FixNotApproved("fix-1")
    assert "fix-1" in str(error)


def test_fix_not_found_carries_fix_id() -> None:
    error = FixNotFound("fix-42")
    assert "fix-42" in str(error)
