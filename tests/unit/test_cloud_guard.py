"""Tests for cloud_guard.py — the architecture guard (hook + scanner)."""

import json
from pathlib import Path

import pytest
from cloud_guard import check_file, main, scan


@pytest.fixture
def clean_file(tmp_path: Path) -> Path:
    f = tmp_path / "plain.py"
    f.write_text("def hello() -> str:\n    return 'hi'\n", encoding="utf-8")
    return f


def test_clean_file_has_no_violations(clean_file: Path) -> None:
    assert check_file(clean_file, clean_file.read_text()) == []


def test_infra_import_in_domain_triggers_violation(tmp_path: Path) -> None:
    f = tmp_path / "domain" / "bad.py"
    f.parent.mkdir(exist_ok=True)
    code = "import httpx\n"
    results = check_file(f, code)
    assert any("HEXAGONAL VIOLATION" in r for r in results)


def test_domain_imports_application_triggers_violation(tmp_path: Path) -> None:
    f = tmp_path / "domain" / "bad.py"
    code = "from application import foo\n"
    results = check_file(f, code)
    assert any("DDD VIOLATION" in r for r in results)


def test_secret_pattern_triggers_violation(tmp_path: Path) -> None:
    f = tmp_path / "code.py"
    code = "api_key = 'ghp_secret'\n"
    results = check_file(f, code)
    assert any("SECURITY VIOLATION" in r for r in results)


def test_scan_returns_zero_on_clean_tree(tmp_path: Path) -> None:
    (tmp_path / "ok.py").write_text("x = 1\n", encoding="utf-8")
    assert scan(tmp_path) == 0


def test_scan_returns_one_on_violating_tree(tmp_path: Path) -> None:
    (tmp_path / "domain" / "bad.py").parent.mkdir(exist_ok=True)
    (tmp_path / "domain" / "bad.py").write_text("import fastapi\n", encoding="utf-8")
    assert scan(tmp_path) == 1


def test_main_approves_without_stdin(monkeypatch) -> None:
    monkeypatch.setattr("sys.stdin", type("S", (), {"read": lambda self: ""})())
    assert main() == 0


def test_main_blocks_on_write_with_violation(monkeypatch, tmp_path: Path) -> None:
    f = tmp_path / "domain" / "bad.py"
    event = json.dumps(
        {
            "tool_name": "Write",
            "tool_input": {"file_path": str(f), "content": "import fastapi\n"},
        }
    )
    monkeypatch.setattr("sys.stdin", type("S", (), {"read": lambda self: event})())
    assert main() == 2
