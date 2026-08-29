"""Tests for the ApprovalNotifier adapter (implements NotificationPort)."""

from hexagents_cloud.adapters.secondary.approval_notifier import ApprovalNotifier


def test_notify_records_message() -> None:
    notifier = ApprovalNotifier()
    notifier.notify("approval required for fix-1")
    assert notifier.messages == ["approval required for fix-1"]


def test_notify_multiple_messages() -> None:
    notifier = ApprovalNotifier()
    notifier.notify("a")
    notifier.notify("b")
    assert notifier.messages == ["a", "b"]


def test_empty_message_allowed() -> None:
    notifier = ApprovalNotifier()
    notifier.notify("")
    assert notifier.messages == [""]
