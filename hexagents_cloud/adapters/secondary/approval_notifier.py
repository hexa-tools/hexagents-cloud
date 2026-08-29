"""ApprovalNotifier adapter — in-memory NotificationPort implementation."""

from hexagents_cloud.application.ports_closed import NotificationPort


class ApprovalNotifier(NotificationPort):
    """Collects notifications in memory (stand-in until the mobile push lands)."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def notify(self, message: str) -> None:
        self.messages.append(message)
