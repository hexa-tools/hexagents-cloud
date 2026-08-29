#!/usr/bin/env python3
"""
hexa_guard.py — Claude Code hook for hexawyn
Enforces: Hexagonal Architecture + DDD + TDD + Security

Place at: hexa_guard.py (project root)
Triggered by: .claude/settings.json PostToolUse hook

Rules:
  R1  — Hexagonal: no infra imports in domain/ or application/
  R2  — TDD: no source file without a test
  R3  — DDD: use case folder structure
  R4  — DDD: domain depends on nothing
  R5  — Hexagonal: adapters don't import domain directly
  R6  — Exception strategy: no try/catch or generic raise in services
  R7  — Security: no secrets in code
  R8  — Security: no SELECT * in DuckDB queries
  R9  — Mutation Guard: no destructive ops in read-only tools
  R10 — Demo mode: DemoAdapter only in mock/
  R11 — Demo mode: never hardcoded
  R12 — TypedDict: no dict[str, Any] return types in use cases
  R13 — SQL: no inline SQL in Python
  R14 — LangGraph: no direct LLM provider imports in nodes
  R15 — Imports: module-level only, no function-scoped imports
"""

import json
import sys
from pathlib import Path

# ─────────────────────────────────────────────
# Read Claude Code event
# ─────────────────────────────────────────────
data = json.load(sys.stdin)
tool_name = data.get("tool_name", "")
tool_input = data.get("tool_input", {})

# Only watch write operations
if tool_name not in ("Write", "Edit", "MultiEdit"):
    sys.exit(0)

file_path = tool_input.get("file_path", "")
if not file_path:
    sys.exit(0)

path = Path(file_path)
content = tool_input.get("content", tool_input.get("new_content", ""))
str_path = str(path)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def block(rule: str, reason: str):
    print(json.dumps({
        "decision": "block",
        "reason": f"[hexa_guard] ❌ {rule}\n{reason}"
    }))
    sys.exit(2)

def warn(rule: str, reason: str):
    """Non-blocking warning — Claude Code continues but sees the message."""
    print(json.dumps({
        "decision": "warn",
        "reason": f"[hexa_guard] ⚠️  {rule}\n{reason}"
    }))

def is_test_file(p: Path) -> bool:
    return p.stem.startswith("test_") or p.stem.endswith("_test")

def find_test(p: Path) -> bool:
    """Look for a corresponding unit test file."""
    candidates = [
        Path("tests") / "unit" / f"test_{p.stem}.py",
        Path("tests") / "unit" / p.parent.name / f"test_{p.stem}.py",
        p.parent / f"test_{p.stem}.py",
        p.parent.parent / "tests" / f"test_{p.stem}.py",
    ]
    return any(c.exists() for c in candidates)

def contains_any(text: str, patterns: list[str]) -> str | None:
    """Return first matching pattern or None."""
    for pattern in patterns:
        if pattern in text:
            return pattern
    return None

def _is_optional_dep_import(statement: str) -> bool:
    """Check if an import statement is for a known optional dependency."""
    for prefix in OPTIONAL_DEP_PREFIXES:
        if (
            statement.startswith(f"import {prefix}")
            or statement.startswith(f"from {prefix}")
        ):
            return True
    return False

# ─────────────────────────────────────────────
# RULE 1 — Hexagonal: no infra imports in domain/ or application/
# ─────────────────────────────────────────────
INFRA_IMPORTS = [
    "import kubernetes", "from kubernetes",
    "import click",      "from click",
    "import fastapi",    "from fastapi",
    "import flask",      "from flask",
    "import boto3",      "from boto3",
    "import httpx",      "from httpx",
    "import requests",   "from requests",
    "import aiohttp",    "from aiohttp",
    "import grpc",       "from grpc",
    "import urllib",     "from urllib",
    "import sqlalchemy", "from sqlalchemy",
    "import redis",      "from redis",
    "import valkey",     "from valkey",
    "import duckdb",     "from duckdb",
    "import anthropic",  "from anthropic",
    "import openai",     "from openai",
    "import textual",    "from textual",
]

