"""
Testes para o módulo auth_service.py.
"""
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth_service import AuthService, _hash_password


def test_hash_password_deterministic():
    """Hash deve ser reprodutível com o mesmo salt."""
    hash1, salt = _hash_password("minha_senha")
    hash2, _ = _hash_password("minha_senha", bytes.fromhex(salt))
    assert hash1 == hash2


def test_hash_password_different_salts():
    """Mesma senha com salts diferentes deve gerar hashes diferentes."""
    hash1, salt1 = _hash_password("senha")
    hash2, salt2 = _hash_password("senha")
    assert salt1 != salt2
    assert hash1 != hash2


def test_auth_admin_exists():
    """AuthService deve criar usuário admin automaticamente."""
    with tempfile.TemporaryDirectory() as tmpdir:
        users_file = Path(tmpdir) / "users.json"
        audit_file = Path(tmpdir) / "audit.json"
        auth = AuthService(
            users_file=str(users_file),
            audit_file=str(audit_file),
        )
        user = auth.get_user("admin")
        assert user is not None
        assert user["role"] == "admin"


def test_auth_create_user():
    """Deve criar um novo usuário com sucesso."""
    with tempfile.TemporaryDirectory() as tmpdir:
        users_file = Path(tmpdir) / "users.json"
        audit_file = Path(tmpdir) / "audit.json"
        auth = AuthService(
            users_file=str(users_file),
            audit_file=str(audit_file),
        )
        ok, msg = auth.create_user("teste", "senha123", role="lawyer")
        assert ok
        user = auth.get_user("teste")
        assert user is not None
        assert user["role"] == "lawyer"


def test_auth_authenticate_success():
    """Autenticação deve funcionar com credenciais corretas."""
    with tempfile.TemporaryDirectory() as tmpdir:
        users_file = Path(tmpdir) / "users.json"
        audit_file = Path(tmpdir) / "audit.json"
        auth = AuthService(
            users_file=str(users_file),
            audit_file=str(audit_file),
        )
        auth.create_user("user1", "senha123", role="lawyer")
        ok, msg, data = auth.authenticate("user1", "senha123")
        assert ok
        assert data["username"] == "user1"


def test_auth_authenticate_fail():
    """Autenticação deve falhar com credenciais erradas."""
    with tempfile.TemporaryDirectory() as tmpdir:
        users_file = Path(tmpdir) / "users.json"
        audit_file = Path(tmpdir) / "audit.json"
        auth = AuthService(
            users_file=str(users_file),
            audit_file=str(audit_file),
        )
        auth.create_user("user2", "senha123", role="lawyer")
        ok, msg, data = auth.authenticate("user2", "senha_errada")
        assert not ok


def test_auth_duplicate_user():
    """Não deve permitir criar usuário duplicado."""
    with tempfile.TemporaryDirectory() as tmpdir:
        users_file = Path(tmpdir) / "users.json"
        audit_file = Path(tmpdir) / "audit.json"
        auth = AuthService(
            users_file=str(users_file),
            audit_file=str(audit_file),
        )
        auth.create_user("dup", "senha123", role="lawyer")
        ok, msg = auth.create_user("dup", "outra_senha", role="lawyer")
        assert not ok


def test_auth_list_users():
    """Deve listar todos os usuários sem expor senhas."""
    with tempfile.TemporaryDirectory() as tmpdir:
        users_file = Path(tmpdir) / "users.json"
        audit_file = Path(tmpdir) / "audit.json"
        auth = AuthService(
            users_file=str(users_file),
            audit_file=str(audit_file),
        )
        auth.create_user("lista1", "senha123", role="intern")
        users = auth.list_users()
        assert len(users) >= 2  # admin + lista1
        for user in users:
            assert "password_hash" not in user
            assert "salt" not in user


