"""Tests for the AuditWriter adapter (implements AuditStorePort)."""

from hexagents_cloud.adapters.secondary.audit_writer import AuditWriter
from hexagents_cloud.domain.actions.events import FixApproved, FixProposed


def test_append_records_events() -> None:
    writer = AuditWriter()
    event = FixApproved(fix_id="fix-1", approver="alice")
    writer.append(event)
    assert writer.events == [event]


def test_append_multiple_events() -> None:
    writer = AuditWriter()
    writer.append(FixProposed(fix_id="fix-1", assumption_id="asmp-1", diff=["spec:"]))
    writer.append(FixApproved(fix_id="fix-1", approver="alice"))
    assert len(writer.events) == 2
    assert type(writer.events[1]).__name__ == "FixApproved"


def test_append_propagates_event_type() -> None:
    writer = AuditWriter()
    event = FixApproved(fix_id="fix-1", approver="alice")
    writer.append(event)
    assert writer.events[0].event_type == "FixApproved"
