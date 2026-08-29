[![Tests](https://img.shields.io/badge/tests-17_passed-brightgreen.svg)]()

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

`hexagents` is pulled from
[`hexa-tools/hexagents`](https://github.com/hexa-tools/hexagents)
(subdirectory `src/backend`, branch `main`) as a git dependency. No extra
checkout is needed.

```bash
poetry install          # resolves hexagents from git
make check              # ruff + mypy (strict)
poetry run pytest --cov-report=term-missing
```

### Working on both repos (live edit)

When you modify `hexagents` and `hexagents-cloud` together, override the
installed `hexagents` with an editable install pointing at your local checkout
(this is a dev-only step, it does not touch `pyproject.toml`/`poetry.lock`):

```bash
poetry run pip install -e ../hexagents/src/backend
```

`import hexagents` then resolves to your local `hexagents/src/backend`. The
committed `poetry.lock` stays on the git dependency, so CI still installs from
git. The lock is intentionally NOT regenerated during live dev (it would not
change — `pip install -e` is outside Poetry).

License: FSL-1.1-Apache-2.0 (see `LICENSE`).
