"""Tests for ProposeFix use case (A1-1)."""

from hexagents_cloud.application.use_cases.actions.propose_fix import ProposeFix
from hexagents_cloud.domain.actions.auto_fix import FixProposal
from hexagents_cloud.domain.actions.value_objects import Diff, FixStatus
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


class NotifyingNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def notify(self, message: str) -> None:
        self.messages.append(message)


def test_propose_fix_happy_path() -> None:
    store = InMemoryStore()
    audit = RecordingAudit()
    notifier = NotifyingNotifier()
    uc = ProposeFix(store, audit, notifier)

    proposal = uc.execute("fix-1", "asmp-1", Diff(description="limits", patch=["spec:"]))

    assert proposal.status == FixStatus.PROPOSED
    stored = store.load("fix-1")
    assert stored.status == FixStatus.PROPOSED
    assert any(type(e).__name__ == "FixProposed" for e in audit.events)
    assert len(notifier.messages) == 1


def test_propose_fix_with_empty_diff_rejected() -> None:
    store = InMemoryStore()
    audit = RecordingAudit()
    notifier = NotifyingNotifier()
    uc = ProposeFix(store, audit, notifier)

    try:
        uc.execute("fix-1", "asmp-1", Diff(description="noop", patch=[]))
    except (InvalidFixTransition, ValueError):
        return
    raise AssertionError("expected rejection for empty diff")