PROTECTED_LAYERS = (
    "domain/",
    "application/ports/",
    "application/service/",
)

if any(layer in str_path for layer in PROTECTED_LAYERS) and not is_test_file(path):
    match = contains_any(content, INFRA_IMPORTS)
    if match:
        block(
            "HEXAGONAL VIOLATION — infra import in protected layer",
            f"'{match}' is forbidden in '{path}'.\n"
            f"Infrastructure dependencies belong in adapters/ only.\n"
            f"domain/ and application/ must have zero external dependencies."
        )

# ─────────────────────────────────────────────
# RULE 2 — TDD: no source file without a test
# ─────────────────────────────────────────────
SKIP_TDD = {
    "__init__", "config", "constants", "settings",
    "types", "errors", "models", "agent_state",
    "hexa_guard", "conftest",
}
TDD_LAYERS = ("domain/", "application/", "adapters/", "lang_graph/", "infrastructure/")

if (
    path.suffix == ".py"
    and not is_test_file(path)
    and path.stem not in SKIP_TDD
    and any(layer in str_path for layer in TDD_LAYERS)
):
    if not find_test(path):
        block(
            "TDD VIOLATION",
            f"No test found for '{path}'.\n"
            f"Create first: tests/unit/test_{path.stem}.py\n"
            f"Rule: Red test first → implement → green."
        )

# ─────────────────────────────────────────────
# RULE 3 — DDD: use case folder structure
# Only use_case.py / command.py / response.py allowed
# ─────────────────────────────────────────────
DRIVING_PORTS = "application/ports/driving"

_ALLOWED_SUFFIXES = ("_command", "_response", "_service_port", "_use_case")

if DRIVING_PORTS in str_path and path.suffix == ".py" and not is_test_file(path):
    stem = path.stem
    is_allowed = (
        stem == "__init__"
        or any(stem.endswith(s) for s in _ALLOWED_SUFFIXES)
    )
    if not is_allowed:
        block(
            "DDD VIOLATION — invalid file in driving port",
            f"'{path.name}' is not allowed in {DRIVING_PORTS}/.\n"
            f"Allowed stems: *_command.py, *_response.py, *_service_port.py, "
            f"*_use_case.py, __init__.py\n"
            f"Never mix command, response and service_port in the same file."
        )

# ─────────────────────────────────────────────
# RULE 4 — DDD: domain depends on nothing
# ─────────────────────────────────────────────
DOMAIN_FORBIDDEN_IMPORTS = [
    "from application",    "import application",
    "from adapters",       "import adapters",
    "from infrastructure", "import infrastructure",
    "from lang_graph",     "import lang_graph",
    "from cli",            "import cli",
    "from server",         "import server",
]

if "domain/" in str_path and not is_test_file(path):
    match = contains_any(content, DOMAIN_FORBIDDEN_IMPORTS)
    if match:
        block(
            "DDD VIOLATION — domain imports external layer",
            f"'{match}' is forbidden in domain/.\n"
            f"The domain must depend on nothing — pure Python only.\n"
            f"Move the dependency to application/ or adapters/."
        )

# ─────────────────────────────────────────────
# RULE 5 — Hexagonal: adapters don't import domain directly
# They go through application/ports/
# ─────────────────────────────────────────────
ADAPTER_DIRECT_DOMAIN = [
    "from hexawyn.domain.models",
    "from hexawyn.domain.services",
    "import hexawyn.domain",
    "from domain",
    "import domain",
]
# domain/errors is explicitly allowed: adapters must raise HexawynError subclasses.
# domain/models and domain/services are forbidden — go through application/ports/.

if "adapters/" in str_path and not is_test_file(path):
    match = contains_any(content, ADAPTER_DIRECT_DOMAIN)
    if match:
        block(
            "HEXAGONAL VIOLATION — adapter imports domain directly",
            f"'{match}' is forbidden in adapters/.\n"
            f"Adapters must go through application/ports/ — never domain models or services.\n"
            f"Exception: from hexawyn.domain.errors import ... is allowed "
            f"(raise HexawynError).\n"
            f"Use: from hexawyn.application.ports.driven.xxx import XxxPort"
        )

