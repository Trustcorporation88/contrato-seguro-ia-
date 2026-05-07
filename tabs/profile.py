import streamlit as st
from datetime import datetime

def show_profile():
    """
    Exibe a página de perfil do usuário com opção de trocar senha.
    Disponível para TODOS os usuários (não apenas admins).
    """
    user = st.session_state.get("authenticated_user", {})
    username = user.get("username", "")
    email = user.get("email", "")
    role = user.get("role", "user")
    
    st.title("🔐 Minha Conta")
    st.markdown("---")
    
    # Informações do Usuário
    st.subheader("👤 Informações do Perfil")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("👤 Usuário", username)
        st.metric("🏷️ Função", "Administrador" if role == "admin" else "Usuário")
    
    with col2:
        if email:
            st.metric("📧 E-mail", email)
        else:
            st.info("📧 Login via Google")
    
    st.markdown("---")
    
    # Trocar Senha (apenas para usuários com senha, não Google OAuth)
    if not email or "@" not in email:  # Usuário local (não Google)
        st.subheader("🔑 Alterar Senha")
        
        st.info("💡 **Dica de Segurança:** Use uma senha forte com pelo menos 6 caracteres.")
        
        with st.form("change_password_form"):
            old_password = st.text_input("🔒 Senha Atual", type="password", help="Digite sua senha atual")
            new_password = st.text_input("🆕 Nova Senha", type="password", help="Mínimo de 6 caracteres")
            confirm_password = st.text_input("✅ Confirmar Nova Senha", type="password", help="Digite a nova senha novamente")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
            
            with col_btn1:
                submit_password = st.form_submit_button("🔄 Alterar Senha", use_container_width=True)
            
            with col_btn2:
                cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
            
            if cancel:
                st.session_state.show_profile = False
                st.rerun()
            
            if submit_password:
                # Validações
                if not old_password or not new_password or not confirm_password:
                    st.error("❌ Por favor, preencha todos os campos.")
                elif new_password != confirm_password:
                    st.error("❌ As senhas não coincidem. Tente novamente.")
                elif len(new_password) < 6:
                    st.error("❌ A nova senha deve ter no mínimo 6 caracteres.")
                elif old_password == new_password:
                    st.warning("⚠️ A nova senha deve ser diferente da atual.")
                else:
                    # Chamar serviço de autenticação
                    auth_service = st.session_state.get("auth_service")
                    if auth_service:
                        success, message = auth_service.change_password(
                            username, old_password, new_password
                        )
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                            st.info("💡 **Sua senha foi alterada!** Por segurança, faça login novamente.")
                            
                            # Botão para fazer logout
                            if st.button("🚪 Fazer Login Novamente"):
                                st.session_state.authenticated_user = None
                                st.session_state.show_profile = False
                                st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ Erro ao acessar o serviço de autenticação.")
    else:
        st.info("🔐 **Conta Google OAuth**\n\nVocê está logado via Google. Para alterar sua senha, acesse sua Conta Google.")
        st.markdown("[🔗 Gerenciar Conta Google](https://myaccount.google.com/security)")
    
    st.markdown("---")
    
    # Estatísticas de uso (se disponível)
    st.subheader("📊 Estatísticas de Uso")
    
    try:
        import json
        import os
        from collections import Counter
        
        audit_log_path = "logs/audit.json"
        
        if os.path.exists(audit_log_path):
            with open(audit_log_path, "r", encoding="utf-8") as f:
                logs = [json.loads(line) for line in f if line.strip()]
            
            # Filtrar logs do usuário atual
            user_logs = [log for log in logs if log.get("username") == username]
            
            if user_logs:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Total de atividades
                    st.metric("📝 Total de Atividades", len(user_logs))
                
                with col2:
                    # Total de análises
                    analyses = [log for log in user_logs if log.get("action") == "ANALYSIS_REQUEST"]
                    st.metric("📄 Análises Realizadas", len(analyses))
                
                with col3:
                    # Último acesso
                    if user_logs:
                        last_log = max(user_logs, key=lambda x: x.get("timestamp", ""))
                        last_time = last_log.get("timestamp", "").split("T")[0] if last_log else "N/A"
                        st.metric("🕐 Último Acesso", last_time)
            else:
                st.info("Nenhuma atividade registrada ainda.")
        else:
            st.info("Logs de auditoria não disponíveis.")
    except Exception as e:
        st.warning(f"Não foi possível carregar estatísticas: {str(e)}")
    
    st.markdown("---")
    st.caption(f"💼 Logado como: **{username}** | 🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
