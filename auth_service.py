"""
auth_service.py - Serviço de Autenticação e Controle de Acesso

Gerencia login, senha, sessões, rate limiting e auditoria de acesso.
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_USERS_FILE = Path(__file__).parent / "cache" / "users.json"
DEFAULT_AUDIT_FILE = Path(__file__).parent / "logs" / "audit.json"


def _hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
    """
    Gera hash de senha usando PBKDF2-SHA256.

    Args:
        password: Senha em texto plano
        salt: Salt opcional (se None, gera um novo)

    Returns:
        Tuple (hash_hex, salt_hex)
    """
    if salt is None:
        salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return key.hex(), salt.hex()


class AuthService:
    """
    Serviço de autenticação com gerenciamento de usuários, sessões e rate limiting.
    """

    def __init__(
        self,
        users_file: Optional[str] = None,
        audit_file: Optional[str] = None,
        max_login_attempts: int = 5,
        lockout_minutes: int = 15,
        rate_limit_per_minute: int = 10,
    ):
        """
        Inicializa o serviço de autenticação.

        Args:
            users_file: Caminho do arquivo JSON de usuários
            audit_file: Caminho do arquivo JSON de auditoria
            max_login_attempts: Máximo de tentativas de login antes de bloqueio
            lockout_minutes: Minutos de bloqueio após exceder tentativas
            rate_limit_per_minute: Máximo de análises por minuto por usuário
        """
        self.users_file = Path(users_file or DEFAULT_USERS_FILE)
        self.audit_file = Path(audit_file or DEFAULT_AUDIT_FILE)
        self.max_login_attempts = max_login_attempts
        self.lockout_minutes = lockout_minutes
        self.rate_limit_per_minute = rate_limit_per_minute

        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)

        self.users: Dict[str, Dict[str, Any]] = {}
        self._load_users()
        self._ensure_admin()

    def _load_users(self) -> None:
        """Carrega usuários do arquivo JSON."""
        try:
            if self.users_file.exists():
                with open(self.users_file, "r", encoding="utf-8") as f:
                    self.users = json.load(f)
                logger.info(f"{len(self.users)} usuário(s) carregado(s)")
            else:
                self.users = {}
                self._save_users()
        except Exception as e:
            logger.error(f"Erro ao carregar usuários: {e}")
            self.users = {}

    def _save_users(self) -> None:
        """Salva usuários no arquivo JSON."""
        try:
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar usuários: {e}")

    def _ensure_admin(self) -> None:
        """Garante que existe um usuário admin padrão."""
        if "admin" not in self.users:
            hash_key, salt = _hash_password("admin123")
            self.users["admin"] = {
                "password_hash": hash_key,
                "salt": salt,
                "role": "admin",
                "created_at": datetime.now().isoformat(),
                "active": True,
                "login_attempts": 0,
                "locked_until": None,
            }
            self._save_users()
            logger.info("Usuário admin padrão criado (admin / admin123)")

    def create_user(
        self,
        username: str,
        password: str,
        role: str = "user",
    ) -> Tuple[bool, str]:
        """
        Cria um novo usuário.

        Args:
            username: Nome de usuário
            password: Senha em texto plano
            role: Função do usuário (admin, lawyer, intern)

        Returns:
            Tuple (sucesso, mensagem)
        """
        if not username or not password:
            return False, "Usuário e senha são obrigatórios"

        if len(password) < 6:
            return False, "Senha deve ter no mínimo 6 caracteres"

        if username in self.users:
            return False, f"Usuário '{username}' já existe"

        valid_roles = {"admin", "lawyer", "intern"}
        if role not in valid_roles:
            return False, f"Role inválida. Opções: {valid_roles}"

        hash_key, salt = _hash_password(password)
        self.users[username] = {
            "password_hash": hash_key,
            "salt": salt,
            "role": role,
            "created_at": datetime.now().isoformat(),
            "active": True,
            "login_attempts": 0,
            "locked_until": None,
        }
        self._save_users()
        logger.info(f"Usuário criado: {username} ({role})")
        return True, f"Usuário '{username}' criado com sucesso"

    def authenticate(
        self, username: str, password: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Autentica um usuário.

        Args:
            username: Nome de usuário
            password: Senha em texto plano

        Returns:
            Tuple (autenticado, mensagem, dados_do_usuario)
        """
        if username not in self.users:
            self._log_audit(username, "LOGIN_FAILED", "Usuário não encontrado")
            return False, "Usuário ou senha inválidos", None

        user = self.users[username]

        if not user.get("active", True):
            self._log_audit(username, "LOGIN_FAILED", "Conta desativada")
            return False, "Conta desativada. Contate o administrador", None

        if user.get("locked_until"):
            lock_time = datetime.fromisoformat(user["locked_until"])
            if lock_time > datetime.now():
                remaining = (lock_time - datetime.now()).seconds // 60
                self._log_audit(username, "LOGIN_BLOCKED", f"Conta bloqueada por {remaining}min")
                return False, f"Conta bloqueada. Tente novamente em {remaining} minutos", None
            else:
                user["locked_until"] = None
                user["login_attempts"] = 0

        stored_hash = user.get("password_hash", "")
        stored_salt = bytes.fromhex(user.get("salt", ""))

        computed_hash, _ = _hash_password(password, stored_salt)

        if computed_hash == stored_hash:
            user["login_attempts"] = 0
            user["locked_until"] = None
            self._save_users()

            user_data = {
                "username": username,
                "role": user["role"],
                "created_at": user["created_at"],
                "login_time": datetime.now().isoformat(),
            }
            self._log_audit(username, "LOGIN_SUCCESS", "")
            logger.info(f"Login bem-sucedido: {username}")
            return True, "Login realizado com sucesso", user_data
        else:
            user["login_attempts"] = user.get("login_attempts", 0) + 1
            if user["login_attempts"] >= self.max_login_attempts:
                user["locked_until"] = (
                    datetime.now() + timedelta(minutes=self.lockout_minutes)
                ).isoformat()
                self._save_users()
                self._log_audit(username, "ACCOUNT_LOCKED", "Múltiplas tentativas falhas")
                return False, f"Conta bloqueada por {self.lockout_minutes} minutos após {self.max_login_attempts} tentativas", None
            self._save_users()
            self._log_audit(username, "LOGIN_FAILED", "Senha incorreta")
            remaining = self.max_login_attempts - user["login_attempts"]
            return False, f"Senha inválida. {remaining} tentativa(s) restante(s)", None

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Retorna dados de um usuário (sem hash da senha)."""
        if username not in self.users:
            return None
        user = self.users[username]
        return {
            "username": username,
            "role": user.get("role"),
            "created_at": user.get("created_at"),
            "active": user.get("active", True),
        }

    def list_users(self) -> List[Dict[str, Any]]:
        """Lista todos os usuários (sem hashes)."""
        return [self.get_user(u) for u in self.users]

    def delete_user(self, username: str) -> Tuple[bool, str]:
        """Remove um usuário."""
        if username == "admin":
            return False, "Não é possível remover o usuário admin"
        if username not in self.users:
            return False, f"Usuário '{username}' não encontrado"
        del self.users[username]
        self._save_users()
        logger.info(f"Usuário removido: {username}")
        return True, f"Usuário '{username}' removido"

    def change_password(
        self, username: str, old_password: str, new_password: str
    ) -> Tuple[bool, str]:
        """Altera a senha de um usuário."""
        if username not in self.users:
            return False, "Usuário não encontrado"

        authenticated, _, _ = self.authenticate(username, old_password)
        if not authenticated:
            return False, "Senha atual incorreta"

        if len(new_password) < 6:
            return False, "Nova senha deve ter no mínimo 6 caracteres"

        hash_key, salt = _hash_password(new_password)
        self.users[username]["password_hash"] = hash_key
        self.users[username]["salt"] = salt
        self._save_users()
        logger.info(f"Senha alterada: {username}")
        return True, "Senha alterada com sucesso"

    def check_rate_limit(self, username: str) -> bool:
        """
        Verifica se o usuário excedeu o limite de requisições por minuto.

        Args:
            username: Nome do usuário

        Returns:
            True se permitido, False se excedeu o limite
        """
        audit = self._load_audit()
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        recent = [
            entry
            for entry in audit
            if entry.get("user") == username
            and entry.get("action") == "ANALYSIS_REQUEST"
            and datetime.fromisoformat(entry["timestamp"]) > one_minute_ago
        ]

        return len(recent) < self.rate_limit_per_minute

    def _load_audit(self) -> List[Dict]:
        """Carrega log de auditoria."""
        try:
            if self.audit_file.exists():
                with open(self.audit_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _save_audit(self, audit: List[Dict]) -> None:
        """Salva log de auditoria (mantém últimas 1000 entradas)."""
        try:
            audit = audit[-1000:]
            with open(self.audit_file, "w", encoding="utf-8") as f:
                json.dump(audit, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar auditoria: {e}")

    def _log_audit(self, username: str, action: str, details: str) -> None:
        """Registra uma ação de auditoria."""
        audit = self._load_audit()
        audit.append(
            {
                "user": username,
                "action": action,
                "details": details,
                "timestamp": datetime.now().isoformat(),
                "ip": "local",
            }
        )
        self._save_audit(audit)

    def log_analysis_request(self, username: str, contract_name: str) -> None:
        """Registra uma solicitação de análise no log de auditoria."""
        self._log_audit(username, "ANALYSIS_REQUEST", f"Contrato: {contract_name}")

    def get_audit_log(
        self, username: Optional[str] = None, limit: int = 100
    ) -> List[Dict]:
        """
        Retorna o log de auditoria, opcionalmente filtrado por usuário.

        Args:
            username: Filtrar por usuário (None = todos)
            limit: Número máximo de registros

        Returns:
            Lista de registros de auditoria
        """
        audit = self._load_audit()
        if username:
            audit = [e for e in audit if e.get("user") == username]
        return audit[-limit:]

    def google_login_url(self, redirect_uri: str) -> str:
        """Gera URL de login OAuth do Google."""
        from urllib.parse import urlencode

        client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        if not client_id:
            return ""

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    def google_callback(self, code: str, redirect_uri: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Processa o callback OAuth do Google.

        Args:
            code: Código de autorização do Google
            redirect_uri: URI de redirecionamento usada

        Returns:
            Tuple (sucesso, mensagem, dados_do_usuario)
        """
        import requests

        client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            return False, "Google OAuth não configurado", None

        try:
            token_resp = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
                timeout=15,
            )

            if token_resp.status_code != 200:
                return False, "Erro ao validar código Google", None

            tokens = token_resp.json()
            access_token = tokens.get("access_token")

            user_resp = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )

            if user_resp.status_code != 200:
                return False, "Erro ao obter dados do usuário Google", None

            google_user = user_resp.json()
            email = google_user.get("email", "")
            name = google_user.get("name", email)

            if not email:
                return False, "Email não encontrado na conta Google", None

            username = email.split("@")[0]

            if username not in self.users:
                import secrets

                random_pass = secrets.token_hex(16)
                hash_key, salt = _hash_password(random_pass)
                self.users[username] = {
                    "password_hash": hash_key,
                    "salt": salt,
                    "role": "lawyer",
                    "created_at": datetime.now().isoformat(),
                    "active": True,
                    "login_attempts": 0,
                    "locked_until": None,
                    "google_email": email,
                    "google_name": name,
                }
                self._save_users()
                logger.info(f"Usuário Google criado: {username} ({email})")
            else:
                self.users[username]["google_email"] = email
                self.users[username]["google_name"] = name
                self._save_users()

            user_data = {
                "username": username,
                "role": self.users[username]["role"],
                "created_at": self.users[username]["created_at"],
                "login_time": datetime.now().isoformat(),
                "google_email": email,
            }
            self._log_audit(username, "LOGIN_GOOGLE_SUCCESS", email)
            logger.info(f"Login Google bem-sucedido: {username}")
            return True, "Login Google realizado com sucesso", user_data

        except Exception as e:
            logger.error(f"Erro no callback Google: {e}")
            return False, f"Erro na autenticação Google: {str(e)}", None


if __name__ == "__main__":
    print("=== Teste do AuthService ===\n")

    auth = AuthService()

    print("1. Criando usuários de teste...")
    success, msg = auth.create_user("advogado1", "senha123", role="lawyer")
    print(f"   {msg}")

    success, msg = auth.create_user("estagiario1", "senha123", role="intern")
    print(f"   {msg}")

    print("\n2. Listando usuários:")
    for user in auth.list_users():
        print(f"   - {user['username']} ({user['role']})")

    print("\n3. Testando login válido...")
    ok, msg, data = auth.authenticate("advogado1", "senha123")
    print(f"   {'OK' if ok else 'ERRO'}: {msg}")

    print("\n4. Testando login inválido...")
    ok, msg, data = auth.authenticate("advogado1", "errada")
    print(f"   {'OK' if ok else 'ERRO'}: {msg}")

    print("\n5. Auditoria:")
    for entry in auth.get_audit_log(limit=5):
        print(f"   [{entry['timestamp']}] {entry['user']} - {entry['action']}")
