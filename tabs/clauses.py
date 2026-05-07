"""
Tab: Sugestão de Cláusulas
Exibe cláusulas problemáticas e gera sugestões com IA.
"""
import streamlit as st

from clause_service import extrair_clausulas_risco, get_clausula_padrao, sugerir_clausula_alternativa


def render_clauses():
    """Renderiza a aba de cláusulas problemáticas e sugestões."""
    st.markdown(
        '<h3 style="color: #3A6FA0;">📝 Cláusulas Problemáticas e Sugestões</h3>',
        unsafe_allow_html=True,
    )
    st.write("Redações alternativas para cláusulas de risco identificadas na análise.")

    try:
        clausulas = extrair_clausulas_risco(st.session_state.analise_resultado)

        if clausulas:
            for i, c in enumerate(clausulas):
                emoji = "🔴" if c["nivel"] == "alto" else ("🟠" if c["nivel"] == "medio" else "🟢")
                with st.expander(
                    f"{emoji} {c['texto_clausula'][:80]}...",
                    expanded=(i == 0 and c["nivel"] == "alto"),
                ):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**Cláusula original:**")
                        st.warning(c["texto_clausula"])
                        st.markdown("**Problema:**")
                        st.write(c["problema"][:300])
                        st.markdown("**Base legal:**")
                        st.caption(c["base_legal"][:200])

                    with col_b:
                        st.markdown("**Sugestão:**")
                        cpadrao = None
                        if "multa" in c["texto_clausula"].lower() or "multa" in c["problema"].lower():
                            cpadrao = get_clausula_padrao("multa_rescisoria")
                        elif "foro" in c["texto_clausula"].lower() or "foro" in c["problema"].lower():
                            cpadrao = get_clausula_padrao("foro_eleicao")
                        elif "confidencial" in c["texto_clausula"].lower() or "sigilo" in c["problema"].lower():
                            cpadrao = get_clausula_padrao("confidencialidade")
                        elif "lgpd" in c["texto_clausula"].lower() or "dados" in c["problema"].lower():
                            cpadrao = get_clausula_padrao("lgpd")
                        elif "reajust" in c["texto_clausula"].lower() or "corre" in c["problema"].lower():
                            cpadrao = get_clausula_padrao("reajuste")

                        if cpadrao:
                            st.success(cpadrao[:600])
                        else:
                            st.info("Gere a sugestão com IA clicando abaixo:")
                            if st.button(f"🤖 Gerar sugestão IA", key=f"gen_clause_{i}"):
                                with st.spinner("Consultando DeepSeek..."):
                                    ok_sug, texto_sug = sugerir_clausula_alternativa(
                                        clausula_original=c["texto_clausula"],
                                        tipo_problema=c["problema"],
                                        base_legal=c["base_legal"],
                                        tipo_contrato="prestação de serviços",
                                    )
                                    if ok_sug:
                                        st.session_state[f"clause_sug_{i}"] = texto_sug
                                    else:
                                        st.error(texto_sug)
                            if f"clause_sug_{i}" in st.session_state:
                                st.success(st.session_state[f"clause_sug_{i}"][:1000])
        else:
            st.info("Nenhuma cláusula de risco identificada no formato estruturado. Verifique a aba Análise Completa.")
    except Exception as e:
        st.warning(f"Erro ao extrair cláusulas: {e}")
        st.info("A análise completa está disponível na aba 'Análise Completa'.")
