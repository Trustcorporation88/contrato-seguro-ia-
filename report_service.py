"""
report_service.py - Serviço de Relatórios Avançados com Gráficos

Gera relatórios visuais com gráficos de risco, timeline de obrigações,
e comparativos de cláusulas.
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.info("matplotlib não instalado. Gráficos desabilitados.")


COLORS_TRUST = {
    "primary": "#1B3A57",
    "secondary": "#2D5A3D",
    "accent": "#D4AF37",
    "danger": "#C41E3A",
    "warning": "#FF9500",
    "success": "#2E7D32",
    "text_primary": "#1B3A57",
    "text_secondary": "#546E7A",
}


def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """Converte cor hex para RGB (0-1)."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))


def gerar_grafico_risco_pizza(
    altos: int, medios: int, baixos: int
) -> Optional[BytesIO]:
    """Gera gráfico de pizza com distribuição de riscos."""
    if not MATPLOTLIB_AVAILABLE:
        return None

    try:
        fig, ax = plt.subplots(figsize=(3.5, 2.8))
        sizes = [altos, medios, baixos]
        labels = [f"Altos ({altos})", f"Médios ({medios})", f"Baixos ({baixos})"]
        colors_pie = [
            _hex_to_rgb(COLORS_TRUST["danger"]),
            _hex_to_rgb(COLORS_TRUST["warning"]),
            _hex_to_rgb(COLORS_TRUST["success"]),
        ]
        explode = (0.05, 0.02, 0)

        if sum(sizes) == 0:
            sizes = [1, 1, 1]
            labels = ["Altos (0)", "Médios (0)", "Baixos (0)"]

        ax.pie(
            sizes,
            explode=explode,
            labels=labels,
            colors=colors_pie,
            autopct="%1.1f%%",
            shadow=False,
            startangle=140,
            textprops={"fontsize": 10, "fontweight": "bold"},
        )
        ax.set_title("Distribuição de Riscos", fontsize=12, fontweight="bold", color=COLORS_TRUST["primary"])

        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", transparent=True)
        plt.close()
        buf.seek(0)
        return buf
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico de pizza: {e}")
        return None


def gerar_grafico_radar(dimensoes: Dict[str, float]) -> Optional[BytesIO]:
    """
    Gera gráfico de radar com avaliação do contrato em 5 dimensões.

    Args:
        dimensoes: Dict com nome da dimensão -> nota (0-10)
    """
    if not MATPLOTLIB_AVAILABLE:
        return None

    try:
        categories = list(dimensoes.keys())
        values = list(dimensoes.values())

        N = len(categories)
        angles = [n / float(N) * 2 * 3.14159 for n in range(N)]
        angles += angles[:1]
        values += values[:1]

        fig, ax = plt.subplots(figsize=(3.5, 3.5), subplot_kw=dict(polar=True))
        ax.set_theta_offset(3.14159 / 2)
        ax.set_theta_direction(-1)

        ax.fill(angles, values, alpha=0.25, color=_hex_to_rgb(COLORS_TRUST["primary"]))
        ax.plot(angles, values, color=_hex_to_rgb(COLORS_TRUST["primary"]), linewidth=2)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=8, color=COLORS_TRUST["text_primary"])
        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=6, color="gray")
        ax.set_title("Avaliação do Contrato", fontsize=12, fontweight="bold", color=COLORS_TRUST["primary"], pad=20)

        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close()
        buf.seek(0)
        return buf
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico de radar: {e}")
        return None


