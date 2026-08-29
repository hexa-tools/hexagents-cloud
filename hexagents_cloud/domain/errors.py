"""Domain errors for hexagents-cloud.

All exceptions inherit from ``HexagentsCloudError`` so callers can catch a
single base type. Contextual params are carried in ``__init__``.
"""


class HexagentsCloudError(Exception):
    """Base class for all hexagents-cloud errors."""


class InvalidFixTransition(HexagentsCloudError):
    """Raised when a FixProposal transition is not legal from its current state."""

    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"Invalid FixProposal transition from status '{status}'")


class FixNotApproved(HexagentsCloudError):
    """Raised when attempting to apply a FixProposal that is not APPROVED."""

    def __init__(self, fix_id: str) -> None:
        self.fix_id = fix_id
        super().__init__(f"Fix '{fix_id}' is not approved; cannot apply")


class FixNotFound(HexagentsCloudError):
    """Raised when a FixProposal store has no proposal for the given id."""

    def __init__(self, fix_id: str) -> None:
        self.fix_id = fix_id
        super().__init__(f"Fix '{fix_id}' not found")


class K8sApplyError(HexagentsCloudError):
    """Raised when the K8s adapter cannot apply a diff after bounded retries."""

    def __init__(self, fix_id: str) -> None:
        self.fix_id = fix_id
        super().__init__(f"K8s apply failed for fix '{fix_id}' after retries")
