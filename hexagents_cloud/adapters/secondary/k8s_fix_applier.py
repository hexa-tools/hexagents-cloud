"""K8sFixApplier adapter — K8sPort implementation with bounded retry/backoff.

The adapter owns the infra resilience (bounded retries, capped backoff) and
translates transport errors into a domain ``K8sApplyError`` before propagating.
The use case stays pure: it calls ``apply`` once and lets the adapter handle
retries.
"""

import time
from collections.abc import Callable

from hexagents_cloud.application.ports_closed import K8sPort
from hexagents_cloud.domain.actions.value_objects import Diff, HealthStatus
from hexagents_cloud.domain.errors import K8sApplyError


def _default_apply(diff: Diff) -> None:
    """No-op placeholder for the real cluster write (in-memory sandbox)."""


class K8sFixApplier(K8sPort):
    """Applies diffs with bounded retries (capped backoff), then reports health."""

    MAX_APPLY_RETRIES = 3

    def __init__(
        self,
        health: HealthStatus = HealthStatus.HEALTHY,
        apply_fn: Callable[[Diff], None] = _default_apply,
        sleep_ms: int = 1000,
    ) -> None:
        self.health = health
        self._apply_fn = apply_fn
        self._sleep_ms = sleep_ms
        self.applied: list[Diff] = []
        self.restored: list[Diff] = []
        self.apply_calls = 0

    def apply(self, diff: Diff) -> None:
        for attempt in range(self.MAX_APPLY_RETRIES):
            self.apply_calls += 1
            try:
                self._apply_fn(diff)
            except Exception as exc:
                if attempt == self.MAX_APPLY_RETRIES - 1:
                    raise K8sApplyError(str(exc)) from exc
                self._sleep(attempt + 1)
                continue
            self.applied.append(diff)
            return

    def _sleep(self, multiplier: int) -> None:
        if self._sleep_ms > 0:
            time.sleep(self._sleep_ms * multiplier / 1000)

    def verify(self) -> HealthStatus:
        return self.health

    def restore(self, previous: Diff) -> None:
        self.restored.append(previous)