def gerar_relatorio_pdf(
    analysis_text: str,
    contract_name: str,
    risk_counts: Optional[Dict[str, int]] = None,
    company_name: str = "TRUST CORPORATION",
    output_buffer: Optional[BytesIO] = None,
) -> BytesIO:
    """
    Gera um relatório PDF profissional com gráficos.

    Args:
        analysis_text: Texto da análise
        contract_name: Nome do contrato
        risk_counts: Dict {'altos': int, 'medios': int, 'baixos': int}
        company_name: Nome da empresa
        output_buffer: Buffer opcional para salvar o PDF

    Returns:
        BytesIO com o PDF gerado
    """
    if output_buffer is None:
        output_buffer = BytesIO()

    doc = SimpleDocTemplate(
        output_buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=1.5 * cm,
        title=f"Análise - {contract_name}",
        author=company_name,
    )

    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        "TrustTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor(COLORS_TRUST["primary"]),
        spaceAfter=6,
        alignment=1,
        fontName="Helvetica-Bold",
    )

    subtitulo_style = ParagraphStyle(
        "TrustSubtitle",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor(COLORS_TRUST["text_secondary"]),
        spaceAfter=12,
        alignment=1,
        fontName="Helvetica",
    )

    heading_style = ParagraphStyle(
        "TrustHeading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor(COLORS_TRUST["primary"]),
        spaceAfter=8,
        spaceBefore=16,
        borderPadding=(0, 0, 2, 0),
        fontName="Helvetica-Bold",
    )

    body_style = ParagraphStyle(
        "TrustBody",
        parent=styles["BodyText"],
        fontSize=10,
        alignment=4,
        fontName="Helvetica",
        textColor=colors.HexColor(COLORS_TRUST["text_primary"]),
        leading=14,
    )

    risk_style = ParagraphStyle(
        "TrustRisk",
        parent=styles["BodyText"],
        fontSize=10,
        alignment=4,
        fontName="Helvetica",
        leading=14,
    )

    content = []

    content.append(Paragraph(company_name, titulo_style))
    content.append(Paragraph("Análise Inteligente de Contratos", subtitulo_style))
    content.append(Spacer(1, 0.3 * cm))

    divisor_style = TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 2, colors.HexColor(COLORS_TRUST["accent"])),
    ])
    content.append(Table([[""]], colWidths=[18 * cm], style=divisor_style))
    content.append(Spacer(1, 0.5 * cm))

    content.append(Paragraph(f"Contrato: {contract_name}", heading_style))
    content.append(Spacer(1, 0.5 * cm))

    if risk_counts and MATPLOTLIB_AVAILABLE:
        grafico_buf = gerar_grafico_risco_pizza(
            risk_counts.get("altos", 0),
            risk_counts.get("medios", 0),
            risk_counts.get("baixos", 0),
        )
        if grafico_buf:
            img = Image(grafico_buf, width=12 * cm, height=9 * cm)
            content.append(img)
            content.append(Spacer(1, 0.5 * cm))

    content.append(Paragraph("Análise Detalhada", heading_style))
    content.append(Spacer(1, 0.3 * cm))

    for paragrafo in analysis_text.split("\n"):
        if not paragrafo.strip():
            continue

        clean = paragrafo.strip()

        if clean.startswith("# "):
            content.append(Paragraph(clean.replace("# ", ""), heading_style))
        elif clean.startswith("## "):
            content.append(Paragraph(clean.replace("## ", ""), heading_style))
        elif clean.startswith("### "):
            content.append(Paragraph(clean.replace("### ", ""), heading_style))
        elif "RISCO ALTO" in clean or "RISCO MÉDIO" in clean:
            text_formatted = clean.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            content.append(Paragraph(text_formatted, risk_style))
        else:
            text_formatted = clean.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            content.append(Paragraph(text_formatted, body_style))

        content.append(Spacer(1, 0.15 * cm))

    content.append(Spacer(1, 1 * cm))
    footer_line = TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1, colors.HexColor(COLORS_TRUST["accent"])),
    ])
    content.append(Table([[""]], colWidths=[18 * cm], style=footer_line))
    content.append(Spacer(1, 0.3 * cm))
    content.append(
        Paragraph(
            f"<font size=8 color='{COLORS_TRUST['text_secondary']}'>"
            f"Documento gerado por {company_name} - Contrato Seguro IA | "
            "Análise baseada em IA. Sempre consulte um advogado para validação final."
            "</font>",
            styles["Normal"],
        )
    )

    doc.build(content)
    output_buffer.seek(0)
    return output_buffer


if __name__ == "__main__":
    print("=== Teste do ReportService ===\n")

    buf = gerar_grafico_risco_pizza(altos=3, medios=5, baixos=2)
    if buf:
        print(f"Gráfico de pizza gerado: {buf.getbuffer().nbytes} bytes")
    else:
        print("Gráfico não gerado (matplotlib não disponível)")

    radar_buf = gerar_grafico_radar({
        "Clareza": 7.5,
        "Equilíbrio": 6.0,
        "Segurança": 8.0,
        "Compliance": 7.0,
        "Riscos": 5.5,
    })
    if radar_buf:
        print(f"Gráfico de radar gerado: {radar_buf.getbuffer().nbytes} bytes")

    print("\nTeste de relatório PDF...")
    pdf_buf = gerar_relatorio_pdf(
        analysis_text="# Análise de Contrato\n\n## Resumo\nContrato de prestação de serviços.\n\n**🔴 RISCO ALTO**\n**Cláusula:** 5.2\n**Problema:** Multa excessiva.",
        contract_name="contrato_teste.pdf",
        risk_counts={"altos": 3, "medios": 5, "baixos": 2},
    )
    print(f"Relatório PDF gerado: {pdf_buf.getbuffer().nbytes} bytes")
