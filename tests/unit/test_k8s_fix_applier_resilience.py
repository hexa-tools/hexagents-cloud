"""Tests for K8sFixApplier bounded retry / backoff resilience."""

import pytest

from hexagents_cloud.adapters.secondary.k8s_fix_applier import K8sFixApplier
from hexagents_cloud.domain.actions.value_objects import Diff
from hexagents_cloud.domain.errors import K8sApplyError


def _diff() -> Diff:
    return Diff(description="limits", patch=["spec:"])


def test_apply_retries_and_succeeds() -> None:
    calls = {"n": 0}
    applier = K8sFixApplier(apply_fn=_fail_then_succeed(calls, failures=2), sleep_ms=0)

    applier.apply(_diff())

    assert applier.applied == [_diff()]
    assert calls["n"] == 3  # 2 failures + 1 success


def test_apply_fails_after_max_retries() -> None:
    applier = K8sFixApplier(apply_fn=_always_fail(), sleep_ms=0)

    with pytest.raises(K8sApplyError):
        applier.apply(_diff())

    assert applier.apply_calls == K8sFixApplier.MAX_APPLY_RETRIES


def test_apply_backoff_calls_sleep(monkeypatch) -> None:
    sleep_calls: list[float] = []
    monkeypatch.setattr(
        "hexagents_cloud.adapters.secondary.k8s_fix_applier.time.sleep",
        lambda seconds: sleep_calls.append(seconds),
    )
    applier = K8sFixApplier(apply_fn=_fail_then_succeed({"n": 0}, failures=1), sleep_ms=100)

    applier.apply(_diff())

    # First attempt fails, then it sleeps 100ms*1 = 0.1s before the retry.
    assert sleep_calls == [0.1]


def _fail_then_succeed(calls: dict[str, int], failures: int):
    def fn(_diff: Diff) -> None:
        calls["n"] += 1
        if calls["n"] <= failures:
            raise RuntimeError("timeout")

    return fn


def _always_fail():
    def fn(_diff: Diff) -> None:
        raise RuntimeError("timeout")

    return fn
