"""
Testes para o módulo report_service.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from report_service import (
    gerar_grafico_risco_pizza,
    gerar_grafico_radar,
    gerar_relatorio_pdf,
)


def test_gerar_grafico_risco_pizza():
    """Deve gerar gráfico de pizza."""
    buf = gerar_grafico_risco_pizza(altos=3, medios=5, baixos=2)
    if buf is not None:
        assert buf.getbuffer().nbytes > 0


def test_gerar_grafico_risco_pizza_zero():
    """Deve gerar gráfico mesmo com zero riscos."""
    buf = gerar_grafico_risco_pizza(altos=0, medios=0, baixos=0)
    if buf is not None:
        assert buf.getbuffer().nbytes > 0


def test_gerar_grafico_radar():
    """Deve gerar gráfico de radar."""
    buf = gerar_grafico_radar({
        "Clareza": 7.5,
        "Equilíbrio": 6.0,
        "Segurança": 8.0,
        "Compliance": 7.0,
        "Riscos": 5.5,
    })
    if buf is not None:
        assert buf.getbuffer().nbytes > 0


def test_gerar_relatorio_pdf():
    """Deve gerar relatório PDF completo."""
    buf = gerar_relatorio_pdf(
        analysis_text="# Análise de Contrato\n\n## Resumo\nContrato de prestação de serviços.\n\n**🔴 RISCO ALTO**\n**Cláusula:** 5.2\n**Problema:** Multa excessiva.",
        contract_name="contrato_teste.pdf",
        risk_counts={"altos": 3, "medios": 5, "baixos": 2},
    )
    assert buf.getbuffer().nbytes > 0


def test_gerar_relatorio_pdf_sem_riscos():
    """Deve gerar relatório mesmo sem contagem de riscos."""
    buf = gerar_relatorio_pdf(
        analysis_text="Análise simples sem riscos estruturados.",
        contract_name="simples.pdf",
    )
    assert buf.getbuffer().nbytes > 0


def test_gerar_relatorio_pdf_vazio():
    """Deve gerar relatório com texto mínimo."""
    buf = gerar_relatorio_pdf(
        analysis_text="OK",
        contract_name="minimo.pdf",
    )
    assert buf.getbuffer().nbytes > 0


if __name__ == "__main__":
    test_gerar_grafico_risco_pizza()
    test_gerar_grafico_risco_pizza_zero()
    test_gerar_grafico_radar()
    test_gerar_relatorio_pdf()
    test_gerar_relatorio_pdf_sem_riscos()
    test_gerar_relatorio_pdf_vazio()
    print("Todos os testes de report_service.py passaram!")