def test_auth_rate_limit():
    """check_rate_limit deve retornar True para usuário sem requisições recentes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        users_file = Path(tmpdir) / "users.json"
        audit_file = Path(tmpdir) / "audit.json"
        auth = AuthService(
            users_file=str(users_file),
            audit_file=str(audit_file),
        )
        assert auth.check_rate_limit("admin") is True


def test_auth_delete_user():
    """Deve remover um usuário com sucesso."""
    with tempfile.TemporaryDirectory() as tmpdir:
        users_file = Path(tmpdir) / "users.json"
        audit_file = Path(tmpdir) / "audit.json"
        auth = AuthService(
            users_file=str(users_file),
            audit_file=str(audit_file),
        )
        auth.create_user("todel", "senha123", role="lawyer")
        ok, msg = auth.delete_user("todel")
        assert ok
        assert auth.get_user("todel") is None


def test_auth_cannot_delete_admin():
    """Não deve permitir remover o admin."""
    with tempfile.TemporaryDirectory() as tmpdir:
        users_file = Path(tmpdir) / "users.json"
        audit_file = Path(tmpdir) / "audit.json"
        auth = AuthService(
            users_file=str(users_file),
            audit_file=str(audit_file),
        )
        ok, msg = auth.delete_user("admin")
        assert not ok


def test_auth_short_password():
    """Não deve permitir criar usuário com senha curta."""
    with tempfile.TemporaryDirectory() as tmpdir:
        users_file = Path(tmpdir) / "users.json"
        audit_file = Path(tmpdir) / "audit.json"
        auth = AuthService(
            users_file=str(users_file),
            audit_file=str(audit_file),
        )
        ok, msg = auth.create_user("short", "12345", role="lawyer")
        assert not ok


def test_google_oauth_configured_and_redirect_resolution():
    """Deve identificar configuração Google e priorizar redirect URI válido."""
    previous_client_id = os.environ.get("GOOGLE_CLIENT_ID")
    previous_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    previous_redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")

    try:
        os.environ["GOOGLE_CLIENT_ID"] = "client-id.apps.googleusercontent.com"
        os.environ["GOOGLE_CLIENT_SECRET"] = "client-secret"
        os.environ["GOOGLE_REDIRECT_URI"] = "https://app.exemplo.com.br/oauth/google/callback"

        with tempfile.TemporaryDirectory() as tmpdir:
            users_file = Path(tmpdir) / "users.json"
            audit_file = Path(tmpdir) / "audit.json"
            auth = AuthService(
                users_file=str(users_file),
                audit_file=str(audit_file),
            )
            assert auth.is_google_oauth_configured() is True
            assert (
                auth.resolve_google_redirect_uri()
                == "https://app.exemplo.com.br/oauth/google/callback"
            )
            assert (
                auth.resolve_google_redirect_uri("https://override.exemplo.com/callback")
                == "https://override.exemplo.com/callback"
            )
    finally:
        if previous_client_id is None:
            os.environ.pop("GOOGLE_CLIENT_ID", None)
        else:
            os.environ["GOOGLE_CLIENT_ID"] = previous_client_id

        if previous_client_secret is None:
            os.environ.pop("GOOGLE_CLIENT_SECRET", None)
        else:
            os.environ["GOOGLE_CLIENT_SECRET"] = previous_client_secret

        if previous_redirect_uri is None:
            os.environ.pop("GOOGLE_REDIRECT_URI", None)
        else:
            os.environ["GOOGLE_REDIRECT_URI"] = previous_redirect_uri


def test_google_login_url_uses_resolved_redirect_uri():
    """URL de login Google deve usar a redirect URI resolvida no parâmetro e no state."""
    previous_client_id = os.environ.get("GOOGLE_CLIENT_ID")
    previous_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    previous_redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")

    try:
        os.environ["GOOGLE_CLIENT_ID"] = "client-id.apps.googleusercontent.com"
        os.environ["GOOGLE_CLIENT_SECRET"] = "client-secret"
        os.environ["GOOGLE_REDIRECT_URI"] = "https://app.exemplo.com.br/oauth/google/callback"

        with tempfile.TemporaryDirectory() as tmpdir:
            users_file = Path(tmpdir) / "users.json"
            audit_file = Path(tmpdir) / "audit.json"
            auth = AuthService(
                users_file=str(users_file),
                audit_file=str(audit_file),
            )
            url = auth.google_login_url()

        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert params["redirect_uri"][0] == "https://app.exemplo.com.br/oauth/google/callback"
        assert params["state"]
    finally:
        if previous_client_id is None:
            os.environ.pop("GOOGLE_CLIENT_ID", None)
        else:
            os.environ["GOOGLE_CLIENT_ID"] = previous_client_id

        if previous_client_secret is None:
            os.environ.pop("GOOGLE_CLIENT_SECRET", None)
        else:
            os.environ["GOOGLE_CLIENT_SECRET"] = previous_client_secret

        if previous_redirect_uri is None:
            os.environ.pop("GOOGLE_REDIRECT_URI", None)
        else:
            os.environ["GOOGLE_REDIRECT_URI"] = previous_redirect_uri


def test_google_callback_prefers_configured_redirect_uri():
    """Troca do code por token deve usar a redirect URI configurada no ambiente."""
    previous_client_id = os.environ.get("GOOGLE_CLIENT_ID")
    previous_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    previous_redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")

    class _DummyResponse:
        status_code = 400
        text = "invalid_grant"

        def json(self):
            return {}

    captured = {}

    def _fake_post(url, data=None, timeout=None):
        captured["url"] = url
        captured["data"] = data
        captured["timeout"] = timeout
        return _DummyResponse()

    try:
        os.environ["GOOGLE_CLIENT_ID"] = "client-id.apps.googleusercontent.com"
        os.environ["GOOGLE_CLIENT_SECRET"] = "client-secret"
        os.environ["GOOGLE_REDIRECT_URI"] = "https://jus.trustcorp.com.br"

        import auth_service as auth_module

        original_requests = auth_module.__dict__.get("requests")

        with tempfile.TemporaryDirectory() as tmpdir:
            users_file = Path(tmpdir) / "users.json"
            audit_file = Path(tmpdir) / "audit.json"
            auth = AuthService(
                users_file=str(users_file),
                audit_file=str(audit_file),
            )

            class _RequestsShim:
                @staticmethod
                def post(url, data=None, timeout=None):
                    return _fake_post(url, data=data, timeout=timeout)

            auth_module.requests = _RequestsShim()
            ok, msg, data = auth.google_callback("codigo-google", "http://localhost:8502")

        assert ok is False
        assert captured["data"]["redirect_uri"] == "https://jus.trustcorp.com.br"
    finally:
        if "auth_module" in locals():
            if original_requests is None:
                auth_module.__dict__.pop("requests", None)
            else:
                auth_module.requests = original_requests

        if previous_client_id is None:
            os.environ.pop("GOOGLE_CLIENT_ID", None)
        else:
            os.environ["GOOGLE_CLIENT_ID"] = previous_client_id

        if previous_client_secret is None:
            os.environ.pop("GOOGLE_CLIENT_SECRET", None)
        else:
            os.environ["GOOGLE_CLIENT_SECRET"] = previous_client_secret

        if previous_redirect_uri is None:
            os.environ.pop("GOOGLE_REDIRECT_URI", None)
        else:
            os.environ["GOOGLE_REDIRECT_URI"] = previous_redirect_uri


def test_google_redirect_ignores_localhost_by_default():
    """Redirect localhost deve ser ignorado em produção."""
    previous_redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")
    previous_allow_local = os.environ.get("ALLOW_LOCALHOST_OAUTH_REDIRECT")

    try:
        os.environ["GOOGLE_REDIRECT_URI"] = "http://localhost:8502"
        os.environ.pop("ALLOW_LOCALHOST_OAUTH_REDIRECT", None)

        with tempfile.TemporaryDirectory() as tmpdir:
            users_file = Path(tmpdir) / "users.json"
            audit_file = Path(tmpdir) / "audit.json"
            auth = AuthService(
                users_file=str(users_file),
                audit_file=str(audit_file),
            )
            assert auth.resolve_google_redirect_uri() == "https://jus.trustcorp.com.br"
    finally:
        if previous_redirect_uri is None:
            os.environ.pop("GOOGLE_REDIRECT_URI", None)
        else:
            os.environ["GOOGLE_REDIRECT_URI"] = previous_redirect_uri

        if previous_allow_local is None:
            os.environ.pop("ALLOW_LOCALHOST_OAUTH_REDIRECT", None)
        else:
            os.environ["ALLOW_LOCALHOST_OAUTH_REDIRECT"] = previous_allow_local


def test_google_redirect_allows_localhost_when_opted_in():
    """Desenvolvimento local pode reabilitar localhost explicitamente."""
    previous_redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")
    previous_allow_local = os.environ.get("ALLOW_LOCALHOST_OAUTH_REDIRECT")

    try:
        os.environ["GOOGLE_REDIRECT_URI"] = "http://localhost:8502"
        os.environ["ALLOW_LOCALHOST_OAUTH_REDIRECT"] = "true"

        with tempfile.TemporaryDirectory() as tmpdir:
            users_file = Path(tmpdir) / "users.json"
            audit_file = Path(tmpdir) / "audit.json"
            auth = AuthService(
                users_file=str(users_file),
                audit_file=str(audit_file),
            )
            assert auth.resolve_google_redirect_uri() == "http://localhost:8502"
    finally:
        if previous_redirect_uri is None:
            os.environ.pop("GOOGLE_REDIRECT_URI", None)
        else:
            os.environ["GOOGLE_REDIRECT_URI"] = previous_redirect_uri

        if previous_allow_local is None:
            os.environ.pop("ALLOW_LOCALHOST_OAUTH_REDIRECT", None)
        else:
            os.environ["ALLOW_LOCALHOST_OAUTH_REDIRECT"] = previous_allow_local


if __name__ == "__main__":
    test_hash_password_deterministic()
    test_hash_password_different_salts()
    test_auth_admin_exists()
    test_auth_create_user()
    test_auth_authenticate_success()
    test_auth_authenticate_fail()
    test_auth_duplicate_user()
    test_auth_list_users()
    test_auth_rate_limit()
    test_auth_delete_user()
    test_auth_cannot_delete_admin()
    test_auth_short_password()
    test_google_oauth_configured_and_redirect_resolution()
    test_google_login_url_uses_resolved_redirect_uri()
    test_google_callback_prefers_configured_redirect_uri()
    test_google_redirect_ignores_localhost_by_default()
    test_google_redirect_allows_localhost_when_opted_in()
    print("Todos os testes de auth_service.py passaram!")
