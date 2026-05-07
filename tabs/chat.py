"""
Tab: Consultoria IA
Chat para tirar dúvidas sobre o contrato analisado.
"""
import logging

import streamlit as st

from analyzer import responder_duvida_clausula

logger = logging.getLogger(__name__)


def render_chat():
    """Renderiza a aba de chat para dúvidas sobre o contrato."""
    st.markdown(
        '<h3 style="color: #3A6FA0;">💬 Tire dúvidas sobre o contrato</h3>',
        unsafe_allow_html=True,
    )
    st.write(
        "Converse com a IA para esclarecer pontos específicos do contrato analisado."
    )

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    duvida = st.chat_input(
        "Ex: O que acontece se a parte atrasar o pagamento em 5 dias?",
        key="chat_input",
    )

    if duvida:
        st.session_state.chat_messages.append({"role": "user", "content": duvida})
        with st.chat_message("user"):
            st.markdown(duvida)

        with st.spinner("Analisando cláusulas e gerando resposta..."):
            try:
                resposta = responder_duvida_clausula(
                    duvida, st.session_state.analise_resultado
                )
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": resposta}
                )
                with st.chat_message("assistant"):
                    st.markdown(resposta)
            except Exception as e:
                st.error(f"Erro ao gerar resposta: {str(e)}")
                logger.error(f"Erro no chat: {str(e)}")