# ─────────────────────────────────────────────
# RULE 6 — Exception strategy: no try/catch or generic raise in services
# ─────────────────────────────────────────────
SERVICE_LAYERS = ("application/service/", "domain/services/")

if any(layer in str_path for layer in SERVICE_LAYERS) and not is_test_file(path):
    # Detect try/except blocks
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("except ") or stripped == "except:":
            block(
                "EXCEPTION STRATEGY VIOLATION — try/catch in service",
                f"Line {i} in '{path}': '{stripped}'\n"
                f"Services must NEVER catch exceptions — let HexawynError propagate.\n"
                f"Only primary adapters (CLI, LangGraph nodes) do the final catch."
            )

    # Detect generic raises
    GENERIC_RAISES = [
        "raise Exception(",
        "raise ValueError(",
        "raise RuntimeError(",
        "raise TypeError(",
        "raise KeyError(",
    ]
    match = contains_any(content, GENERIC_RAISES)
    if match:
        block(
            "EXCEPTION STRATEGY VIOLATION — generic exception raised in service",
            f"'{match}' detected in '{path}'.\n"
            f"Never raise generic exceptions in services or domain.\n"
            f"Define a specific subclass in domain/errors.py:\n"
            f"  class MySpecificError(HexawynError): ...\n"
            f"and raise that instead."
        )

# ─────────────────────────────────────────────
# RULE 7 — Security: no secrets in code
# ─────────────────────────────────────────────
SECRET_PATTERNS = [
    "sk-ant-",             # Anthropic API key
    "AKIA",                # AWS access key
    "-----BEGIN RSA",      # Private key
    "-----BEGIN EC",       # EC private key
    "ghp_",                # GitHub Personal Access Token
    "xoxb-",               # Slack Bot Token
    "xoxp-",               # Slack User Token
    "AIza",                # Google API Key
    "sk-",                 # OpenAI key
    "DD_API_KEY",          # Datadog API key hardcoded
    "SNOWFLAKE_PASSWORD",  # Snowflake password
    "password =",          # hardcoded password
    "password=",
    'password = "',
    "api_key =",
    'api_key = "',
    "secret_key =",
    'secret_key = "',
    "token =",
    'token = "',
]

# Skip .env.example and test files
if not str_path.endswith(".env.example") and not is_test_file(path):
    match = contains_any(content, SECRET_PATTERNS)
    if match:
        block(
            "SECURITY VIOLATION — potential secret in code",
            f"Pattern '{match}' detected in '{path}'.\n"
            f"Never hardcode secrets, API keys, or passwords.\n"
            f"Use environment variables via config.py:\n"
            f"  ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')"
        )

# ─────────────────────────────────────────────
# RULE 8 — Security: no SELECT * in DuckDB queries
# ─────────────────────────────────────────────
if "infrastructure/memory/" in str_path or "duckdb" in str_path.lower():
    if "SELECT *" in content or "select *" in content:
        block(
            "DUCKDB VIOLATION — SELECT * forbidden",
            f"'SELECT *' detected in '{path}'.\n"
            f"Always use explicit columns for DuckDB queries.\n"
            f"Example: SELECT id, tool_name, cause, severity FROM incidents WHERE ..."
        )

# ─────────────────────────────────────────────
# RULE 9 — Mutation Guard: no destructive language in read-only tools
# ─────────────────────────────────────────────
READONLY_TOOL_PATHS = (
    "application/ports/driving/",
    "application/service/",
    "domain/services/",
)

DESTRUCTIVE_PATTERNS = [
    "delete_namespace",
    "delete namespace",
    "kubectl delete ns",
    "patch clusterrole",
    "patch_cluster_role",
    "scale replicas=0",
    "replicas=0",
    "drain node",
    "cordon node",
    "delete_persistent_volume",
    "delete persistentvolume",
]

