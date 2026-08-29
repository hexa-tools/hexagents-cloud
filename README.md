[![Tests](https://img.shields.io/badge/tests-9_passed-brightgreen.svg)]()

# hexagents-cloud

Private action layer for HexAgents. Built on the `hexagents` harness
(open-core) and licensed under the Functional Source License (FSL-1.1).

## Layering

```
hexagents-cloud  →  hexagents  (public harness)
```

Unidirectional: the private package consumes the public harness and
registers itself into the public extension points. The public never
referenced the private package (`tests/adapters/test_dependency_direction.py`).

## Architecture

Ports & Adapters (hexagonal) + DDD-lite:

- `hexagents_cloud/domain/` — pure Python, zero external I/O (invariants, aggregates, value objects, events)
- `hexagents_cloud/application/` — use cases + closed ports (`ports_closed.py`)
- `hexagents_cloud/adapters/` — primary (registry, api) and secondary (k8s, git, social, billing, audit) adapters

## Development

```bash
poetry install
make check          # ruff + mypy (strict)
poetry run pytest --cov-report=term-missing
```

License: FSL-1.1-Apache-2.0 (see `LICENSE`).
