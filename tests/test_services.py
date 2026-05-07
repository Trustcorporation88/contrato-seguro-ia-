"""
Testes para os módulos cache_manager.py e clause_service.py.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cache_manager import CacheManager
import clause_service
from clause_service import (
    CLAUSULAS_PADRAO,
    RISCO_BLOCO_PATTERN,
    extrair_clausulas_risco,
    extrair_numeros_riscos,
    extrair_pontos_atencao,
    get_clausula_padrao,
    listar_tipos_clausulas,
)


# ========== CacheManager ==========

def test_cache_save_and_retrieve():
    """Deve salvar e recuperar uma análise do cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(cache_dir=tmpdir, max_history=10)
        cache.save_analysis("contrato de teste", {"analise": "resultado"})
        result = cache.get_analysis("contrato de teste")
        assert result is not None
        assert result["analise"]["analise"] == "resultado"


def test_cache_duplicate_detection():
    """Contratos iguais devem retornar cache hit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(cache_dir=tmpdir, max_history=10)
        cache.save_analysis("mesmo texto", "analise 1")
        hit = cache.get_analysis("mesmo texto")
        assert hit is not None
        assert hit["analise"] == "analise 1"


def test_cache_different_contracts():
    """Contratos diferentes não devem dar cache hit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(cache_dir=tmpdir, max_history=10)
        cache.save_analysis("texto A", "analise A")
        hit = cache.get_analysis("texto B")
        assert hit is None


def test_cache_max_history():
    """Deve respeitar o limite máximo de histórico."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(cache_dir=tmpdir, max_history=3)
        for i in range(5):
            cache.save_analysis(f"contrato {i}", f"analise {i}")
        stats = cache.get_cache_stats()
        assert stats["total_entries"] <= 3


def test_cache_clear():
    """Deve limpar todo o cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(cache_dir=tmpdir, max_history=10)
        cache.save_analysis("texto", "analise")
        cache.clear_cache()
        stats = cache.get_cache_stats()
        assert stats["total_entries"] == 0


def test_cache_remove_entry():
    """Deve remover uma entrada específica."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = CacheManager(cache_dir=tmpdir, max_history=10)
        cache.save_analysis("texto", "analise")
        result = cache.remove_entry("texto")
        assert result is True
        assert cache.get_analysis("texto") is None


# ========== ClauseService ==========

def test_risco_bloco_pattern_alto():
    """Deve detectar RISCO ALTO no texto."""
    match = RISCO_BLOCO_PATTERN.search("**🔴 RISCO ALTO**")
    assert match is not None
    assert "ALTO" in match.group(1)


def test_risco_bloco_pattern_medio():
    """Deve detectar RISCO MÉDIO no texto."""
    match = RISCO_BLOCO_PATTERN.search("**🟠 RISCO MÉDIO**")
    assert match is not None


def test_risco_bloco_pattern_baixo():
    """Deve detectar RISCO BAIXO no texto."""
    match = RISCO_BLOCO_PATTERN.search("**🟢 RISCO BAIXO**")
    assert match is not None


def test_extrair_numeros_riscos():
    """Deve extrair contagem correta de riscos."""
    texto = """
    **🔴 RISCO ALTO** - Cláusula 1
    **🔴 RISCO ALTO** - Cláusula 2
    **🟠 RISCO MÉDIO** - Cláusula 3
    **🟢 RISCO BAIXO** - Cláusula 4
    """
    resultado = extrair_numeros_riscos(texto)
    assert resultado["altos"] == 2
    assert resultado["medios"] == 1
    assert resultado["baixos"] == 1
    assert resultado["total"] == 4


def test_extrair_numeros_riscos_vazio():
    """Deve retornar zeros para texto sem riscos."""
    resultado = extrair_numeros_riscos("texto sem riscos")
    assert resultado["total"] == 0


def test_extrair_clausulas_risco():
    """Deve extrair cláusulas estruturadas da análise."""
    analise = """
    **🔴 RISCO ALTO**
    **Cláusula:** 5.2 - Multa
    **Problema:** Multa excessiva de 50%
    **Base legal:** Art. 412 CC

    **🟠 RISCO MÉDIO**
    **Cláusula:** 8.1 - Foro
    **Problema:** Foro distante
    **Base legal:** Art. 421 CC
    """
    clausulas = extrair_clausulas_risco(analise)
    assert len(clausulas) == 2
    assert clausulas[0]["nivel"] == "alto"
    assert "Multa" in clausulas[0]["texto_clausula"]
    assert clausulas[1]["nivel"] == "medio"


def test_get_clausula_padrao():
    """Deve retornar cláusulas padrão da biblioteca."""
    multa = get_clausula_padrao("multa_rescisoria")
    assert multa is not None
    assert "MULTA RESCISÓRIA" in multa

    foro = get_clausula_padrao("foro_eleicao")
    assert foro is not None
    assert "FORO DE ELEIÇÃO" in foro

    inexistente = get_clausula_padrao("tipo_inexistente")
    assert inexistente is None


def test_listar_tipos_clausulas():
    """Deve listar os 5 tipos de cláusulas padrão."""
    tipos = listar_tipos_clausulas()
    assert len(tipos) == 5
    assert "multa_rescisoria" in tipos
    assert "lgpd" in tipos


def test_extrair_pontos_atencao():
    """Deve extrair resumo executivo da análise."""
    analise = """
    **🔴 RISCO ALTO**
    **Cláusula:** 5.2 - Multa Contratual
    **Problema:** Multa de 50% sobre o valor do contrato, excessiva.
    """
    pontos = extrair_pontos_atencao(analise, max_linhas=10)
    assert "Multa Contratual" in pontos
    assert "50%" in pontos


def test_extrair_pontos_atencao_vazio():
    """Deve retornar mensagem padrão para análise sem riscos."""
    pontos = extrair_pontos_atencao("texto sem estrutura de risco", max_linhas=10)
    assert len(pontos) > 0


def test_sugerir_clausula_sem_gemini_disponivel():
    """Módulo deve falhar graciosamente se google-genai não carregar."""
    original_available = clause_service.GEMINI_AVAILABLE
    try:
        clause_service.GEMINI_AVAILABLE = False
        ok, mensagem = clause_service.sugerir_clausula_alternativa(
            "Cláusula original",
            "Problema",
            "Base legal",
        )
    finally:
        clause_service.GEMINI_AVAILABLE = original_available

    assert ok is False
    assert "google-genai" in mensagem


if __name__ == "__main__":
    # Cache
    test_cache_save_and_retrieve()
    test_cache_duplicate_detection()
    test_cache_different_contracts()
    test_cache_max_history()
    test_cache_clear()
    test_cache_remove_entry()

    # Clause
    test_risco_bloco_pattern_alto()
    test_risco_bloco_pattern_medio()
    test_risco_bloco_pattern_baixo()
    test_extrair_numeros_riscos()
    test_extrair_numeros_riscos_vazio()
    test_extrair_clausulas_risco()
    test_get_clausula_padrao()
    test_listar_tipos_clausulas()
    test_extrair_pontos_atencao()
    test_extrair_pontos_atencao_vazio()
    test_sugerir_clausula_sem_gemini_disponivel()

    print("Todos os testes de cache_manager e clause_service passaram!")
