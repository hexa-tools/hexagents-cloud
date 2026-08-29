"""Tests for the ACTIONS (A1) domain events."""

from hexagents_cloud.domain.actions.events import (
    FixApplied,
    FixApproved,
    FixFailed,
    FixProposed,
    FixRejected,
    FixRolledBack,
)


def test_fix_proposed_event_fields() -> None:
    event = FixProposed(fix_id="fix-1", assumption_id="asmp-1", diff=["spec:"])
    assert event.fix_id == "fix-1"
    assert event.assumption_id == "asmp-1"
    assert event.diff == ["spec:"]


def test_fix_approved_event_has_approver() -> None:
    event = FixApproved(fix_id="fix-1", approver="user-1")
    assert event.approver == "user-1"


def test_fix_applied_event_fields() -> None:
    event = FixApplied(fix_id="fix-1", assumption_id="asmp-1")
    assert event.fix_id == "fix-1"
    assert event.assumption_id == "asmp-1"


def test_fix_rolled_back_event_fields() -> None:
    event = FixRolledBack(fix_id="fix-1")
    assert event.fix_id == "fix-1"


def test_fix_rejected_event_fields() -> None:
    event = FixRejected(fix_id="fix-1", reason="scope out")
    assert event.reason == "scope out"


def test_fix_failed_event_fields() -> None:
    event = FixFailed(fix_id="fix-1", reason="apply timeout")
    assert event.reason == "apply timeout"
