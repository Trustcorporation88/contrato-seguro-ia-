import os
import json
import base64
from urllib.parse import urlencode

import requests
import streamlit as st


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def _get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _get_query_param(name: str):
    try:
        if hasattr(st, "query_params"):
            value = st.query_params.get(name)
            if isinstance(value, list):
                return value[0] if value else None
            return value

        params = st.experimental_get_query_params()
        value = params.get(name)
        if isinstance(value, list):
            return value[0] if value else None
        return value
    except Exception:
        return None


def _clear_oauth_query_params():
    try:
        if hasattr(st, "query_params"):
            st.query_params.clear()
        else:
            st.experimental_set_query_params()
    except Exception:
        pass


def _decode_state_redirect_uri():
    """
    O Google exige que o redirect_uri usado para trocar o code por token
    seja exatamente o mesmo usado na URL de autorização.

    Como o app já envia esse valor no state, usamos ele como fonte principal.
    """
    state = _get_query_param("state")

    if not state:
        return None

    try:
        padded = state + "=" * (-len(state) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
        payload = json.loads(decoded)
        redirect_uri = payload.get("redirect_uri")

        if redirect_uri:
            return str(redirect_uri).strip()
    except Exception:
        return None

    return None


def get_google_redirect_uri() -> str:
    return _get_env("GOOGLE_REDIRECT_URI", "https://jus.trustcorp.com.br")


def get_google_login_url() -> str:
    client_id = _get_env("GOOGLE_CLIENT_ID")
    redirect_uri = get_google_redirect_uri()

    state_payload = {
        "redirect_uri": redirect_uri,
    }

    state = base64.urlsafe_b64encode(
        json.dumps(state_payload).encode("utf-8")
    ).decode("utf-8").rstrip("=")

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def _save_google_session(google_user: dict):
    email = google_user.get("email")
    name = google_user.get("name") or email
    picture = google_user.get("picture")

    if not email:
        st.error("A conta Google não retornou e-mail.")
        return False

    # Chaves genéricas
    st.session_state["authenticated"] = True
    st.session_state["google_authenticated"] = True
    st.session_state["logged_in"] = True
    st.session_state["login_ok"] = True
    st.session_state["auth_provider"] = "google"

    # Dados do usuário
    st.session_state["user_email"] = email
    st.session_state["user_name"] = name
    st.session_state["user_picture"] = picture

    # Compatibilidade com nomes comuns usados em apps Streamlit
    st.session_state["email"] = email
    st.session_state["name"] = name
    st.session_state["usuario"] = email
    st.session_state["username"] = email
    st.session_state["user"] = {
        "email": email,
        "name": name,
        "picture": picture,
        "provider": "google",
    }

    return True


def handle_google_oauth_callback():
    code = _get_query_param("code")
    error = _get_query_param("error")

    if error:
        st.error(f"Erro no login Google: {error}")
        _clear_oauth_query_params()
        return False

    if not code:
        return False

    client_id = _get_env("GOOGLE_CLIENT_ID")
    client_secret = _get_env("GOOGLE_CLIENT_SECRET")

    # Fonte principal: redirect_uri salvo no state do próprio fluxo OAuth.
    # Fallback: variável de ambiente.
    redirect_uri = _decode_state_redirect_uri() or get_google_redirect_uri()

    if not client_id or not client_secret:
        st.error("Login Google não configurado. Verifique GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET.")
        return False

    try:
        token_response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=20,
        )

        if token_response.status_code != 200:
            details = None
            try:
                details = token_response.json()
            except Exception:
                details = token_response.text

            st.error("Não foi possível finalizar o login Google.")
            st.caption(f"Detalhe técnico: {details}")
            st.caption(f"Redirect URI usado na finalização: {redirect_uri}")
            return False

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            st.error("Google não retornou access_token.")
            return False

        user_response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20,
        )

        if user_response.status_code != 200:
            st.error("Não foi possível obter os dados do usuário Google.")
            return False

        google_user = user_response.json()

        if not _save_google_session(google_user):
            return False

        _clear_oauth_query_params()
        st.success(f"Login realizado com sucesso: {google_user.get('email')}")
        st.rerun()
        return True

    except Exception as exc:
        st.error("Erro ao finalizar login Google.")
        st.caption(str(exc))
        return False
