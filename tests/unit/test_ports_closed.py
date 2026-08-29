"""Tests for the closed ports (inbound + outbound) of the action layer."""

import pytest

from hexagents_cloud.application.ports_closed import (
    ApprobationPort,
    AuditStorePort,
    FixProposalStorePort,
    K8sPort,
    NotificationPort,
)


def test_ports_are_abstract() -> None:
    for port_type in (
        ApprobationPort,
        FixProposalStorePort,
        K8sPort,
        AuditStorePort,
        NotificationPort,
    ):
        with pytest.raises(TypeError):
            port_type()


def test_approbation_port_has_approve() -> None:
    assert hasattr(ApprobationPort, "approve")


def test_proposal_store_port_has_load_and_save() -> None:
    assert hasattr(FixProposalStorePort, "load")
    assert hasattr(FixProposalStorePort, "save")


def test_k8s_port_has_apply_verify_restore() -> None:
    assert hasattr(K8sPort, "apply")
    assert hasattr(K8sPort, "verify")
    assert hasattr(K8sPort, "restore")


def test_audit_port_has_append() -> None:
    assert hasattr(AuditStorePort, "append")


def test_notification_port_has_notify() -> None:
    assert hasattr(NotificationPort, "notify")
