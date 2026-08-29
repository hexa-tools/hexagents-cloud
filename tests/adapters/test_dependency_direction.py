"""Contract test: the public harness must never reference the private package.

The dependency direction is strictly one-way (hexagents-cloud -> hexagents).
``test_dependency_direction`` proves the reverse is absent: no ``hexagents_cloud``
symbol appears anywhere in the public harness source.
"""

import pathlib

import pytest

from hexagents_cloud.adapters.primary.registry import register


def _public_source_root() -> pathlib.Path | None:
    """Return the public package source root, or None if not resolvable."""
    try:
        import hexagents  # type: ignore[import-untyped]
    except ImportError:
        return None
    return pathlib.Path(hexagents.__file__).parent


def test_public_never_references_private() -> None:
    root = _public_source_root()
    if root is None:
        pytest.skip("public hexagents package not installed — cannot scan")

    offenders: list[str] = []
    for py_file in root.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        if "hexagents_cloud" in text:
            offenders.append(str(py_file))

    assert offenders == [], f"public harness references private: {offenders}"


def test_public_works_without_private_registered() -> None:
    """The private layer can be imported/instantiated independently of the
    public harness extension point (register degrades gracefully)."""
    packs = register()
    assert "cloud.actions.approve" in packs
