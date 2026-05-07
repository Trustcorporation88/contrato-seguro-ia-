"""
admin.py - Dashboard Administrativo de Analytics
Monitora logins, uso do sistema e gerenciamento de usuários.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


def _load_audit_log() -> List[Dict]:
    """Carrega o log de auditoria."""
    audit_file = Path(__file__).parent.parent / "logs" / "audit.json"
    if not audit_file.exists():
        return []
    
    try:
        with open(audit_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar audit.json: {e}")
        return []


def _load_users() -> Dict:
    """Carrega dados dos usuários."""
    users_file = Path(__file__).parent.parent / "cache" / "users.json"
    if not users_file.exists():
        return {}
    
    try:
        with open(users_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar users.json: {e}")
        return {}


def _get_today_logins(audit_log: List[Dict]) -> List[Dict]:
    """Filtra logins de hoje."""
    today = datetime.now().date()
    logins = []
    
    for entry in audit_log:
        if entry.get("action") in ["LOGIN_SUCCESS", "LOGIN_GOOGLE_SUCCESS"]:
            try:
                timestamp = datetime.fromisoformat(entry["timestamp"])
                if timestamp.date() == today:
                    logins.append(entry)
            except Exception:
                continue
    
    return logins


def _calculate_session_duration(login_time: datetime, audit_log: List[Dict], username: str) -> int:
    """
    Calcula duração da sessão em minutos.
    Usa a última ação registrada do usuário após o login.
    """
    # Encontra todas as ações do usuário após o login
    user_actions = []
    for entry in audit_log:
        if entry.get("user") == username:
            try:
                action_time = datetime.fromisoformat(entry["timestamp"])
                if action_time >= login_time:
                    user_actions.append(action_time)
            except Exception:
                continue
    
    if not user_actions:
        # Se não há ações, assume sessão mínima de 1 minuto
        return 1
    
    # Última ação registrada
    last_action = max(user_actions)
    duration = (last_action - login_time).total_seconds() / 60
    
    return max(1, int(duration))  # Mínimo 1 minuto


def render_admin_tab():
    """Renderiza a aba de administração."""
    st.title("📊 Painel Administrativo")
    
    # Verifica se usuário tem permissão
    if not st.session_state.get("user"):
        st.warning("⚠️ Você precisa estar logado para acessar esta página.")
        return
    
    user_role = st.session_state.get("user", {}).get("role", "lawyer")
    if user_role != "admin":
        st.error("🚫 Acesso negado. Apenas administradores podem acessar esta página.")
        st.info("💡 Entre em contato com um administrador para solicitar acesso.")
        return
    
    # Carrega dados
    audit_log = _load_audit_log()
    users = _load_users()
    
    if not audit_log:
        st.warning("📭 Nenhum log de auditoria encontrado.")
        return
    
    # ================================================================
    # MÉTRICAS PRINCIPAIS
    # ================================================================
    
    st.subheader("🎯 Resumo de Hoje")
    
    today_logins = _get_today_logins(audit_log)
    unique_users_today = len(set(entry["user"] for entry in today_logins))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔑 Logins Hoje", len(today_logins))
    
    with col2:
        st.metric("👥 Usuários Únicos", unique_users_today)
    
    with col3:
        st.metric("📊 Total Usuários", len(users))
    
    with col4:
        # Logins da última hora
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_logins = sum(
            1 for entry in today_logins
            if datetime.fromisoformat(entry["timestamp"]) >= one_hour_ago
        )
        st.metric("⏱️ Última Hora", recent_logins)
    
    st.markdown("---")
    
    # ================================================================
    # QUEM LOGOU HOJE
    # ================================================================
    
    st.subheader("👤 Quem Logou Hoje")
    
    if not today_logins:
        st.info("📭 Nenhum login registrado hoje.")
    else:
        # Prepara dados para tabela
        login_data = []
        for entry in today_logins:
            username = entry["user"]
            timestamp_str = entry["timestamp"]
            timestamp = datetime.fromisoformat(timestamp_str)
            
            # Pega email do Google se disponível
            email = entry.get("details", "")
            if not email and username in users:
                email = users[username].get("google_email", "N/A")
            
            # Calcula duração da sessão
            duration = _calculate_session_duration(timestamp, audit_log, username)
            
            login_data.append({
                "Usuário": username,
                "Email": email,
                "Horário": timestamp.strftime("%H:%M:%S"),
                "Método": "Google" if entry["action"] == "LOGIN_GOOGLE_SUCCESS" else "Senha",
                "Tempo de Uso (min)": duration,
            })
        
        df_logins = pd.DataFrame(login_data)
        
        # Ordena por horário (mais recente primeiro)
        df_logins = df_logins.sort_values("Horário", ascending=False)
        
        st.dataframe(
            df_logins,
            use_container_width=True,
            hide_index=True,
        )
    
    st.markdown("---")
    
    # ================================================================
    # TEMPO MÉDIO DE USO
    # ================================================================
    
    st.subheader("⏱️ Tempo Médio de Uso")
    
    if today_logins:
        total_duration = 0
        duration_count = 0
        
        for entry in today_logins:
            username = entry["user"]
            timestamp = datetime.fromisoformat(entry["timestamp"])
            duration = _calculate_session_duration(timestamp, audit_log, username)
            total_duration += duration
            duration_count += 1
        
        avg_duration = total_duration / duration_count if duration_count > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("⏱️ Tempo Médio", f"{int(avg_duration)} min")
        
        with col2:
            st.metric("📈 Tempo Total", f"{int(total_duration)} min")
        
        with col3:
            st.metric("📊 Sessões", duration_count)
        
        # Gráfico de tempo por usuário (se mais de um usuário)
        if unique_users_today > 1:
            st.markdown("**Tempo de Uso por Usuário:**")
            
            user_durations = {}
            for entry in today_logins:
                username = entry["user"]
                timestamp = datetime.fromisoformat(entry["timestamp"])
                duration = _calculate_session_duration(timestamp, audit_log, username)
                
                if username not in user_durations:
                    user_durations[username] = 0
                user_durations[username] += duration
            
            df_durations = pd.DataFrame(
                list(user_durations.items()),
                columns=["Usuário", "Tempo Total (min)"]
            ).sort_values("Tempo Total (min)", ascending=False)
            
            st.bar_chart(df_durations.set_index("Usuário"))
    else:
        st.info("📭 Nenhuma sessão registrada hoje.")
    
    st.markdown("---")
    
    # ================================================================
    # HISTÓRICO RECENTE (ÚLTIMOS 7 DIAS)
    # ================================================================
    
    st.subheader("📅 Histórico dos Últimos 7 Dias")
    
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    daily_stats = {}
    for entry in audit_log:
        if entry.get("action") in ["LOGIN_SUCCESS", "LOGIN_GOOGLE_SUCCESS"]:
            try:
                timestamp = datetime.fromisoformat(entry["timestamp"])
                if timestamp >= seven_days_ago:
                    date_key = timestamp.date()
                    if date_key not in daily_stats:
                        daily_stats[date_key] = {"logins": 0, "users": set()}
                    daily_stats[date_key]["logins"] += 1
                    daily_stats[date_key]["users"].add(entry["user"])
            except Exception:
                continue
    
    if daily_stats:
        chart_data = []
        for date_key in sorted(daily_stats.keys()):
            chart_data.append({
                "Data": date_key.strftime("%d/%m"),
                "Logins": daily_stats[date_key]["logins"],
                "Usuários Únicos": len(daily_stats[date_key]["users"]),
            })
        
        df_chart = pd.DataFrame(chart_data)
        st.line_chart(df_chart.set_index("Data"))
    else:
        st.info("📭 Nenhum login nos últimos 7 dias.")
    
    st.markdown("---")
    
    # ================================================================
    # GERENCIAMENTO DE CONTA
    # ================================================================
    
    st.subheader("🔐 Gerenciamento de Conta")
    
    with st.expander("🔑 Alterar Minha Senha", expanded=False):
        st.markdown("**Altere sua senha de administrador:**")
        
        current_username = st.session_state.get("user", {}).get("username", "")
        
        with st.form("change_password_form"):
            old_password = st.text_input("Senha Atual", type="password")
            new_password = st.text_input("Nova Senha", type="password")
            confirm_password = st.text_input("Confirmar Nova Senha", type="password")
            
            submit_password = st.form_submit_button("🔄 Alterar Senha")
            
            if submit_password:
                if not old_password or not new_password or not confirm_password:
                    st.error("❌ Preencha todos os campos.")
                elif new_password != confirm_password:
                    st.error("❌ As senhas não coincidem.")
                elif len(new_password) < 6:
                    st.error("❌ A nova senha deve ter no mínimo 6 caracteres.")
                else:
                    auth_service = st.session_state.get("auth_service")
                    if auth_service:
                        success, message = auth_service.change_password(
                            current_username, old_password, new_password
                        )
                        if success:
                            st.success(f"✅ {message}")
                            st.info("💡 Faça login novamente com a nova senha.")
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ Erro ao acessar serviço de autenticação.")
    
    st.markdown("---")
    
    # ================================================================
    # EXPORT
    # ================================================================
    
    st.subheader("💾 Exportar Dados")
    
    if st.button("📥 Baixar Relatório de Hoje (CSV)"):
        if today_logins:
            df_export = pd.DataFrame(login_data)
            csv = df_export.to_csv(index=False).encode("utf-8")
            
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"logins_{datetime.now().strftime('%Y-%m-%d')}.csv",
                mime="text/csv",
            )
        else:
            st.warning("📭 Nenhum dado para exportar hoje.")