if any(layer in str_path for layer in READONLY_TOOL_PATHS) and not is_test_file(path):
    match = contains_any(content.lower(), [p.lower() for p in DESTRUCTIVE_PATTERNS])
    if match:
        block(
            "MUTATION GUARD — destructive operation in read-only layer",
            f"Pattern '{match}' detected in '{path}'.\n"
            f"Read-only tools must NEVER perform destructive operations.\n"
            f"Blocked operations: delete namespace, patch clusterrole, "
            f"scale replicas=0, drain, cordon, delete persistentvolume.\n"
            f"If this is intentional, it belongs in a separate write adapter."
        )

# ─────────────────────────────────────────────
# RULE 10 — Demo mode: DemoAdapter only in mock/
# ─────────────────────────────────────────────
if "DemoAdapter" in content and "mock/" not in str_path and "adapter_factory" not in str_path:
    block(
        "DEMO MODE VIOLATION — DemoAdapter outside mock/",
        f"'DemoAdapter' detected in '{path}'.\n"
        f"DemoAdapter must live in adapters/secondary/mock/ only.\n"
        f"Never reference DemoAdapter in production code paths."
    )

# ─────────────────────────────────────────────
# RULE 11 — Demo mode: never hardcoded
# ─────────────────────────────────────────────
HARDCODED_DEMO = [
    "DEMO_MODE = True",
    "DEMO_MODE = true",
    "demo_mode = True",
    "demo_mode = true",
]

if contains_any(content, HARDCODED_DEMO) and "config.py" not in str_path:
    block(
        "DEMO MODE VIOLATION — hardcoded demo mode",
        f"Demo mode must NEVER be hardcoded.\n"
        f"Use: DEMO_MODE = os.environ.get('HEXAWYN_DEMO_MODE', 'false').lower() == 'true'\n"
        f"Only in config.py."
    )

# ─────────────────────────────────────────────
# RULE 12 — TypedDict: no dict[str, Any] return types in use cases
# ─────────────────────────────────────────────
GENERIC_DICT_PATTERNS = [
    "dict[str, Any]",
    "dict[str, any]",
    "dict[str, object]",
    "Dict[str, Any]",
    "Dict[str, any]",
    "Dict[str, object]",
    "-> dict:",
    "-> Dict:",
]

USE_CASE_LAYERS = (
    "application/use_case/",
    "application/ports/driving/",
    "application/service/",
    "domain/services/",
)

if any(layer in str_path for layer in USE_CASE_LAYERS) and not is_test_file(path):
    match = contains_any(content, GENERIC_DICT_PATTERNS)
    if match:
        block(
            "TYPING VIOLATION — generic dict return type",
            f"'{match}' is forbidden in '{path}'.\n"
            f"Never use dict[str, Any] or dict[str, object] as a return type.\n"
            f"Define a TypedDict in application/ports/driving/xxx_response.py:\n"
            f"  class MyResponse(TypedDict):\n"
            f"      field_name: str\n"
            f"      other_field: int"
        )

# ─────────────────────────────────────────────
# RULE 13 — SQL: no inline SQL in Python
# All SQL must live in sql/ folders as .sql files
# ─────────────────────────────────────────────
SQL_INLINE_PATTERNS = [
    '"""SELECT', "'''SELECT",
    '"""INSERT', "'''INSERT",
    '"""UPDATE', "'''UPDATE",
    '"""DELETE', "'''DELETE",
    '"""CREATE', "'''CREATE",
    '"SELECT ',  "'SELECT ",
    '"INSERT ',  "'INSERT ",
    '"UPDATE ',  "'UPDATE ",
    '"DELETE ',  "'DELETE ",
]

INFRA_SQL_LAYERS = ("infrastructure/", "adapters/")

if any(layer in str_path for layer in INFRA_SQL_LAYERS) and not is_test_file(path):
    match = contains_any(content, SQL_INLINE_PATTERNS)
    if match:
        block(
            "SQL VIOLATION — inline SQL in Python",
            f"'{match}' detected in '{path}'.\n"
            f"All SQL must live in sql/ folder as .sql files.\n"
            f"Use a helper to load the query:\n"
            f"  query = load_sql('get_incidents.sql')\n"
            f"  self.conn.execute(query, [param1, param2])"
        )

