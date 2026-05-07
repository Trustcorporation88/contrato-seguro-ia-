"""
database_service.py - Serviço de Banco de Dados e Histórico de Análises

Persiste análises, usuários e histórico usando SQLite (zero-config).
Suporta busca full-text e estatísticas agregadas.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from config import compute_hash

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).parent / "cache" / "contrato_seguro.db"


class DatabaseService:
    """
    Serviço de banco de dados para persistência de análises e histórico.
    Usa SQLite com FTS5 para busca full-text.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_conn()
            try:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS analyses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        hash TEXT UNIQUE NOT NULL,
                        contract_name TEXT NOT NULL,
                        contract_text TEXT NOT NULL,
                        analysis_text TEXT NOT NULL,
                        model_used TEXT DEFAULT 'gemini',
                        risk_high INTEGER DEFAULT 0,
                        risk_medium INTEGER DEFAULT 0,
                        risk_low INTEGER DEFAULT 0,
                        contract_size INTEGER DEFAULT 0,
                        analysis_time_ms INTEGER DEFAULT 0,
                        user_id TEXT DEFAULT 'anonymous',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );

                    CREATE INDEX IF NOT EXISTS idx_analyses_hash ON analyses(hash);
                    CREATE INDEX IF NOT EXISTS idx_analyses_user ON analyses(user_id);
                    CREATE INDEX IF NOT EXISTS idx_analyses_created ON analyses(created_at);

                    CREATE VIRTUAL TABLE IF NOT EXISTS analyses_fts USING fts5(
                        contract_name, contract_text, analysis_text,
                        content=analyses, content_rowid=id
                    );

                    CREATE TRIGGER IF NOT EXISTS analyses_ai AFTER INSERT ON analyses BEGIN
                        INSERT INTO analyses_fts(rowid, contract_name, contract_text, analysis_text)
                        VALUES (new.id, new.contract_name, new.contract_text, new.analysis_text);
                    END;

                    CREATE TRIGGER IF NOT EXISTS analyses_ad AFTER DELETE ON analyses BEGIN
                        INSERT INTO analyses_fts(analyses_fts, rowid, contract_name, contract_text, analysis_text)
                        VALUES ('delete', old.id, old.contract_name, old.contract_text, old.analysis_text);
                    END;

                    CREATE TABLE IF NOT EXISTS contract_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        recorded_at TEXT NOT NULL
                    );

                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    tokens_input INTEGER DEFAULT 0,
                    tokens_output INTEGER DEFAULT 0,
                    request_time_ms INTEGER DEFAULT 0,
                    success INTEGER DEFAULT 1,
                    error_message TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS acceptance_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    ip_address TEXT DEFAULT 'local',
                    accepted_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_acceptance_user ON acceptance_log(username);
                """)
                conn.commit()
                logger.info(f"Banco de dados inicializado: {self.db_path}")
            except Exception as e:
                logger.error(f"Erro ao inicializar banco: {e}")
                raise
            finally:
                conn.close()

    def save_analysis(
        self,
        contract_text: str,
        analysis_text: str,
        contract_name: str = "sem_nome",
        model_used: str = "gemini",
        risk_high: int = 0,
        risk_medium: int = 0,
        risk_low: int = 0,
        analysis_time_ms: int = 0,
        user_id: str = "anonymous",
    ) -> int:
        """
        Salva uma análise no banco de dados.

        Returns:
            ID da análise salva
        """
        contract_hash = compute_hash(contract_text)
        now = datetime.now().isoformat()

        with self._lock:
            conn = self._get_conn()
            try:
                cursor = conn.execute(
                    """
                    INSERT OR REPLACE INTO analyses
                        (hash, contract_name, contract_text, analysis_text, model_used,
                         risk_high, risk_medium, risk_low, contract_size, analysis_time_ms,
                         user_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        contract_hash,
                        contract_name,
                        contract_text,
                        analysis_text,
                        model_used,
                        risk_high,
                        risk_medium,
                        risk_low,
                        len(contract_text),
                        analysis_time_ms,
                        user_id,
                        now,
                        now,
                    ),
                )
                conn.commit()
                logger.info(f"Análise salva: {contract_name} (hash: {contract_hash[:16]}...)")
                return cursor.lastrowid
            except Exception as e:
                logger.error(f"Erro ao salvar análise: {e}")
                raise
            finally:
                conn.close()

    def get_analysis_by_hash(self, contract_text: str) -> Optional[Dict[str, Any]]:
        """Recupera análise pelo hash do texto do contrato."""
        contract_hash = compute_hash(contract_text)

        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM analyses WHERE hash = ?", (contract_hash,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_analysis_by_id(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """Recupera análise pelo ID."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_user_history(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Recupera histórico de análises de um usuário."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT id, hash, contract_name, model_used, risk_high, risk_medium,
                       risk_low, contract_size, analysis_time_ms, created_at
                FROM analyses
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def search_analyses(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Busca full-text nas análises salvas."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT a.id, a.hash, a.contract_name, a.model_used, a.created_at,
                       snippet(analyses_fts, 1, '<b>', '</b>', '...', 40) as snippet
                FROM analyses_fts
                JOIN analyses a ON analyses_fts.rowid = a.id
                WHERE analyses_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas agregadas de todas as análises."""
        conn = self._get_conn()
        try:
            total = conn.execute("SELECT COUNT(*) as cnt FROM analyses").fetchone()
            avg_risks = conn.execute(
                """
                SELECT
                    AVG(risk_high) as avg_high,
                    AVG(risk_medium) as avg_medium,
                    AVG(risk_low) as avg_low,
                    MAX(risk_high) as max_high,
                    SUM(risk_high) as total_high
                FROM analyses
                """
            ).fetchone()
            model_usage = conn.execute(
                """
                SELECT model_used, COUNT(*) as cnt
                FROM analyses GROUP BY model_used
                """
            ).fetchall()
            recent = conn.execute(
                """
                SELECT contract_name, risk_high, risk_medium, risk_low, created_at
                FROM analyses ORDER BY created_at DESC LIMIT 10
                """
            ).fetchall()

            return {
                "total_analyses": total["cnt"] if total else 0,
                "avg_high_risks": round(avg_risks["avg_high"] or 0, 1),
                "avg_medium_risks": round(avg_risks["avg_medium"] or 0, 1),
                "avg_low_risks": round(avg_risks["avg_low"] or 0, 1),
                "max_high_risks": avg_risks["max_high"] or 0,
                "total_high_risks": avg_risks["total_high"] or 0,
                "model_usage": {r["model_used"]: r["cnt"] for r in model_usage},
                "recent": [dict(r) for r in recent],
            }
        finally:
            conn.close()

    def log_api_usage(
        self,
        model: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        request_time_ms: int = 0,
        success: bool = True,
        error_message: str = "",
    ) -> None:
        """Registra uso da API para monitoramento de custos."""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    """
                    INSERT INTO api_usage (model, tokens_input, tokens_output,
                        request_time_ms, success, error_message, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        model,
                        tokens_input,
                        tokens_output,
                        request_time_ms,
                        1 if success else 0,
                        error_message,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def get_api_stats(self, days: int = 30) -> Dict[str, Any]:
        """Retorna estatísticas de uso da API."""
        conn = self._get_conn()
        try:
            total = conn.execute(
                f"""
                SELECT
                    COUNT(*) as total_requests,
                    SUM(tokens_input) as total_input,
                    SUM(tokens_output) as total_output,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failures
                FROM api_usage
                WHERE created_at >= datetime('now', '-{days} days')
                """
            ).fetchone()

            by_model = conn.execute(
                f"""
                SELECT model, COUNT(*) as cnt, SUM(tokens_input + tokens_output) as tokens
                FROM api_usage
                WHERE created_at >= datetime('now', '-{days} days')
                GROUP BY model
                """
            ).fetchall()

            return {
                "total_requests": total["total_requests"] or 0,
                "total_input_tokens": total["total_input"] or 0,
                "total_output_tokens": total["total_output"] or 0,
                "failures": total["failures"] or 0,
                "by_model": {r["model"]: {"requests": r["cnt"], "tokens": r["tokens"]} for r in by_model},
                "period_days": days,
            }
        finally:
            conn.close()

    def delete_analysis(self, analysis_id: int) -> bool:
        """Remove uma análise do banco."""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Erro ao deletar análise {analysis_id}: {e}")
                return False
            finally:
                conn.close()

    def export_to_json(self, output_path: str) -> bool:
        """Exporta todas as análises para JSON."""
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT * FROM analyses ORDER BY created_at").fetchall()
            data = [dict(r) for r in rows]
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"{len(data)} análises exportadas para {output_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao exportar: {e}")
            return False
        finally:
            conn.close()

    def log_acceptance(self, username: str, ip_address: str = "local") -> bool:
        """Registra aceite dos termos de uso pelo usuário."""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO acceptance_log (username, ip_address, accepted_at) VALUES (?, ?, ?)",
                    (username, ip_address, datetime.now().isoformat()),
                )
                conn.commit()
                logger.info(f"Termos aceitos por: {username}")
                return True
            except Exception as e:
                logger.error(f"Erro ao registrar aceite: {e}")
                return False
            finally:
                conn.close()

    def get_acceptance_history(self, username: str = "") -> list:
        """Retorna histórico de aceites, opcionalmente filtrado por usuário."""
        conn = self._get_conn()
        try:
            if username:
                rows = conn.execute(
                    "SELECT * FROM acceptance_log WHERE username = ? ORDER BY accepted_at DESC",
                    (username,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM acceptance_log ORDER BY accepted_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


if __name__ == "__main__":
    db = DatabaseService()

    print("=== Teste do DatabaseService ===\n")

    analysis_id = db.save_analysis(
        contract_text="Contrato de teste...",
        analysis_text="Análise do contrato de teste...",
        contract_name="contrato_teste.pdf",
        model_used="gemini",
        risk_high=2,
        risk_medium=3,
        risk_low=1,
        user_id="admin",
    )
    print(f"Análise salva com ID: {analysis_id}")

    stats = db.get_stats()
    print(f"\nEstatísticas: {json.dumps(stats, indent=2, ensure_ascii=False)}")
