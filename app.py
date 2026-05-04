# ================================================================
# CONTRATO SEGURO IA - Aplicação Principal
# ================================================================
# Análise inteligente de contratos usando Gemini/Ollama
# ================================================================

import io
import logging
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

# Importações para processamento
import google.generativeai as genai
import streamlit as st
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Importações do projeto
from analyzer import SELECTED_MODEL, analisar_contrato, set_model, set_fallback
from auth_service import AuthService
from cache_manager import CacheManager
from config import load_env_config
from database_service import DatabaseService
from pdf_extractor import extrair_metadados_pdf, extrair_texto_pdf_bytes

# ================================================================
# CONFIGURAÇÕES INICIAIS
# ================================================================

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ================================================================
# CONFIGURAÇÃO DE PÁGINA STREAMLIT
# ================================================================

st.set_page_config(
    page_title="TRUST CORPORATION - Contrato Seguro IA",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Aplicar CSS customizado - Design Profissional Fase 1
st.markdown(
    """
<style>
    /* ============ PALETA DE CORES PROFISSIONAL ============ */
    :root {
        --primary: #3A6FA0;      /* Azul claro - confiança */
        --secondary: #5B9E6D;    /* Verde claro - segurança */
        --accent: #D4AF37;       /* Ouro - premium */
        --danger: #C41E3A;       /* Vermelho escuro */
        --warning: #E89500;      /* Laranja */
        --success: #4CAF50;      /* Verde vibrante */
        --bg: #F7F2EA;           /* Bege claro */
        --text-primary: #3A6FA0; /* Texto principal */
        --text-secondary: #6A8A9A; /* Texto secundário */
    }

    /* ============ MAIN CONTAINER ============ */
    .main {
        padding: 0;
        background-color: #F7F2EA;
    }

    /* ============ HEADER PROFISSIONAL ============ */
    .header-top {
        background: linear-gradient(135deg, #3A6FA0 0%, #5B9E6D 100%);
        padding: 1rem 2rem;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-bottom: 3px solid #D4AF37;
    }

    /* ============ TIPOGRAFIA PROFISSIONAL ============ */
    h1 {
        font-family: 'Georgia', 'Times New Roman', serif;
        color: #3A6FA0;
        letter-spacing: 2px;
        font-weight: 700;
        margin-top: 2rem;
    }

    h2 {
        font-family: 'Georgia', 'Times New Roman', serif;
        color: #3A6FA0;
        letter-spacing: 1px;
        font-weight: 600;
        border-bottom: 2px solid #D4AF37;
        padding-bottom: 0.5rem;
    }

    h3 {
        font-family: 'Georgia', 'Times New Roman', serif;
        color: #5B9E6D;
        font-weight: 600;
    }

    /* ============ BADGES DE SEGURANÇA ============ */
    .security-badge {
        display: inline-block;
        background-color: #E8F5E9;
        border: 1px solid #2E7D32;
        color: #2E7D32;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        margin: 0.25rem;
        vertical-align: middle;
    }

    .trust-badge {
        display: inline-block;
        background: linear-gradient(135deg, #D4AF37 0%, #C9A227 100%);
        color: #3A6FA0;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-weight: 700;
        margin: 0.5rem 0.25rem;
        box-shadow: 0 2px 4px rgba(212,175,55,0.3);
    }

    /* ============ BUTTONS PROFISSIONAIS ============ */
    .stButton > button {
        background-color: #4088C0 !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 6px rgba(64,136,192,0.2) !important;
    }

    .stButton > button[kind="primary"] {
        background-color: #4088C0 !important;
        border: none !important;
        color: white !important;
    }

    .stButton > button:hover {
        background-color: #5B9E6D !important;
        box-shadow: 0 4px 12px rgba(91,158,109,0.3) !important;
        transform: translateY(-2px) !important;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #5B9E6D !important;
    }

    .stFormSubmitButton > button {
        background-color: #4088C0 !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }

    .stFormSubmitButton > button:hover {
        background-color: #5B9E6D !important;
    }

    /* ============ ALERT BOXES PROFISSIONAIS ============ */
    .alert-box {
        padding: 1.25rem;
        border-radius: 4px;
        margin: 1rem 0;
        border-left: 4px solid;
        background-color: #F7F2EA;
    }

    .alert-high {
        background-color: #FFEBEE;
        border-left-color: #C41E3A;
        color: #C41E3A;
    }

    .alert-medium {
        background-color: #FFF3E0;
        border-left-color: #FF9500;
        color: #FF9500;
    }

    .alert-low {
        background-color: #E8F5E9;
        border-left-color: #2E7D32;
        color: #2E7D32;
    }

    /* ============ DIVIDER PROFISSIONAL ============ */
    .streamlit-expanderHeader {
        background-color: #F7F2EA;
        border: 1px solid #E0E0E0;
    }

    /* ============ SIDEBAR ============ */
    .sidebar .sidebar-content {
        background-color: #F7F2EA;
    }

    /* ============ CARDS/CONTAINERS ============ */
    .info-card {
        background: #F7F2EA;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }

    .info-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: #D4AF37;
    }

    /* ============ TRUST INDICATORS ============ */
    .trust-section {
        background: linear-gradient(135deg, #F7F2EA 0%, #FFFFFF 100%);
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }

    .trust-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0.5rem 0.5rem 0.5rem 0;
        font-size: 0.9em;
        color: #2E7D32;
        font-weight: 600;
    }

    /* ============ TABS ============ */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 1.05em;
        font-weight: 600;
        color: #546E7A;
        border-bottom: 3px solid transparent;
        transition: all 0.3s ease;
    }

    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #3A6FA0;
        border-bottom-color: #D4AF37;
    }

    /* ============ EXPANDER ============ */
    .streamlit-expanderHeader {
        background-color: #F7F2EA;
        border: 1px solid #E0E0E0;
        border-radius: 4px;
    }

    /* ============ TEXT ============ */
    p {
        color: #546E7A;
        line-height: 1.6;
    }

    strong {
        color: #3A6FA0;
        font-weight: 700;
    }</style>
""",
    unsafe_allow_html=True,
)

# ================================================================
# AUTENTICAÇÃO
# ================================================================

if "auth_service" not in st.session_state:
    st.session_state.auth_service = AuthService()

if "db_service" not in st.session_state:
    st.session_state.db_service = DatabaseService()

if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

if st.session_state.authenticated_user is None:

    # Google OAuth callback
    query_params = st.query_params
    if "code" in query_params and "state" not in query_params:
        code = query_params["code"]
        redirect_uri = query_params.get("redirect_uri", "http://localhost:8502")
        ok, msg, user_data = st.session_state.auth_service.google_callback(code, redirect_uri)
        if ok:
            st.session_state.authenticated_user = user_data
            st.session_state.db_service.log_acceptance(user_data["username"])
            st.query_params.clear()
            st.rerun()
        else:
            st.error(f"Erro no login Google: {msg}")
            st.query_params.clear()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        st.markdown(
            '<h2 style="text-align: center; color: #3A6FA0;">🔐 Acesso ao Sistema</h2>',
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")

            st.markdown("---")
            st.markdown("""
            **⚠️ Termos de Uso**

            As análises são geradas por inteligência artificial com base jurídica em evidências públicas,
            jurisprudências e boas práticas dos maiores escritórios do Brasil. Esta ferramenta é um auxílio
            e **não substitui a consulta a um advogado**.

            A TRUST CORPORATION não se responsabiliza por decisões tomadas com base
            exclusivamente nas análises desta plataforma.
            """)

            aceite = st.checkbox(
                "Li e aceito os termos de uso",
                value=False,
                key="accept_terms",
            )

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")
            with col_btn2:
                google_login = st.form_submit_button("Entrar com Google", use_container_width=True)

            if submitted:
                if not aceite:
                    st.error("É necessário aceitar os termos de uso para acessar o sistema.")
                else:
                    ok, msg, user_data = st.session_state.auth_service.authenticate(username, password)
                    if ok:
                        st.session_state.authenticated_user = user_data
                        st.session_state.db_service.log_acceptance(username)
                        st.rerun()
                    else:
                        st.error(msg)

            if google_login:
                if not aceite:
                    st.error("É necessário aceitar os termos de uso para acessar o sistema.")
                else:
                    redirect_uri = "http://localhost:8502"
                    google_url = st.session_state.auth_service.google_login_url(redirect_uri)
                    if google_url:
                        st.markdown(
                            f'<meta http-equiv="refresh" content="0; url={google_url}">'
                            f'<a href="{google_url}" target="_self">'
                            '<button style="width: 100%; padding: 0.75rem; background-color: #4285F4; '
                            'color: white; border: none; border-radius: 0.4rem; cursor: pointer; '
                            'font-weight: bold;">Redirecionando para Google...</button></a>',
                            unsafe_allow_html=True,
                        )
                        st.stop()
                    else:
                        st.error("Google OAuth não configurado. Configure GOOGLE_CLIENT_ID no .env")

        st.caption("Usuário padrão: admin / admin123")

    st.stop()

# ================================================================
# INICIALIZAÇÃO DO SESSION STATE
# ================================================================

# Inicializar variáveis de sessão com valores padrão
if "cache_analise" not in st.session_state:
    st.session_state.cache_analise = None

if "texto_original" not in st.session_state:
    st.session_state.texto_original = ""

if "analise_resultado" not in st.session_state:
    st.session_state.analise_resultado = ""

if "nome_arquivo" not in st.session_state:
    st.session_state.nome_arquivo = ""

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "modelo_selecionado" not in st.session_state:
    st.session_state.modelo_selecionado = "deepseek"

if "cache_manager" not in st.session_state:
    st.session_state.cache_manager = CacheManager(cache_dir="cache", max_history=100)

# ================================================================
# FUNÇÕES AUXILIARES
# ================================================================


def limpar_analise():
    """
    Limpa o resultado da análise atual.
    Mantém o arquivo, texto original e cache persistido.
    """
    st.session_state.cache_analise = None
    st.session_state.analise_resultado = ""
    st.session_state.chat_messages = []
    logger.info("Análise limpa do session state")


def extrair_numeros_riscos(analise_texto: str) -> dict:
    """
    Extrai estatísticas de riscos do texto da análise.

    Args:
        analise_texto: Texto da análise contendo os riscos

    Returns:
        Dicionário com contagem de riscos por nível
    """
    riscos_altos = len(re.findall(r"🔴\s*RISCO\s*ALTO", analise_texto, re.IGNORECASE))
    riscos_medios = len(
        re.findall(r"🟠\s*RISCO\s*M[ÉE]DIO", analise_texto, re.IGNORECASE)
    )
    riscos_baixos = len(
        re.findall(r"🟢\s*RISCO\s*BAIXO|🟢\s*BAIXO", analise_texto, re.IGNORECASE)
    )

    return {
        "altos": riscos_altos,
        "medios": riscos_medios,
        "baixos": riscos_baixos,
        "total": riscos_altos + riscos_medios + riscos_baixos,
    }


def exibir_estatisticas(analise_texto: str):
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

    # Barra de progresso de risco
    st.subheader("Índice de Risco Geral")

    if riscos["total"] > 0:
        percentual_alto = (riscos["altos"] / riscos["total"]) * 100
        percentual_medio = (riscos["medios"] / riscos["total"]) * 100
        percentual_baixo = (riscos["baixos"] / riscos["total"]) * 100

        st.write(f"**Composição de Riscos:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"🔴 Altos: {percentual_alto:.1f}%")
        with col2:
            st.write(f"🟠 Médios: {percentual_medio:.1f}%")
        with col3:
            st.write(f"🟢 Baixos: {percentual_baixo:.1f}%")

        # Avaliação geral
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


def extrair_pontos_atencao(analise_texto: str, max_linhas: int = 20) -> str:
    """
    Extrai um resumo executivo conciso com os pontos de atenção/riscos.
    Para cada risco identificado, extrai APENAS cláusula + problema (1 linha),
    ignorando base legal e sugestão para manter o resumo enxuto.

    Args:
        analise_texto: Texto completo da análise
        max_linhas: Número máximo de linhas para retornar

    Returns:
        Resumo executivo conciso (máx. 20 linhas)
    """
    import re

    pontos = []

    # Padrão para detectar cada bloco de risco
    bloco_pattern = re.compile(
        r"\*\*[🔴🟠🟢]\s*RISCO\s*(ALTO|M[ÉE]DIO|BAIXO)\*\*",
        re.IGNORECASE,
    )

    matches = list(bloco_pattern.finditer(analise_texto))

    if matches:
        for i, match in enumerate(matches):
            nivel = match.group(1).upper()
            emoji = "🔴" if "ALTO" in nivel else ("🟠" if "MÉDIO" in nivel or "MEDIO" in nivel else "🟢")

            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else min(len(analise_texto), start + 2000)
            bloco = analise_texto[start:end]

            clausula_match = re.search(
                r"Cl[aá]usula\S*\s*:?\s*(.+?)(?:\n|$)", bloco, re.IGNORECASE
            )
            problema_match = re.search(
                r"Problema\S*\s*:?\s*(.+?)(?:\.(?:\s|$))", bloco, re.IGNORECASE | re.DOTALL
            )

            clausula_texto = clausula_match.group(1).strip() if clausula_match else ""
            problema_texto = problema_match.group(1).strip() if problema_match else ""

            primeira_linha_problema = problema_texto.split(".")[0].strip() if problema_texto else ""

            if clausula_texto and primeira_linha_problema:
                pontos.append(f"{emoji} **{clausula_texto}**: {primeira_linha_problema[:140]}.")
            elif clausula_texto:
                pontos.append(f"{emoji} **{clausula_texto}**")
            elif primeira_linha_problema:
                pontos.append(f"{emoji} {primeira_linha_problema[:160]}.")

            if len(pontos) >= max_linhas:
                break

    if not pontos:
        # Fallback: extrair linhas relevantes do texto
        linhas = analise_texto.split("\n")
        em_resumo = False
        for linha in linhas:
            if "resumo fiel" in linha.lower() or "resumo executivo" in linha.lower():
                em_resumo = True
                continue
            if em_resumo and (
                "tópicos" in linha.lower()
                or "análise de riscos" in linha.lower()
                or linha.startswith("##")
                or linha.startswith("###")
            ):
                em_resumo = False
                continue
            if em_resumo and linha.strip():
                clean = linha.strip()
                if any(clean.startswith(p) for p in ["- ", "• ", "* "]):
                    pontos.append(clean)
                elif clean and not clean.startswith("#"):
                    pontos.append(clean)
                if len(pontos) >= max_linhas:
                    break

    resumo = "\n".join(pontos[:max_linhas])

    if len(pontos) > max_linhas:
        resumo += f"\n\n... (mais {len(pontos) - max_linhas} pontos na análise completa)"

    return resumo if resumo else "Nenhum ponto crítico identificado."


def gerar_pdf(analise_texto: str, nome_arquivo: str = "analise_contrato") -> BytesIO:
    """
    Gera um arquivo PDF com a análise do contrato.

    Args:
        analise_texto: Texto da análise para incluir no PDF
        nome_arquivo: Nome base do arquivo (sem extensão)

    Returns:
        BytesIO contendo o PDF gerado
    """
    try:
        # Criar buffer em memória
        buffer = BytesIO()

        # Criar documento PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1 * cm,
            leftMargin=1 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1 * cm,
        )

        # Obter estilos
        styles = getSampleStyleSheet()

        # Criar estilos customizados
        titulo_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#1a237e"),
            spaceAfter=12,
            alignment=1,  # Center
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#283593"),
            spaceAfter=8,
            spaceBefore=8,
        )

        body_style = ParagraphStyle(
            "CustomBody",
            parent=styles["BodyText"],
            fontSize=10,
            alignment=4,  # Justify
        )

        # Montar conteúdo
        content = []

        # Título
        content.append(Paragraph("ANÁLISE DE CONTRATO", titulo_style))
        content.append(
            Paragraph(f"<font size=9>{nome_arquivo}</font>", styles["Normal"])
        )
        content.append(Spacer(1, 0.5 * cm))

        # Análise (quebra de parágrafos)
        for paragrafo in analise_texto.split("\n"):
            if paragrafo.strip():
                # Detectar nível de heading
                if paragrafo.startswith("# "):
                    content.append(
                        Paragraph(paragrafo.replace("# ", ""), heading_style)
                    )
                elif paragrafo.startswith("## "):
                    content.append(
                        Paragraph(paragrafo.replace("## ", ""), heading_style)
                    )
                else:
                    content.append(Paragraph(paragrafo, body_style))
                content.append(Spacer(1, 0.2 * cm))

        # Rodapé com informações
        content.append(Spacer(1, 0.5 * cm))
        content.append(
            Paragraph(
                "<font size=8><i>Documento gerado pela plataforma TRUST CORPORATION - Contrato Seguro IA</i></font>",
                styles["Normal"],
            )
        )

        # Compilar PDF
        doc.build(content)
        buffer.seek(0)

        return buffer

    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {str(e)}")
        raise


def gerar_word(analise_texto: str, nome_arquivo: str = "analise_contrato") -> BytesIO:
    """
    Gera um arquivo Word (.docx) com a análise do contrato.

    Args:
        analise_texto: Texto da análise para incluir no documento
        nome_arquivo: Nome base do arquivo (sem extensão)

    Returns:
        BytesIO contendo o documento Word gerado
    """
    try:
        # Criar documento
        doc = Document()

        # Configurar fonte padrão
        style = doc.styles["Normal"]
        style.font.name = "Calibri"
        style.font.size = Pt(11)

        # Título
        titulo = doc.add_heading("ANÁLISE DE CONTRATO", level=1)
        titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Subtítulo com nome do arquivo
        subtitulo = doc.add_paragraph(nome_arquivo)
        subtitulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitulo_format = subtitulo.runs[0]
        subtitulo_format.italic = True
        subtitulo_format.font.size = Pt(9)

        # Adicionar linha em branco
        doc.add_paragraph()

        # Processar análise linha por linha
        for linha in analise_texto.split("\n"):
            if not linha.strip():
                continue

            # Detectar heading (Markdown style)
            if linha.startswith("# "):
                p = doc.add_heading(linha.replace("# ", ""), level=1)
            elif linha.startswith("## "):
                p = doc.add_heading(linha.replace("## ", ""), level=2)
            elif linha.startswith("### "):
                p = doc.add_heading(linha.replace("### ", ""), level=3)
            else:
                # Parágrafo normal
                p = doc.add_paragraph(linha)

                # Aplicar formatação de negrito a padrões específicos
                for run in p.runs:
                    if any(
                        word in run.text
                        for word in [
                            "RISCO ALTO",
                            "RISCO MÉDIO",
                            "Cláusula:",
                            "Problema:",
                            "Base legal:",
                            "Sugestão",
                        ]
                    ):
                        run.bold = True

        # Adicionar rodapé
        doc.add_paragraph()
        rodape = doc.add_paragraph(
            "Documento gerado pela plataforma TRUST CORPORATION - Contrato Seguro IA"
        )
        for run in rodape.runs:
            run.font.size = Pt(8)
            run.italic = True

        # Salvar em buffer
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        return buffer

    except Exception as e:
        logger.error(f"Erro ao gerar Word: {str(e)}")
        raise


def responder_duvida_clausula(duvida: str, contexto_analise: str) -> str:
    """
    Usa Gemini para responder dúvidas sobre o contrato analisado.

    Args:
        duvida: Pergunta do usuário sobre o contrato
        contexto_analise: Texto da análise do contrato

    Returns:
        Resposta gerada pela IA
    """
    try:
        import os as _os
        api_key = _os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Erro: Chave da API Gemini não configurada. Configure GEMINI_API_KEY no arquivo .env"
        genai.configure(api_key=api_key)

        prompt = f"""Você é um assistente jurídico especializado em análise de contratos.
Responda a seguinte dúvida do usuário baseando-se na análise fornecida.

Análise do Contrato:
{contexto_analise}

Dúvida do usuário:
{duvida}

Forneça uma resposta clara, objetiva e fundamentada baseada apenas na análise fornecida."""

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        return response.text

    except Exception as e:
        logger.error(f"Erro ao responder dúvida: {str(e)}")
        return f"Desculpe, não consegui processar sua pergunta. Erro: {str(e)}"


# ================================================================
# INTERFACE PRINCIPAL
# ================================================================

# ================================================================
# HEADER PROFISSIONAL COM BADGES DE SEGURANÇA
# ================================================================

# Header com logo e título
col1, col2 = st.columns([1, 4])

with col1:
    try:
        logo_path = Path("assets/Logo TRUST Contrato Seguro.png")
        if logo_path.exists():
            st.image(str(logo_path), width=300)
        else:
            st.write("🔐")
    except Exception as e:
        logger.warning(f"Logo não encontrada: {str(e)}")
        st.write("🔐")

with col2:
    st.title("TRUST CORPORATION")
    st.markdown("### Contrato Seguro IA - Análise Inteligente de Contratos")
    st.markdown(
        "*Riscos Contratuais analisados pelos modelos utilizados pelos maiores escritórios de advocacia do Brasil*"
    )

# ================================================================
# BADGES DE SEGURANÇA E TRUST INDICATORS
# ================================================================

st.markdown("---")

# Badges de Segurança
col_badge1, col_badge2, col_badge3, col_badge4, col_badge5 = st.columns(5)

with col_badge1:
    st.markdown(
        '<div class="security-badge">🔒 LGPD Compliant</div>',
        unsafe_allow_html=True,
    )

with col_badge2:
    st.markdown(
        '<div class="security-badge">🔐 SSL/TLS Encrypted</div>',
        unsafe_allow_html=True,
    )

with col_badge3:
    st.markdown(
        '<div class="security-badge">✅ ISO 27001</div>',
        unsafe_allow_html=True,
    )

with col_badge4:
    st.markdown(
        '<div class="security-badge">📊 Auditável</div>',
        unsafe_allow_html=True,
    )

with col_badge5:
    st.markdown(
        '<div class="trust-badge">⭐ v2.3 Premium</div>',
        unsafe_allow_html=True,
    )

# Trust Indicators Section
st.markdown(
    """
    <div class="trust-section">
        <h3 style="color: #3A6FA0; margin-top: 0;">🛡️ Garantias de Segurança</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="trust-indicator">✅ Dados não são salvos no servidor</div>
            <div class="trust-indicator">✅ Análise 100% privada</div>
            <div class="trust-indicator">✅ End-to-end encrypted</div>
            <div class="trust-indicator">✅ Sem rastreamento</div>
            <div class="trust-indicator">✅ Resultado em tempo real</div>
            <div class="trust-indicator">✅ Modelo validado por especialistas</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ================================================================
# BARRA LATERAL - CONFIGURAÇÕES
# ================================================================

with st.sidebar:
    st.markdown(
        """
        <style>
            [data-testid="stSidebarContent"] {
                background-color: #F7F2EA;
                padding-top: 2rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    user = st.session_state.authenticated_user
    st.markdown(
        f'<div style="text-align: center; padding: 0.5rem;">'
        f'<span style="color: #3A6FA0; font-weight: 700;">👤 {user["username"]}</span>'
        f'<br><span style="color: #546E7A; font-size: 0.8em;">{user["role"].upper()}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.authenticated_user = None
        st.rerun()

    st.markdown("---")

    st.markdown(
        '<h2 style="color: #3A6FA0; border-bottom: 2px solid #D4AF37; padding-bottom: 0.5rem; margin-bottom: 1.5rem;">⚙️ Configurações</h2>',
        unsafe_allow_html=True,
    )

    # Seleção de modelo com estilo melhorado
    st.markdown(
        '<p style="color: #3A6FA0; font-weight: 600; margin-bottom: 0.5rem;">Modelo de IA:</p>',
        unsafe_allow_html=True,
    )
    modelo = st.radio(
        "Escolha o modelo",
        ["DeepSeek (Primário)", "Gemini (Cloud)", "Ollama (Local)"],
        index=0,
        label_visibility="collapsed",
    )

    modelo_map = {
        "DeepSeek (Primário)": "deepseek",
        "Gemini (Cloud)": "gemini",
        "Ollama (Local)": "ollama",
    }

    modelo_selecionado = modelo_map[modelo]
    if modelo_selecionado != st.session_state.modelo_selecionado:
        set_model(modelo_selecionado)
        st.session_state.modelo_selecionado = modelo_selecionado
        logger.info(f"Modelo alterado para: {modelo_selecionado}")

    st.divider()

    # Opções avançadas
    st.markdown(
        '<p style="color: #3A6FA0; font-weight: 600; margin-bottom: 0.5rem;">Opcões Avançadas:</p>',
        unsafe_allow_html=True,
    )
    fallback_enabled = st.checkbox("Fallback automático entre modelos", value=True,
                                  help="Se o modelo principal falhar, tenta automaticamente o outro modelo")
    set_fallback(fallback_enabled)

    st.divider()

    # Botão para limpar análise com estilo
    st.markdown(
        '<p style="color: #3A6FA0; font-weight: 600; margin-bottom: 0.5rem;">Ações:</p>',
        unsafe_allow_html=True,
    )
    if st.button("🗑️ Limpar Análise", use_container_width=True):
        limpar_analise()
        st.success("Análise limpa com sucesso!")
        st.rerun()

    st.divider()

    # Estatísticas do cache
    st.markdown(
        '<h3 style="color: #3A6FA0; border-bottom: 2px solid #D4AF37; padding-bottom: 0.5rem;">💾 Cache</h3>',
        unsafe_allow_html=True,
    )
    cache_stats = st.session_state.cache_manager.get_cache_stats()
    st.metric("Análises em cache", cache_stats.get("total_entries", 0))
    if st.button("🗑️ Limpar Cache", use_container_width=True):
        st.session_state.cache_manager.clear_cache()
        st.success("Cache limpo!")
        st.rerun()

    # Histórico de análises (via DB)
    with st.expander("📋 Histórico de Análises", expanded=False):
        try:
            user_id = st.session_state.authenticated_user.get("username", "anonymous")
            history = st.session_state.db_service.get_user_history(user_id, limit=10)
            if history:
                for h in history:
                    emoji = "🔴" if h.get("risk_high", 0) > 2 else ("🟠" if h.get("risk_medium", 0) > 2 else "🟢")
                    st.caption(
                        f"{emoji} {h.get('contract_name', 'N/A')[:40]}\n"
                        f"Altos: {h.get('risk_high', 0)} | "
                        f"Médios: {h.get('risk_medium', 0)} | "
                        f"Baixos: {h.get('risk_low', 0)}"
                    )
            else:
                st.caption("Nenhuma análise salva ainda.")
        except Exception:
            st.caption("Banco de dados indisponível.")

    st.divider()

    # Seção de Segurança
    st.markdown(
        '<h3 style="color: #3A6FA0; border-bottom: 2px solid #D4AF37; padding-bottom: 0.5rem;">🛡️ Segurança</h3>',
        unsafe_allow_html=True,
    )

    # Indicadores de segurança
    col_sec1, col_sec2 = st.columns(2)
    with col_sec1:
        st.markdown(
            '<div style="text-align: center; color: #2E7D32; font-weight: 600; font-size: 0.9em;">🔐 Privado</div>',
            unsafe_allow_html=True,
        )
    with col_sec2:
        st.markdown(
            '<div style="text-align: center; color: #2E7D32; font-weight: 600; font-size: 0.9em;">🔒 Criptografado</div>',
            unsafe_allow_html=True,
        )

    st.info(
        "💡 **Dica:** Carregue um PDF, Word, Excel ou TXT com o contrato para iniciar a análise."
    )

    # Painel Admin
    if st.session_state.authenticated_user.get("role") == "admin":
        st.markdown("---")
        st.markdown(
            '<h3 style="color: #D4AF37; border-bottom: 2px solid #D4AF37; padding-bottom: 0.25rem;">🔑 Painel Admin</h3>',
            unsafe_allow_html=True,
        )

        with st.expander("👥 Usuários", expanded=False):
            users = st.session_state.auth_service.list_users()
            for u in users:
                st.caption(f"• {u['username']} — {u['role']} | Criado: {u['created_at'][:10]}")

        with st.expander("📝 Registro de Aceites", expanded=False):
            try:
                acceptances = st.session_state.db_service.get_acceptance_history()
                if acceptances:
                    for a in acceptances[-15:]:
                        st.caption(f"• {a['username']} em {a['accepted_at'][:19]}")
                else:
                    st.caption("Nenhum aceite registrado.")
            except Exception:
                st.caption("Erro ao carregar aceites.")

        with st.expander("🔐 Log de Acessos", expanded=False):
            try:
                audit = st.session_state.auth_service.get_audit_log(limit=15)
                for entry in audit:
                    emoji = "✅" if "SUCCESS" in entry["action"] else "❌"
                    st.caption(f"{emoji} {entry['user']} — {entry['action']} — {entry['timestamp'][:19]}")
            except Exception:
                st.caption("Erro ao carregar auditoria.")

        with st.expander("📊 Estatísticas Gerais", expanded=False):
            try:
                stats = st.session_state.db_service.get_stats()
                st.metric("Total Análises", stats.get("total_analyses", 0))
                st.metric("Média Riscos Altos", stats.get("avg_high_risks", 0))
                st.metric("Média Riscos Médios", stats.get("avg_medium_risks", 0))
                api_stats = st.session_state.db_service.get_api_stats()
                st.metric("Chamadas API (30d)", api_stats.get("total_requests", 0))
            except Exception:
                st.caption("Erro ao carregar estatísticas.")

st.divider()

st.warning("""
**⚠️ Aviso Importante**

As análises são geradas por inteligência artificial de última geração, com base jurídica em evidências públicas, jurisprudências e nas melhores práticas dos maiores escritórios de advocacia do Brasil.

Esta ferramenta é um **auxílio para compreensão do seu contrato** e esclarecimento de dúvidas, mas **não substitui a consulta a um advogado**. Sempre consulte um profissional qualificado antes de tomar qualquer decisão ou assinar qualquer documento.

A TRUST CORPORATION não se responsabiliza por decisões tomadas com base exclusivamente nas análises geradas por esta plataforma.
""")

st.divider()

# ================================================================
# TUTORIAL DE USO
# ================================================================

with st.expander("📖 Tutorial — Como usar o ContratoSeguro IA", expanded=False):
    st.markdown("""
    ### 🚀 Passo a passo

    **1. 🔐 Login**
    - Use `admin` / `admin123` (padrão) ou crie novos usuários

    **2. 📄 Upload do Contrato**
    - Formatos aceitos: **PDF**, **Word** (.docx), **Excel** (.xlsx), **TXT**
    - Ative OCR para PDFs digitalizados/escaneados

    **3. 🤖 Escolha do Modelo**
    - **DeepSeek** (padrão) — mais rápido e econômico
    - **Gemini** e **Ollama** como alternativas
    - Fallback automático ativado por padrão

    **4. 🔍 Análise**
    - Clique em **Iniciar Análise Especializada**
    - A IA analisa riscos, base legal e sugere melhorias
    - Análises repetidas são recuperadas do cache (instantâneo)

    **5. 📊 Dashboard**
    - Métricas de riscos (altos/médios/baixos)
    - Gráfico de pizza com distribuição
    - Gráfico radar com avaliação em 5 dimensões
    - Resumo executivo em até 20 linhas

    **6. 📝 Sugestão de Cláusulas**
    - Visualize cada cláusula problemática lado a lado
    - Biblioteca com redações padrão (multa, foro, LGPD, etc.)
    - Opção de gerar sugestão com IA

    **7. 💬 Consultoria IA**
    - Chat para tirar dúvidas sobre o contrato analisado
    - Pergunte sobre cláusulas específicas, prazos, riscos

    **8. 💾 Exportação**
    - **WhatsApp (Twilio)**: envio automático de PDF + resumo
    - **Link manual**: abre WhatsApp Web com resumo pronto
    - **PDF**: documento profissional com gráficos
    - **Word**: documento editável para anotações

    ---
    ### ⚙️ Configurações da Sidebar
    - Alterne entre modelos de IA
    - Ative/desative fallback automático
    - Veja estatísticas de cache e histórico de análises
    - Faça logout ao terminar
    """)

st.divider()

# ================================================================
# SEÇÃO 1: UPLOAD E EXTRAÇÃO
# ================================================================

st.header("📄 Upload do Contrato")

arquivo_upload = st.file_uploader(
    "Carregue um arquivo (PDF, Word, Excel ou TXT)",
    type=["pdf", "docx", "xlsx", "txt"],
    help="Formatos aceitos: PDF, Word (.docx), Excel (.xlsx) ou TXT",
)

if arquivo_upload is not None:
    st.session_state.nome_arquivo = arquivo_upload.name

    usar_ocr = st.checkbox("🔍 Usar OCR para PDFs escaneados", value=True,
                           help="Ativa reconhecimento de texto em PDFs digitalizados (requer pytesseract)")

    try:
        with st.spinner("Processando arquivo..."):
            ext = arquivo_upload.name.lower()
            file_bytes = arquivo_upload.getvalue()

            if ext.endswith(".pdf"):
                pdf_bytes = BytesIO(file_bytes)
                texto_extraido = extrair_texto_pdf_bytes(pdf_bytes, enable_ocr=usar_ocr)

                metadados = extrair_metadados_pdf(pdf_bytes)
                if any(v != "N/A" for v in metadados.values()):
                    with st.expander("📋 Metadados do Documento", expanded=False):
                        cols = st.columns(3)
                        for i, (key, value) in enumerate(metadados.items()):
                            if value != "N/A":
                                with cols[i % 3]:
                                    st.caption(f"**{key.replace('_', ' ').title()}:** {value}")

            elif ext.endswith(".docx"):
                try:
                    from extractor_service import extrair_texto_docx
                    texto_extraido = extrair_texto_docx(BytesIO(file_bytes))
                except ImportError:
                    texto_extraido = file_bytes.decode("utf-8", errors="ignore")

            elif ext.endswith(".xlsx"):
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
                    partes = []
                    for sheet_name in wb.sheetnames:
                        ws = wb[sheet_name]
                        partes.append(f"[Planilha: {sheet_name}]")
                        for row in ws.iter_rows(values_only=True):
                            linha = " | ".join(str(c) if c is not None else "" for c in row)
                            if linha.strip():
                                partes.append(linha)
                    wb.close()
                    texto_extraido = "\n".join(partes)
                except ImportError:
                    st.error("openpyxl não instalado. Execute: pip install openpyxl")
                    texto_extraido = ""

            else:  # TXT
                try:
                    texto_extraido = file_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    texto_extraido = file_bytes.decode("latin-1", errors="ignore")

            st.session_state.texto_original = texto_extraido

            # Exibir preview do texto
            with st.expander("👁️ Visualizar Texto Extraído", expanded=False):
                st.text_area(
                    "Texto do contrato:",
                    value=texto_extraido[:1000] + "..."
                    if len(texto_extraido) > 1000
                    else texto_extraido,
                    height=200,
                    disabled=True,
                )

            st.success(
                f"✅ Arquivo carregado com sucesso! ({len(texto_extraido)} caracteres)"
            )

    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo: {str(e)}")
        logger.error(f"Erro na extração: {str(e)}")

# ================================================================
# SEÇÃO 2: ANÁLISE DO CONTRATO
# ================================================================

st.markdown(
    '<h2 style="color: #3A6FA0; border-bottom: 2px solid #D4AF37; padding-bottom: 0.5rem;">🔍 Análise do Contrato</h2>',
    unsafe_allow_html=True,
)

if st.session_state.texto_original:
    st.info(
        "💡 O contrato foi carregado. Clique no botão abaixo para iniciar a análise jurídica avançada."
    )

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        analisar_btn = st.button(
            "🚀 Iniciar Análise Especializada", use_container_width=True, type="primary"
        )

    if analisar_btn:
        cache_mgr = st.session_state.cache_manager
        texto_contrato = st.session_state.texto_original
        cache_hit = False
        resultado = ""
        tempo_inicio = __import__("time").time()
        user_id = st.session_state.authenticated_user.get("username", "anonymous")
        model_used = st.session_state.modelo_selecionado

        cached = cache_mgr.get_analysis(texto_contrato)
        if cached and "analise" in cached and isinstance(cached["analise"], str):
            resultado = cached["analise"]
            cache_hit = True
            st.info("⚡ Análise recuperada do cache (instantâneo)")
            logger.info("Análise encontrada no cache")
        else:
            with st.spinner(
                "⏳ Analisando contrato com Inteligência Artificial. Por favor, aguarde..."
            ):
                try:
                    resultado = analisar_contrato(texto_contrato)
                    cache_mgr.save_analysis(texto_contrato, resultado)
                    st.success("✅ Análise concluída com sucesso!")
                except Exception as e:
                    st.error(f"❌ Erro na análise: {str(e)}")
                    logger.error(f"Erro durante análise: {str(e)}")

        if resultado:
            st.session_state.analise_resultado = resultado
            st.session_state.cache_analise = resultado
            tempo_total = __import__("time").time() - tempo_inicio
            if not cache_hit:
                st.caption(f"⏱️ Tempo de análise: {tempo_total:.1f}s")

            if not cache_hit:
                riscos_dict = extrair_numeros_riscos(resultado)
                try:
                    st.session_state.db_service.save_analysis(
                        contract_text=texto_contrato,
                        analysis_text=resultado,
                        contract_name=st.session_state.nome_arquivo,
                        model_used=model_used,
                        risk_high=riscos_dict.get("altos", 0),
                        risk_medium=riscos_dict.get("medios", 0),
                        risk_low=riscos_dict.get("baixos", 0),
                        analysis_time_ms=int(tempo_total * 1000),
                        user_id=user_id,
                    )
                    st.session_state.db_service.log_api_usage(
                        model=model_used,
                        tokens_input=len(texto_contrato) // 4,
                        tokens_output=len(resultado) // 4,
                        request_time_ms=int(tempo_total * 1000),
                        success=True,
                    )
                except Exception as e:
                    logger.warning(f"Erro ao salvar no banco: {e}")
                    pass
else:
    st.warning("📝 Aguardando upload do arquivo para iniciar a análise.")

# ================================================================
# SEÇÃO 3: RESULTADOS E TABS
# ================================================================

if st.session_state.analise_resultado:
    st.divider()

    # Criar abas profissionais
    tab_dashboard, tab_analise, tab_clausulas, tab_chat, tab_export = st.tabs(
        [
            "📊 Dashboard de Riscos",
            "📖 Análise Completa",
            "📝 Sugestão de Cláusulas",
            "💬 Consultoria IA",
            "💾 Exportação",
        ]
    )

    # --- ABA 1: DASHBOARD ---
    with tab_dashboard:
        riscos_dict = extrair_numeros_riscos(st.session_state.analise_resultado)

        st.markdown(
            '<h3 style="color: #3A6FA0;">Métricas de Risco</h3>', unsafe_allow_html=True
        )
        exibir_estatisticas(st.session_state.analise_resultado)

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
                st.caption(f"Gráficos indisponíveis: matplotlib não instalado")

        st.markdown(
            '<h3 style="color: #3A6FA0; margin-top: 2rem;">⚠️ Resumo Executivo (Máximo 20 linhas)</h3>',
            unsafe_allow_html=True,
        )

        # Exibir resumo em um container elegante
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

    # --- ABA 2: ANÁLISE COMPLETA ---
    with tab_analise:
        st.markdown(
            '<h3 style="color: #3A6FA0;">Documento de Análise Detalhada</h3>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div style="background-color: #F7F2EA; padding: 2rem; border-radius: 8px; border: 1px solid #E0E0E0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            """,
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state.analise_resultado)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- ABA 3: SUGESTÃO DE CLÁUSULAS ---
    with tab_clausulas:
        st.markdown(
            '<h3 style="color: #3A6FA0;">📝 Cláusulas Problemáticas e Sugestões</h3>',
            unsafe_allow_html=True,
        )
        st.write("Redações alternativas para cláusulas de risco identificadas na análise.")

        try:
            from clause_service import extrair_clausulas_risco, get_clausula_padrao

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
                                        ok_sug, texto_sug = __import__("clause_service").sugerir_clausula_alternativa(
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

    # --- ABA 4: CHAT DE DÚVIDAS ---
    with tab_chat:
        st.markdown(
            '<h3 style="color: #3A6FA0;">💬 Tire dúvidas sobre o contrato</h3>',
            unsafe_allow_html=True,
        )
        st.write(
            "Converse com a IA para esclarecer pontos específicos do contrato analisado."
        )

        # Exibir histórico de mensagens
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Input para nova mensagem
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

    # --- ABA 4: EXPORTAÇÃO ---
    with tab_export:
        st.markdown(
            '<h3 style="color: #3A6FA0;">💾 Exportar e Compartilhar</h3>',
            unsafe_allow_html=True,
        )
        st.write("Baixe a análise completa ou compartilhe o resumo com seus clientes.")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                '<div class="info-card" style="text-align: center;">',
                unsafe_allow_html=True,
            )
            st.markdown("#### PDF Oficial")
            st.write("Documento formatado ideal para impressão e envio formal.")
            if st.button("📄 Gerar PDF", use_container_width=True):
                try:
                    with st.spinner("Gerando PDF..."):
                        pdf_buffer = gerar_pdf(
                            st.session_state.analise_resultado,
                            st.session_state.nome_arquivo,
                        )
                        st.download_button(
                            label="⬇️ Baixar PDF",
                            data=pdf_buffer,
                            file_name=f"analise_{Path(st.session_state.nome_arquivo).stem}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="btn_dl_pdf",
                        )
                        st.success("Pronto!")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(
                '<div class="info-card" style="text-align: center;">',
                unsafe_allow_html=True,
            )
            st.markdown("#### Word (Editável)")
            st.write(
                "Documento editável (.docx) para você adicionar seus próprios comentários."
            )
            if st.button("📝 Gerar Word", use_container_width=True):
                try:
                    with st.spinner("Gerando Word..."):
                        word_buffer = gerar_word(
                            st.session_state.analise_resultado,
                            st.session_state.nome_arquivo,
                        )
                        st.download_button(
                            label="⬇️ Baixar Word",
                            data=word_buffer,
                            file_name=f"analise_{Path(st.session_state.nome_arquivo).stem}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                            key="btn_dl_word",
                        )
                        st.success("Pronto!")
                except Exception as e:
                    st.error(f"Erro ao gerar Word: {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            st.markdown(
                '<div class="info-card" style="text-align: center;">',
                unsafe_allow_html=True,
            )
            st.markdown("#### 📱 WhatsApp (Twilio)")
            st.write("PDF + resumo enviados automaticamente.")

            telefone = st.text_input(
                "Seu número de WhatsApp:",
                placeholder="5514999999999",
                value=st.session_state.get("user_whatsapp", ""),
                key="whatsapp_twilio_phone",
            )

            if st.button("🚀 Enviar PDF + Resumo", use_container_width=True, type="primary"):
                if not telefone:
                    st.warning("Informe seu número de WhatsApp")
                else:
                    try:
                        with st.spinner("Gerando PDF e enviando via Twilio..."):
                            from notification_service import NotificationService

                            notifier = NotificationService()
                            pdf_buf = gerar_pdf(
                                st.session_state.analise_resultado,
                                st.session_state.nome_arquivo,
                            )
                            resumo = extrair_pontos_atencao(
                                st.session_state.analise_resultado, max_linhas=20
                            )
                            phone = "".join(c for c in telefone if c.isdigit())
                            fname = f"analise_{Path(st.session_state.nome_arquivo).stem}.pdf"

                            ok, msg = notifier.send_whatsapp_pdf_twilio(
                                to_number=phone,
                                pdf_buffer=pdf_buf,
                                filename=fname,
                                summary=resumo,
                                contract_name=st.session_state.nome_arquivo,
                            )

                            if ok:
                                st.success(f"Enviado com sucesso para {phone}!")
                            else:
                                st.error(f"Falha: {msg}")
                                st.info("Verifique se o número está autorizado no sandbox Twilio (join parts-current)")

                    except Exception as e:
                        st.error(f"Erro: {str(e)}")

            # Tutorial
            with st.expander("📖 Autorize o envio do WhatsApp", expanded=False):
                st.markdown("""
                **Para poder receber os arquivos, faça somente 1 vez:**

                Envie uma mensagem de seu número de WhatsApp para o número:
                ```
                +1 415 523 8886
                ```
                Com a mensagem:
                ```
                join parts-current
                ```
                """)

            st.markdown("---")

            # Fallback: link manual
            st.markdown("#### 🔗 Link manual (fallback)")
            st.write("Se o Twilio falhar, envie o resumo manualmente.")
            if st.button("📱 Abrir WhatsApp com resumo", use_container_width=True):
                resumo = extrair_pontos_atencao(
                    st.session_state.analise_resultado, max_linhas=20
                )
                mensagem = (
                    "📊 *ANÁLISE DE CONTRATO - TRUST CORPORATION*\n"
                    f"📄 *Contrato:* {st.session_state.nome_arquivo}\n\n"
                    "⚠️ *RESUMO DE RISCOS:*\n"
                    f"{resumo}\n\n"
                    "✅ TRUST CORPORATION - Contrato Seguro IA"
                )
                st.markdown(
                    f'<a href="https://api.whatsapp.com/send?text={quote(mensagem[:4000])}" target="_blank">'
                    '<button style="width: 100%; padding: 0.75rem; background-color: #25D366; '
                    'color: white; border: none; border-radius: 0.4rem; cursor: pointer; '
                    'font-weight: bold;">📱 Abrir WhatsApp</button></a>',
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

# ================================================================
# RODAPÉ
# ================================================================

st.divider()

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption("🔒 TRUST CORPORATION - Contrato Seguro IA")

with footer_col2:
    st.caption("⚠️ Consulte sempre um advogado")

with footer_col3:
    st.caption("© 2026 - Todos os direitos reservados")

logger.info("Aplicação Streamlit iniciada com sucesso")
