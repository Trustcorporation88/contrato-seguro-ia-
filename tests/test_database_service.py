"""
Testes para o módulo database_service.py.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database_service import DatabaseService


def _temp_db():
    """Cria um DatabaseService temporário para testes."""
    td = tempfile.TemporaryDirectory()
    db = DatabaseService(db_path=str(Path(td.name) / "test.db"))
    return db, td


def test_init_db():
    """Deve criar tabelas sem erro."""
    db, td = _temp_db()
    stats = db.get_stats()
    assert stats["total_analyses"] == 0


def test_save_analysis():
    """Deve salvar uma análise e retornar ID."""
    db, td = _temp_db()
    aid = db.save_analysis(
        contract_text="Contrato de teste",
        analysis_text="Análise do contrato",
        contract_name="teste.pdf",
        model_used="deepseek",
        risk_high=2,
        risk_medium=3,
        risk_low=1,
        user_id="admin",
    )
    assert aid > 0
    stats = db.get_stats()
    assert stats["total_analyses"] == 1


def test_save_analysis_dedup():
    """Deve fazer upsert por hash (INSERT OR REPLACE)."""
    db, td = _temp_db()
    db.save_analysis("mesmo texto", "analise 1", contract_name="a.pdf", user_id="u1")
    db.save_analysis("mesmo texto", "analise 2", contract_name="b.pdf", user_id="u1")
    stats = db.get_stats()
    assert stats["total_analyses"] == 1


def test_get_analysis_by_hash():
    """Deve recuperar análise por hash do texto."""
    db, td = _temp_db()
    db.save_analysis("texto unico", "resultado unico", contract_name="u.pdf")
    result = db.get_analysis_by_hash("texto unico")
    assert result is not None
    assert result["analysis_text"] == "resultado unico"


def test_get_analysis_by_hash_missing():
    """Deve retornar None para texto não salvo."""
    db, td = _temp_db()
    result = db.get_analysis_by_hash("nunca salvo")
    assert result is None


def test_get_user_history():
    """Deve retornar histórico do usuário."""
    db, td = _temp_db()
    db.save_analysis("t1", "a1", user_id="user_a")
    db.save_analysis("t2", "a2", user_id="user_a")
    db.save_analysis("t3", "a3", user_id="user_b")
    history = db.get_user_history("user_a", limit=10)
    assert len(history) == 2


def test_get_stats():
    """Deve retornar estatísticas agregadas."""
    db, td = _temp_db()
    db.save_analysis("t1", "a1", risk_high=3, risk_medium=2, risk_low=1)
    db.save_analysis("t2", "a2", risk_high=1, risk_medium=1, risk_low=5)
    stats = db.get_stats()
    assert stats["total_analyses"] == 2
    assert stats["avg_high_risks"] > 0
    assert len(stats["recent"]) == 2


def test_log_api_usage():
    """Deve registrar uso de API sem erro."""
    db, td = _temp_db()
    db.log_api_usage("deepseek", tokens_input=100, tokens_output=50, request_time_ms=2000)
    stats = db.get_api_stats(days=30)
    assert stats["total_requests"] == 1
    assert stats["total_input_tokens"] == 100


def test_log_acceptance():
    """Deve registrar aceite de termos."""
    db, td = _temp_db()
    ok = db.log_acceptance("joao", "192.168.1.1")
    assert ok is True
    history = db.get_acceptance_history()
    assert len(history) == 1
    assert history[0]["username"] == "joao"


def test_search_analyses():
    """Deve buscar análises via FTS5."""
    db, td = _temp_db()
    db.save_analysis("Cláusula de multa contratual", "Risco alto detectado", contract_name="c1.pdf")
    results = db.search_analyses("multa", limit=5)
    assert len(results) >= 1


def test_delete_analysis():
    """Deve remover uma análise."""
    db, td = _temp_db()
    aid = db.save_analysis("t1", "a1")
    ok = db.delete_analysis(aid)
    assert ok is True
    assert db.get_analysis_by_id(aid) is None


def test_export_to_json():
    """Deve exportar análises para JSON."""
    import tempfile
    db, td = _temp_db()
    db.save_analysis("t1", "a1", contract_name="teste.pdf")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        f.close()
        ok = db.export_to_json(f.name)
        assert ok is True
        import json
        with open(f.name) as jf:
            data = json.load(jf)
        assert len(data) == 1


if __name__ == "__main__":
    test_init_db()
    test_save_analysis()
    test_save_analysis_dedup()
    test_get_analysis_by_hash()
    test_get_analysis_by_hash_missing()
    test_get_user_history()
    test_get_stats()
    test_log_api_usage()
    test_log_acceptance()
    test_search_analyses()
    test_delete_analysis()
    test_export_to_json()
    print("Todos os testes de database_service.py passaram!")
