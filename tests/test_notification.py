"""
Testes para o módulo notification_service.py.
"""
import os
import sys
import tempfile
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from notification_service import NotificationService


def test_generate_whatsapp_link():
    """Deve gerar um link WhatsApp válido."""
    notifier = NotificationService()
    link = notifier.generate_whatsapp_link("Resumo de teste", "contrato.pdf")
    assert link.startswith("https://api.whatsapp.com/send?text=")


def test_create_share_link():
    """Deve criar um link compartilhável com token."""
    notifier = NotificationService()
    ok, data = notifier.create_share_link(
        "Análise de teste", "contrato.pdf", expires_hours=1
    )
    assert ok is True
    assert "token" in data
    assert len(data["token"]) == 16
    assert data.get("has_password") is False


def test_create_share_link_with_password():
    """Deve criar link com proteção de senha."""
    notifier = NotificationService()
    ok, data = notifier.create_share_link(
        "Análise de teste", "contrato.pdf", expires_hours=1, password="123456"
    )
    assert ok is True
    assert data.get("has_password") is True


def test_get_shared_analysis_valid():
    """Deve recuperar análise compartilhada com token válido."""
    notifier = NotificationService()
    ok, data = notifier.create_share_link("Meu texto analisado", "contrato.pdf")
    valid, msg, analysis = notifier.get_shared_analysis(data["token"])
    assert valid is True
    assert analysis is not None
    assert "Meu texto" in analysis["analysis_text"]


def test_get_shared_analysis_expired():
    """Deve rejeitar token expirado."""
    notifier = NotificationService()
    ok, data = notifier.create_share_link(
        "Conteúdo", "teste.pdf", expires_hours=-1
    )
    valid, msg, analysis = notifier.get_shared_analysis(data["token"])
    assert valid is False


def test_get_shared_analysis_password_required():
    """Deve exigir senha para links protegidos."""
    notifier = NotificationService()
    ok, data = notifier.create_share_link(
        "Conteúdo secreto", "teste.pdf", password="123456"
    )
    valid, msg, analysis = notifier.get_shared_analysis(data["token"])
    assert valid is False


def test_get_shared_analysis_password_correct():
    """Deve aceitar senha correta."""
    notifier = NotificationService()
    ok, data = notifier.create_share_link(
        "Conteúdo secreto", "teste.pdf", password="123456"
    )
    valid, msg, analysis = notifier.get_shared_analysis(
        data["token"], password="123456"
    )
    assert valid is True


def test_get_shared_analysis_wrong_password():
    """Deve rejeitar senha incorreta."""
    notifier = NotificationService()
    ok, data = notifier.create_share_link(
        "Secreto", "teste.pdf", password="senha_certa"
    )
    valid, msg, analysis = notifier.get_shared_analysis(
        data["token"], password="senha_errada"
    )
    assert valid is False


def test_get_shared_analysis_nonexistent():
    """Deve rejeitar token inexistente."""
    notifier = NotificationService()
    valid, msg, analysis = notifier.get_shared_analysis("token_inexistente123")
    assert valid is False


def test_cleanup_expired_shares():
    """Deve limpar links expirados sem erro."""
    notifier = NotificationService()
    removed = notifier.cleanup_expired_shares()
    assert isinstance(removed, int)
    assert removed >= 0


def test_notification_initialization():
    """Deve inicializar o serviço sem erros."""
    notifier = NotificationService()
    assert notifier is not None
    assert hasattr(notifier, "send_email")
    assert hasattr(notifier, "create_share_link")
    assert hasattr(notifier, "generate_qr_code")
    assert hasattr(notifier, "send_whatsapp_text")
    assert hasattr(notifier, "send_whatsapp_document")
    assert hasattr(notifier, "cleanup_expired_shares")


def test_qr_code_generation():
    """Deve gerar QR Code quando disponível."""
    notifier = NotificationService()
    qr = notifier.generate_qr_code("https://trust-corp.com")
    if qr is not None:
        assert qr.getbuffer().nbytes > 0


if __name__ == "__main__":
    test_generate_whatsapp_link()
    test_create_share_link()
    test_create_share_link_with_password()
    test_get_shared_analysis_valid()
    test_get_shared_analysis_expired()
    test_get_shared_analysis_password_required()
    test_get_shared_analysis_password_correct()
    test_get_shared_analysis_wrong_password()
    test_get_shared_analysis_nonexistent()
    test_cleanup_expired_shares()
    test_notification_initialization()
    test_qr_code_generation()
    print("Todos os testes de notification_service.py passaram!")
