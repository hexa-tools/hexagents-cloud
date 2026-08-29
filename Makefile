# ═══════════════════════════════════════════════════════════
#  hexagents-cloud — Makefile
# ═══════════════════════════════════════════════════════════

# ─────────────────────────────────────
#  Variables
# ─────────────────────────────────────

POETRY  := poetry
PYTHON  := $(POETRY) run python
PYTEST  := $(POETRY) run pytest
RUFF    := $(POETRY) run ruff
MYPY    := $(POETRY) run mypy

ifneq (,$(wildcard .env))
include .env
export
endif

# ─────────────────────────────────────
#  Dev setup
# ─────────────────────────────────────

.PHONY: install

install:
	@echo "📦 Installing all dependencies..."
	$(POETRY) install --with dev
	@echo "✅ Dependencies installed"

# ─────────────────────────────────────
#  Code quality
# ─────────────────────────────────────

.PHONY: lint format format-check type-check check

lint:
	@echo "🔍 Linting Python with ruff..."
	$(RUFF) check hexagents_cloud/ tests/
	@echo "✅ Lint passed"

format:
	@echo "🎨 Formatting Python with ruff..."
	$(RUFF) format hexagents_cloud/ tests/
	@echo "✅ Formatting done"

format-check:
	@echo "📐 Checking Python formatting with ruff..."
	$(RUFF) format --check hexagents_cloud/ tests/
	@echo "✅ Format check passed"

type-check:
	@echo "🔎 Running mypy strict type check..."
	$(MYPY) hexagents_cloud/
	@echo "✅ Type check passed"

check:
	@echo "🔍 Running all quality checks..."
	@echo ""
	@$(MAKE) lint
	@$(MAKE) format-check
	@$(MAKE) type-check
	@echo ""
	@echo "✅ All checks passed"

# ─────────────────────────────────────
#  Tests
# ─────────────────────────────────────

.PHONY: test test-integration test-e2e test-all coverage update-badge

test:
	@echo "🧪 Running unit tests..."
	$(PYTEST) tests/unit/ -q --tb=short
	@echo "✅ Unit tests passed"

test-integration:
	@echo "🔬 Running integration tests (sandbox targets)..."
	SANDBOX_MODE=true $(PYTEST) tests/integration/ -v -m integration
	@echo "✅ Integration tests passed"

test-e2e:
	@echo "🧪 Running E2E tests (real environment, CI release only)..."
	$(PYTEST) tests/e2e/ -v -m e2e --strict-markers --tb=short
	@echo "✅ E2E tests passed"

test-all:
	@echo "🧪 Running all tests (unit + integration)..."
	$(PYTEST) tests/unit/ tests/integration/ -v
	@echo "✅ All tests passed"

coverage:
	@echo "📊 Running tests with coverage..."
	$(PYTEST) tests/ --cov=hexagents_cloud --cov-report=term-missing --cov-fail-under=95
	@echo "✅ Coverage threshold met"

update-badge:
	@echo "🏷️  Updating test count badge in README.md..."
	$(PYTHON) scripts/update_test_badge.py
	@echo "✅ Badge updated"

# ─────────────────────────────────────
#  Guard
# ─────────────────────────────────────

.PHONY: guard

guard:
	@echo "🛡️  Running cloud_guard..."
	$(PYTHON) cloud_guard.py --all --root hexagents_cloud
	@echo "✅ Guard rules validated"

# ─────────────────────────────────────
#  Maintenance
# ─────────────────────────────────────

.PHONY: clean

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf dist/ .coverage coverage.xml htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	@echo "✅ Clean complete"

# ─────────────────────────────────────
#  Help
# ─────────────────────────────────────

.PHONY: help

help:
	@echo ""
	@echo "══════════════════════════════════════════"
	@echo "     ☁️  HEXAGENTS-CLOUD — Action Layer"
	@echo "══════════════════════════════════════════"
	@echo ""
	@echo "📦 DEV SETUP"
	@echo "  make install               → Install Poetry dependencies"
	@echo ""
	@echo "🧪 CODE QUALITY"
	@echo "  make lint                  → Lint Python with ruff"
	@echo "  make format                → Auto-format Python with ruff"
	@echo "  make format-check          → Check formatting with ruff"
	@echo "  make type-check            → Strict mypy type check"
	@echo "  make check                 → Run lint + format-check + type-check"
	@echo "  make guard                 → Run cloud_guard.py rules"
	@echo ""
	@echo "🧪 TESTS"
	@echo "  make test                  → Run unit tests"
	@echo "  make test-integration      → Run integration tests (sandbox)"
	@echo "  make test-e2e              → Run E2E tests (CI release only)"
	@echo "  make test-all              → Run unit + integration tests"
	@echo "  make coverage              → Run tests with coverage (≥95%)"
	@echo "  make update-badge          → Update test count badge in README.md"
	@echo ""
	@echo "🧹 MAINTENANCE"
	@echo "  make clean                 → Remove build artifacts and caches"
	@echo ""
	@echo "══════════════════════════════════════════"
	@echo ""
