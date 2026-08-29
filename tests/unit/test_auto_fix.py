"""Tests for the FixProposal aggregate (ACTIONS / A1)."""

import pytest

from hexagents_cloud.domain.actions.auto_fix import FixProposal
from hexagents_cloud.domain.actions.value_objects import AssumptionId, Diff, FixId, FixStatus
from hexagents_cloud.domain.errors import FixNotApproved, InvalidFixTransition


def make_proposal() -> FixProposal:
    return FixProposal(
        fix_id=FixId("fix-1"),
        assumption_id=AssumptionId("asmp-1"),
        diff=Diff(description="add limits", patch=["spec:", "  resources.limits.cpu"]),
    )


def test_new_proposal_is_proposed() -> None:
    proposal = make_proposal()
    assert proposal.status == FixStatus.PROPOSED
    assert proposal.events[0].fix_id == "fix-1"


def test_approve_moves_to_approved_and_emits_event() -> None:
    proposal = make_proposal()
    approved = proposal.approve()
    assert approved.status == FixStatus.APPROVED
    assert any(e.__class__.__name__ == "FixApproved" for e in approved.events)
    assert proposal.status == FixStatus.PROPOSED


def test_apply_without_approval_raises_fix_not_approved() -> None:
    proposal = make_proposal()
    with pytest.raises(FixNotApproved):
        proposal.applied()


def test_apply_after_approve_moves_to_applied() -> None:
    approved = make_proposal().approve()
    applied = approved.applied()
    assert applied.status == FixStatus.APPLIED
    assert any(e.__class__.__name__ == "FixApplied" for e in applied.events)


def test_apply_twice_is_invalid_transition() -> None:
    applied = make_proposal().approve().applied()
    with pytest.raises(InvalidFixTransition):
        applied.applied()


def test_approve_twice_is_invalid_transition() -> None:
    approved = make_proposal().approve()
    with pytest.raises(InvalidFixTransition):
        approved.approve()


def test_rollback_after_applied_moves_to_rolled_back() -> None:
    applied = make_proposal().approve().applied()
    rolled_back = applied.rollback()
    assert rolled_back.status == FixStatus.ROLLED_BACK
    assert any(e.__class__.__name__ == "FixRolledBack" for e in rolled_back.events)


def test_rollback_before_applied_is_invalid() -> None:
    proposal = make_proposal()
    with pytest.raises(InvalidFixTransition):
        proposal.rollback()


def test_reject_moves_to_rejected() -> None:
    proposal = make_proposal()
    rejected = proposal.reject("out of scope")
    assert rejected.status == FixStatus.REJECTED
    assert any(e.__class__.__name__ == "FixRejected" for e in rejected.events)
