"""Tests for the registry (adapter factories + pack registration)."""

from hexagents_cloud.adapters.primary.registry import (
    build_approbation_adapter,
    build_audit_adapter,
    build_k8s_adapter,
    build_notification_adapter,
    build_proposal_store_adapter,
    register,
)
from hexagents_cloud.application.ports_closed import (
    ApprobationPort,
    AuditStorePort,
    FixProposalStorePort,
    K8sPort,
    NotificationPort,
)


def test_build_k8s_adapter_returns_k8s_port() -> None:
    assert isinstance(build_k8s_adapter(), K8sPort)


def test_build_audit_adapter_returns_audit_port() -> None:
    assert isinstance(build_audit_adapter(), AuditStorePort)


def test_build_notification_adapter_returns_notification_port() -> None:
    assert isinstance(build_notification_adapter(), NotificationPort)


def test_build_approbation_adapter_returns_approbation_port() -> None:
    assert isinstance(build_approbation_adapter(), ApprobationPort)


def test_build_proposal_store_adapter_returns_store_port() -> None:
    assert isinstance(build_proposal_store_adapter(), FixProposalStorePort)


def test_register_returns_registered_packs() -> None:
    result = register()
    assert "cloud.actions.propose" in result
    assert "cloud.actions.approve" in result
    assert "cloud.actions.apply" in result
    assert "cloud.actions.rollback" in result
