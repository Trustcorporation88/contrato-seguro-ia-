"""
Tab: Dashboard de Riscos
Exibe métricas, gráficos e resumo executivo da análise.
"""
import streamlit as st

from clause_service import extrair_numeros_riscos, extrair_pontos_atencao


def _exibir_estatisticas(analise_texto: str):
    """
    Exibe métricas e estatísticas de risco em formato visual.

    Args:
        analise_texto: Texto da análise para extrair estatísticas
    """
    riscos = extrair_numeros_riscos(analise_texto)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🔴 Riscos Altos", riscos["altos"])

    with col2:
        st.metric("🟠 Riscos Médios", riscos["medios"])

    with col3:
        st.metric("🟢 Riscos Baixos", riscos["baixos"])

    with col4:
        st.metric("📊 Total de Riscos", riscos["total"])

    st.subheader("Índice de Risco Geral")

    if riscos["total"] > 0:
        percentual_alto = (riscos["altos"] / riscos["total"]) * 100
        percentual_medio = (riscos["medios"] / riscos["total"]) * 100
        percentual_baixo = (riscos["baixos"] / riscos["total"]) * 100

        st.write("**Composição de Riscos:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"🔴 Altos: {percentual_alto:.1f}%")
        with col2:
            st.write(f"🟠 Médios: {percentual_medio:.1f}%")
        with col3:
            st.write(f"🟢 Baixos: {percentual_baixo:.1f}%")

        if percentual_alto > 20:
            st.warning(
                "⚠️ Contrato com alto nível de risco. Recomenda-se revisão completa antes de assinar."
            )
        elif percentual_medio > 30:
            st.info("ℹ️ Contrato com riscos moderados. Negociar pontos identificados.")
        else:
            st.success(
                "✅ Contrato com risco controlado. Pontos de atenção estão marcados."
            )
    else:
        st.info("Nenhum risco identificado na análise.")


def render_dashboard():
    """Renderiza a aba de dashboard com métricas, gráficos e resumo executivo."""
    riscos_dict = extrair_numeros_riscos(st.session_state.analise_resultado)

    st.markdown(
        '<h3 style="color: #3A6FA0;">Métricas de Risco</h3>', unsafe_allow_html=True
    )
    _exibir_estatisticas(st.session_state.analise_resultado)

    total = riscos_dict["altos"] + riscos_dict["medios"] + riscos_dict["baixos"]
    if total > 0:
        st.markdown(
            '<h3 style="color: #3A6FA0; margin-top: 2rem;">📈 Gráfico de Riscos</h3>',
            unsafe_allow_html=True,
        )
        try:
            from report_service import gerar_grafico_risco_pizza, gerar_grafico_radar

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                grafico_buf = gerar_grafico_risco_pizza(
                    riscos_dict["altos"], riscos_dict["medios"], riscos_dict["baixos"]
                )
                if grafico_buf:
                    st.image(grafico_buf, width=350)

            with col_g2:
                nota_riscos = max(0, 10 - (riscos_dict["altos"] * 3 + riscos_dict["medios"] * 1.5))
                radar_buf = gerar_grafico_radar({
                    "Clareza": 7.0,
                    "Equilíbrio": min(10, 8 - riscos_dict["altos"] * 2),
                    "Segurança": min(10, 8 - riscos_dict["altos"] * 1.5),
                    "LGPD": 7.5,
                    "Riscos": min(10, nota_riscos),
                })
                if radar_buf:
                    st.image(radar_buf, width=350)
        except Exception as e:
            st.caption(f"Gráficos indisponíveis: {str(e)}")

    st.markdown(
        '<h3 style="color: #3A6FA0; margin-top: 2rem;">⚠️ Resumo Executivo (Máximo 20 linhas)</h3>',
        unsafe_allow_html=True,
    )

    pontos = extrair_pontos_atencao(
        st.session_state.analise_resultado, max_linhas=20
    )
    st.markdown(
        f"""
        <div style="background-color: #F7F2EA; padding: 1.5rem; border-radius: 8px; border-left: 5px solid #D4AF37; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            {pontos.replace(chr(10), "<br>")}
        </div>
        """,
        unsafe_allow_html=True,
    )
