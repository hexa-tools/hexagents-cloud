"""Tests for scripts/update_test_badge.py."""

import subprocess

from scripts.update_test_badge import (
    BADGE_PATTERN,
    count_tests,
    render_badge_url,
    update_badge,
)


def test_render_badge_url_returns_shields_url() -> None:
    assert render_badge_url(12) == "https://img.shields.io/badge/tests-12_passed-brightgreen.svg"


def test_render_badge_url_zero() -> None:
    assert render_badge_url(0) == "https://img.shields.io/badge/tests-0_passed-brightgreen.svg"


def test_badge_pattern_matches_url_encoded_plus() -> None:
    encoded = "https://img.shields.io/badge/tests-8500%2B_passed-brightgreen.svg"
    assert BADGE_PATTERN.match(encoded) is not None


def test_count_tests_returns_collected_count(monkeypatch) -> None:
    class FakeResult:
        stdout = "tests/unit/test_a.py: 5\n3 warnings\ntests/unit/test_b.py: 7\n"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeResult())
    assert count_tests() == 12


def test_count_tests_returns_zero_on_no_match(monkeypatch) -> None:
    class FakeResult:
        stdout = "nothing collected here\n"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeResult())
    assert count_tests() == 0


def test_count_tests_falls_back_to_collected_summary(monkeypatch) -> None:
    class FakeResult:
        stdout = "12 tests collected in 0.01s\n"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeResult())
    assert count_tests() == 12


def test_update_badge_replaces_count_and_writes(tmp_path, monkeypatch) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "# t\n[![Tests](https://img.shields.io/badge/tests-3_passed-brightgreen.svg)]()\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("scripts.update_test_badge.README", readme)

    changed = update_badge(42)

    assert changed is True
    assert "tests-42_passed" in readme.read_text(encoding="utf-8")


def test_update_badge_reports_when_already_current(tmp_path, monkeypatch) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "# t\n[![Tests](https://img.shields.io/badge/tests-10_passed-brightgreen.svg)]()\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("scripts.update_test_badge.README", readme)

    changed = update_badge(10)

    assert changed is False


def test_update_badge_reports_missing_pattern(tmp_path, monkeypatch) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("no badge here\n", encoding="utf-8")
    monkeypatch.setattr("scripts.update_test_badge.README", readme)

    changed = update_badge(10)

    assert changed is False