# ─────────────────────────────────────────────
# RULE 14 — LangGraph: no direct LLM provider imports in nodes
# Only the Provider layer knows LLM implementations
# ─────────────────────────────────────────────
LLM_PROVIDER_IMPORTS = [
    "from langchain_anthropic", "import langchain_anthropic",
    "from langchain_openai",    "import langchain_openai",
    "from langchain_ollama",    "import langchain_ollama",
    "from anthropic",           "import anthropic",
    "from openai",              "import openai",
    "ChatOllama",
    "ChatAnthropic",
    "ChatOpenAI",
    "AzureChatOpenAI",
]

if "lang_graph/nodes/" in str_path and not is_test_file(path):
    match = contains_any(content, LLM_PROVIDER_IMPORTS)
    if match:
        block(
            "LANGGRAPH VIOLATION — LLM provider imported in node",
            f"'{match}' is forbidden in lang_graph/nodes/.\n"
            f"LangGraph nodes must NEVER import LLM providers directly.\n"
            f"Only the Provider layer (runtime/providers/) knows LLM implementations.\n"
            f"Inject the LLM via dependency injection:\n"
            f"  def __init__(self, llm: BaseChatModel): ...\n"
            f"Never: from langchain_anthropic import ChatAnthropic"
        )
        
# ─────────────────────────────────────────────
# RULE 15 — Imports: module-level only, no function-scoped imports
# ─────────────────────────────────────────────
IMPORT_ALLOWED_LAYERS = (
    "domain/",
    "application/",
    "adapters/",
    "lang_graph/",
    "infrastructure/",
)

# Directories where optional dependencies are legitimately imported lazily.
# These are infra-heavy adapters that import cloud SDKs, kubernetes, etc.
LAZY_IMPORT_EXEMPT_PATHS = (
    "adapters/secondary/aws/",
    "adapters/secondary/azure/",
    "adapters/secondary/gcp/",
    "adapters/secondary/datadog/",
    "adapters/secondary/openshift/",
    "adapters/secondary/gitops/",
    "adapters/secondary/vanilla/",
    "adapters/secondary/slack/",
    "adapters/primary/slack/",
    "domain/services/schedule/",
    "infrastructure/config/",
)

# Known optional dependencies — always allowed to be imported lazily
# regardless of file path. These are optional extras or platform-specific
# modules that MUST NOT cause ImportError at module level.
OPTIONAL_DEP_PREFIXES = (
    "kubernetes",
    "duckdb",
    "cryptography",
    "boto3",
    "azure",
    "google.cloud",
    "openshift",
    "datadog",
    "winreg",
    "requests",
    "httpx",
)

if (
    path.suffix == ".py"
    and not is_test_file(path)
    and any(layer in str_path for layer in IMPORT_ALLOWED_LAYERS)
    and not any(exempt in str_path for exempt in LAZY_IMPORT_EXEMPT_PATHS)
):
    for i, line in enumerate(content.split("\n"), 1):
        # Indented import → inside a function, method or conditional block
        if not line.startswith((" ", "\t")):
            continue

        stripped = line.strip()
        if not (stripped.startswith("import ") or stripped.startswith("from ")):
            continue

        # Allow explicit escape hatch for circular imports
        if "hexa-lazy-import" in line:
            continue

        # Skip lines inside string literals (docstring continuations)
        if '"""' in line or "'''" in line:
            continue

        # Allow lazy imports of known optional dependencies
        if _is_optional_dep_import(stripped):
            continue

        block(
            "IMPORT VIOLATION — function-scoped import",
            f"Line {i} in '{path}': '{stripped}'\n"
            f"All imports must be declared at module level (PEP 8).\n"
            f"Function-scoped imports hide real dependencies and defer "
            f"ImportError to runtime.\n"
            f"Exceptions:\n"
            f"  - optional cloud SDKs in adapters/secondary/<provider>/\n"
            f"  - known optional deps: kubernetes, duckdb, cryptography, "
            f"boto3, azure, etc.\n"
            f"  - circular import breaks — add '# noqa: hexa-lazy-import' "
            f"with a comment explaining why"
        )

# ─────────────────────────────────────────────
# All checks passed
# ─────────────────────────────────────────────
print(json.dumps({"decision": "approve"}))
sys.exit(0)
