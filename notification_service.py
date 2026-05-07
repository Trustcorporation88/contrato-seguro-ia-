"""
notification_service.py - Serviço de Notificações e Compartilhamento

Envia análises por email, WhatsApp Business API, gera links compartilháveis
com senha e QR Codes.
"""

import hashlib
import json
import logging
import os
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth

from config import compute_hash

logger = logging.getLogger(__name__)

SHARE_DIR = Path(__file__).parent / "cache" / "shares"

try:
    import qrcode

    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    logger.info("qrcode não instalado. QR Codes desabilitados.")


class NotificationService:
    """Serviço de notificações por email, WhatsApp e links compartilháveis."""

    def __init__(
        self,
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        sender_email: str = "",
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.sender_email = sender_email or os.getenv("SENDER_EMAIL", "")

        SHARE_DIR.mkdir(parents=True, exist_ok=True)

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        pdf_buffer: Optional[BytesIO] = None,
        pdf_filename: str = "analise.pdf",
        html: bool = False,
    ) -> Tuple[bool, str]:
        """
        Envia email com análise, opcionalmente com PDF anexo.

        Args:
            to_email: Email do destinatário
            subject: Assunto do email
            body: Corpo do email
            pdf_buffer: Buffer do PDF para anexar (opcional)
            pdf_filename: Nome do arquivo PDF anexo
            html: Se True, body é interpretado como HTML

        Returns:
            Tuple (sucesso, mensagem)
        """
        if not self.smtp_user or not self.smtp_password:
            return False, "SMTP não configurado. Configure SMTP_USER e SMTP_PASSWORD no .env"

        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email or self.smtp_user
            msg["To"] = to_email
            msg["Subject"] = subject

            content_type = "html" if html else "plain"
            msg.attach(MIMEText(body, content_type, "utf-8"))

            if pdf_buffer:
                pdf_buffer.seek(0)
                attachment = MIMEApplication(pdf_buffer.read(), _subtype="pdf")
                attachment.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=pdf_filename,
                )
                msg.attach(attachment)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email enviado para {to_email}")
            return True, f"Email enviado com sucesso para {to_email}"

        except smtplib.SMTPAuthenticationError:
            logger.error("Erro de autenticacao SMTP")
            return False, "Erro de autenticação SMTP. Verifique usuário e senha"
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False, "Erro ao enviar email. Tente novamente mais tarde."

    def generate_whatsapp_link(self, texto_resumo: str, contract_name: str) -> str:
        """
        Gera link para compartilhamento via WhatsApp.

        Args:
            texto_resumo: Resumo da análise (até 20 linhas)
            contract_name: Nome do contrato

        Returns:
            URL do WhatsApp API
        """
        mensagem = (
            "📊 ANÁLISE DE CONTRATO - TRUST CORPORATION\n"
            f"📄 Contrato: {contract_name}\n\n"
            "⚠️ RESUMO DE RISCOS:\n"
            f"{texto_resumo}\n\n"
            "✅ Análise completa na plataforma TRUST CORPORATION"
        )

        mensagem_truncada = mensagem[:4000]
        encoded = quote(mensagem_truncada)
        return f"https://api.whatsapp.com/send?text={encoded}"

    def create_share_link(
        self,
        analysis_text: str,
        contract_name: str,
        expires_hours: int = 24,
        password: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Cria um link compartilhável temporário para a análise.

        Args:
            analysis_text: Texto da análise
            contract_name: Nome do contrato
            expires_hours: Horas até expirar o link
            password: Senha opcional para acessar

        Returns:
            Tuple (sucesso, dados_do_link)
        """
        try:
            timestamp = datetime.now().isoformat()
            token = compute_hash(
                f"{contract_name}{timestamp}{os.urandom(8).hex()}"
            )[:16]

            share_data = {
                "token": token,
                "contract_name": contract_name,
                "analysis_text": analysis_text[:10000],
                "created_at": timestamp,
                "expires_at": (datetime.now() + timedelta(hours=expires_hours)).isoformat(),
                "password_hash": (
                    hashlib.sha256(password.encode()).hexdigest()
                    if password
                    else None
                ),
                "accessed": 0,
            }

            share_file = SHARE_DIR / f"{token}.json"
            with open(share_file, "w", encoding="utf-8") as f:
                json.dump(share_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Link compartilhável criado: {token}")
            return True, {
                "token": token,
                "expires_in_hours": expires_hours,
                "has_password": password is not None,
            }

        except Exception as e:
            logger.error(f"Erro ao criar link: {e}")
            return False, {"error": "Erro ao criar link compartilhável"}

    def get_shared_analysis(
        self, token: str, password: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Recupera uma análise compartilhada pelo token.

        Args:
            token: Token do link compartilhável
            password: Senha (se configurada)

        Returns:
            Tuple (válido, mensagem, dados_da_análise)
        """
        share_file = SHARE_DIR / f"{token}.json"

        if not share_file.exists():
            return False, "Link não encontrado ou expirado", None

        try:
            with open(share_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            expires = datetime.fromisoformat(data["expires_at"])
            if datetime.now() > expires:
                share_file.unlink(missing_ok=True)
                return False, "Link expirado", None

            if data["password_hash"]:
                if not password:
                    return False, "Senha necessária para acessar", {"requires_password": True}
                if hashlib.sha256(password.encode()).hexdigest() != data["password_hash"]:
                    return False, "Senha incorreta", None

            data["accessed"] = data.get("accessed", 0) + 1
            with open(share_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True, "Análise recuperada com sucesso", {
                "contract_name": data["contract_name"],
                "analysis_text": data["analysis_text"],
                "created_at": data["created_at"],
            }

        except Exception as e:
            logger.error(f"Erro ao recuperar análise: {e}")
            return False, "Erro ao recuperar análise", None

    def generate_qr_code(
        self, data: str, box_size: int = 10, border: int = 4
    ) -> Optional[BytesIO]:
        """
        Gera QR Code a partir de uma string/dados.

        Args:
            data: Dados para codificar no QR Code
            box_size: Tamanho de cada quadrado
            border: Tamanho da borda

        Returns:
            BytesIO com a imagem PNG do QR Code
        """
        if not QR_AVAILABLE:
            logger.warning("qrcode não instalado")
            return None

        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=box_size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return buf

        except Exception as e:
            logger.error(f"Erro ao gerar QR Code: {e}")
            return None

    def upload_pdf_to_cloud(self, pdf_buffer: BytesIO, filename: str) -> Tuple[bool, str]:
        """
        Faz upload do PDF para um serviço gratuito e retorna o link público.
        O cliente pode baixar o PDF diretamente pelo link.

        Args:
            pdf_buffer: Buffer do PDF
            filename: Nome do arquivo

        Returns:
            Tuple (sucesso, url_ou_erro)
        """
        pdf_buffer.seek(0)

        try:
            response = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": (filename, pdf_buffer, "application/pdf")},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                url = data.get("data", {}).get("url", "")
                if url:
                    url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                    logger.info(f"PDF uploaded: {url}")
                    return True, url

            logger.error(f"Upload failed: {response.status_code} {response.text[:200]}")
            return False, f"Erro no upload ({response.status_code})"

        except Exception as e:
            logger.error(f"Erro upload PDF: {e}")
            return False, "Falha no upload do PDF. Tente novamente."

    def _twilio_send(self, to_number: str, body: str, media_url: str = "") -> Tuple[bool, str]:
        """Método interno para envio via Twilio WhatsApp."""
        account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "+14155238886")

        if not account_sid or not auth_token:
            return False, "Twilio não configurada. Configure TWILIO_ACCOUNT_SID e TWILIO_AUTH_TOKEN"

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

        data = {
            "To": f"whatsapp:+{to_number.replace('+', '')}",
            "From": f"whatsapp:{from_number}",
            "Body": body[:1600],
        }

        if media_url:
            data["MediaUrl"] = media_url

        try:
            resp = requests.post(
                url,
                data=data,
                auth=HTTPBasicAuth(account_sid, auth_token),
                timeout=30,
            )

            if resp.status_code in (200, 201):
                logger.info(f"Twilio WhatsApp enviado para {to_number}")
                return True, "Mensagem enviada via Twilio"

            error = resp.json().get("message", resp.text)
            return False, f"Twilio erro: {error[:200]}"

        except Exception as e:
            logger.error(f"Twilio erro: {e}")
            return False, "Falha ao enviar mensagem via Twilio. Tente novamente."

    def send_whatsapp_pdf_twilio(
        self, to_number: str, pdf_buffer: BytesIO, filename: str,
        summary: str = "", contract_name: str = "",
    ) -> Tuple[bool, str]:
        """
        Fluxo completo Twilio: upload PDF para nuvem + envia WhatsApp com link.

        Args:
            to_number: Número do destinatário (ex: 5514996919098)
            pdf_buffer: Buffer do PDF
            filename: Nome do arquivo PDF
            summary: Resumo dos riscos (opcional)
            contract_name: Nome do contrato (opcional)

        Returns:
            Tuple (sucesso, mensagem)
        """
        ok, url = self.upload_pdf_to_cloud(pdf_buffer, filename)
        if not ok:
            return False, f"Falha ao fazer upload do PDF: {url}"

        header = (
            f"📊 *TRUST CORPORATION - Análise de Contrato*\n"
            f"📄 *{contract_name}*\n\n"
        )

        remaining = 1500 - len(header) - len(url) - 30

        if summary and remaining > 200:
            summary_short = summary[:remaining].strip()
            last_nl = summary_short.rfind("\n")
            if last_nl > remaining - 100:
                summary_short = summary_short[:last_nl].strip()

            body = header
            body += f"⚠️ *Principais riscos:*\n{summary_short}\n\n"
        else:
            body = header
            body += "⚠️ *Verifique os principais riscos identificados.*\n\n"

        body += (
            f"📎 *PDF completo:* {url}\n\n"
            f"✅ TRUST CORPORATION - Contrato Seguro IA"
        )

        return self._twilio_send(to_number, body[:1600], media_url=url)

    def cleanup_expired_shares(self) -> int:
        """Remove links compartilháveis expirados. Retorna quantidade removida."""
        removed = 0
        if not SHARE_DIR.exists():
            return 0

        for share_file in SHARE_DIR.glob("*.json"):
            try:
                with open(share_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                expires = datetime.fromisoformat(data.get("expires_at", "2000-01-01"))
                if datetime.now() > expires:
                    share_file.unlink()
                    removed += 1
            except Exception:
                pass

        logger.info(f"{removed} links expirados removidos")
        return removed

    def send_whatsapp_text(
        self, phone_number: str, message: str
    ) -> Tuple[bool, str]:
        """
        Envia mensagem de texto via WhatsApp Cloud API.

        Requer WHATSAPP_PHONE_NUMBER_ID e WHATSAPP_ACCESS_TOKEN no .env
        (Meta Business Platform).

        Args:
            phone_number: Número do destinatário (ex: 5511999999999)
            message: Texto da mensagem

        Returns:
            Tuple (sucesso, resposta)
        """
        phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")

        if not phone_number_id or not access_token:
            return False, "WhatsApp Cloud API não configurada. Configure WHATSAPP_PHONE_NUMBER_ID e WHATSAPP_ACCESS_TOKEN no .env"

        url = f"https://graph.facebook.com/v25.0/{phone_number_id}/messages"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {"preview_url": False, "body": message[:4000]},
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            data = response.json()
            if response.status_code == 200 or response.status_code == 201:
                logger.info(f"WhatsApp texto enviado para {phone_number}")
                return True, "Mensagem enviada com sucesso"
            else:
                error_msg = data.get("error", {}).get("message", str(data))
                logger.error(f"Erro WhatsApp: {error_msg}")
                return False, f"Erro: {error_msg}"
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp: {e}")
            return False, "Falha ao enviar mensagem via WhatsApp. Tente novamente."

    def send_whatsapp_document(
        self, phone_number: str, pdf_buffer: BytesIO, filename: str,
        caption: str = "",
    ) -> Tuple[bool, str]:
        """
        Envia documento PDF via WhatsApp Cloud API.

        Requer WHATSAPP_PHONE_NUMBER_ID e WHATSAPP_ACCESS_TOKEN no .env.

        Args:
            phone_number: Número do destinatário (ex: 5511999999999)
            pdf_buffer: Buffer do PDF a enviar
            filename: Nome do arquivo
            caption: Legenda opcional

        Returns:
            Tuple (sucesso, resposta)
        """
        phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")

        if not phone_number_id or not access_token:
            return False, "WhatsApp Cloud API não configurada"

        pdf_buffer.seek(0)
        pdf_data = pdf_buffer.read()
        pdf_size_mb = len(pdf_data) / (1024 * 1024)

        if pdf_size_mb > 5:
            return False, f"PDF muito grande ({pdf_size_mb:.1f}MB). Máximo: 5MB para WhatsApp"

        upload_url = f"https://graph.facebook.com/v25.0/{phone_number_id}/media"

        try:
            upload_response = requests.post(
                upload_url,
                headers={"Authorization": f"Bearer {access_token}"},
                files={
                    "file": (filename, pdf_data, "application/pdf"),
                    "messaging_product": (None, "whatsapp"),
                },
                timeout=30,
            )

            if upload_response.status_code not in (200, 201):
                error = upload_response.json().get("error", {}).get("message", "Erro no upload")
                return False, f"Erro ao enviar PDF: {error}"

            media_id = upload_response.json().get("id", "")

            send_url = f"https://graph.facebook.com/v25.0/{phone_number_id}/messages"

            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone_number,
                "type": "document",
                "document": {
                    "id": media_id,
                    "filename": filename,
                    "caption": caption[:1024] if caption else "Analise de Contrato - TRUST CORPORATION",
                },
            }

            send_response = requests.post(
                send_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )

            if send_response.status_code in (200, 201):
                logger.info(f"WhatsApp PDF enviado para {phone_number}: {filename}")
                return True, "PDF enviado com sucesso via WhatsApp"
            else:
                error = send_response.json().get("error", {}).get("message", "Erro")
                return False, f"Erro ao enviar: {error}"

        except Exception as e:
            logger.error(f"Erro ao enviar PDF via WhatsApp: {e}")
            return False, "Falha ao enviar PDF via WhatsApp. Tente novamente."


if __name__ == "__main__":
    print("=== Teste do NotificationService ===\n")

    notifier = NotificationService()

    print("1. Teste de link WhatsApp...")
    url = notifier.generate_whatsapp_link("Resumo de teste...", "contrato.pdf")
    print(f"   URL: {url[:80]}...")

    print("\n2. Teste de link compartilhável...")
    ok, data = notifier.create_share_link(
        "Análise de teste...",
        "contrato_teste.pdf",
        expires_hours=1,
        password="123456",
    )
    print(f"   Criado: {ok} - Token: {data.get('token', 'N/A')}")

    if ok:
        print("\n3. Acessando análise compartilhada...")
        valid, msg, analysis = notifier.get_shared_analysis(data["token"])
        print(f"   Sem senha: {valid} - {msg}")

        valid, msg, analysis = notifier.get_shared_analysis(data["token"], password="123456")
        print(f"   Com senha: {valid} - {msg}")

    print("\n4. Teste de QR Code...")
    qr_buf = notifier.generate_qr_code("https://trust-corporation.com")
    if qr_buf:
        print(f"   QR Code gerado: {qr_buf.getbuffer().nbytes} bytes")
    else:
        print("   QR Code não disponível (qrcode não instalado)")

    print("\n5. Limpando links expirados...")
    removed = notifier.cleanup_expired_shares()
    print(f"   {removed} link(s) removido(s)")
