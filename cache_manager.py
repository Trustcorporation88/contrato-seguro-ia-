"""
Cache Manager - Gerenciador de cache para análises de contratos.

Este módulo implementa um sistema de cache em memória com persistência em JSON
para evitar re-análise de contratos duplicados.
"""

import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Configuração de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CacheManager:
    """
    Gerenciador de cache para análises de contratos.

    Funcionalidades:
    - Cache em memória para acesso rápido
    - Persistência em JSON para durabilidade
    - Limite de histórico para evitar crescimento infinito
    - Métodos de hash SHA256 para identificar contratos duplicados
    """

    def __init__(self, cache_dir: str = "cache", max_history: int = 50):
        """
        Inicializa o gerenciador de cache.

        Args:
            cache_dir: Diretório para armazenar arquivos de cache (padrão: "cache")
            max_history: Número máximo de análises a manter no histórico (padrão: 50)
        """
        self.cache_dir = Path(cache_dir)
        self.history_file = self.cache_dir / "historico.json"
        self.max_history = max_history
        self.cache_memory: Dict[str, Dict[str, Any]] = {}

        # Criar diretório de cache se não existir
        self._create_cache_directory()

        # Carregar histórico do arquivo
        self._load_history()

        logger.info(
            f"CacheManager inicializado: cache_dir={self.cache_dir}, max_history={self.max_history}"
        )

    def _create_cache_directory(self) -> None:
        """Cria o diretório de cache se não existir."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Diretório de cache criado/verificado: {self.cache_dir}")
        except Exception as e:
            logger.error(f"Erro ao criar diretório de cache: {e}")
            raise

    def _compute_hash(self, texto_contrato: str) -> str:
        """
        Calcula o hash SHA256 do texto do contrato.

        Args:
            texto_contrato: Texto do contrato a ser hasheado

        Returns:
            Hash SHA256 em formato hexadecimal
        """
        return hashlib.sha256(texto_contrato.encode("utf-8")).hexdigest()

    def _load_history(self) -> None:
        """Carrega o histórico de análises do arquivo JSON."""
        try:
            if self.history_file.exists():
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.cache_memory = json.load(f)
                logger.info(f"Histórico carregado: {len(self.cache_memory)} entradas")
            else:
                logger.info(
                    "Arquivo de histórico não encontrado. Iniciando com cache vazio."
                )
                self.cache_memory = {}
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar arquivo de histórico: {e}")
            self.cache_memory = {}
        except Exception as e:
            logger.error(f"Erro ao carregar histórico: {e}")
            self.cache_memory = {}

    def _save_history(self) -> None:
        """Salva o histórico de análises no arquivo JSON."""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.cache_memory, f, ensure_ascii=False, indent=2)
            logger.debug(f"Histórico salvo: {len(self.cache_memory)} entradas")
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")

    def _remove_oldest_entries(self) -> None:
        """Remove as entradas mais antigas se o cache exceder o limite."""
        if len(self.cache_memory) > self.max_history:
            # Ordena por data (assumindo que "data" existe em todas as entradas)
            sorted_entries = sorted(
                self.cache_memory.items(),
                key=lambda x: x[1].get("data", ""),
                reverse=False,
            )

            # Remove entradas extras
            entries_to_remove = len(self.cache_memory) - self.max_history
            for hash_key, _ in sorted_entries[:entries_to_remove]:
                removed_data = self.cache_memory.pop(hash_key)
                logger.info(f"Entrada removida do cache (limite excedido): {hash_key}")

    def get_analysis(self, texto_contrato: str) -> Optional[Dict[str, Any]]:
        """
        Recupera a análise em cache se existir.

        Args:
            texto_contrato: Texto do contrato

        Returns:
            Dicionário com a análise se encontrada, None caso contrário
        """
        try:
            hash_contrato = self._compute_hash(texto_contrato)

            if hash_contrato in self.cache_memory:
                logger.info(f"Análise encontrada em cache para hash: {hash_contrato}")
                return self.cache_memory[hash_contrato]
            else:
                logger.debug(
                    f"Análise não encontrada em cache para hash: {hash_contrato}"
                )
                return None
        except Exception as e:
            logger.error(f"Erro ao recuperar análise do cache: {e}")
            return None

    def save_analysis(self, texto_contrato: str, analise: Any) -> str:
        """
        Salva a análise no cache e persiste em arquivo.

        Args:
            texto_contrato: Texto do contrato
            analise: Dicionário com a análise

        Returns:
            Hash SHA256 do contrato
        """
        try:
            hash_contrato = self._compute_hash(texto_contrato)
            tamanho_contrato = len(texto_contrato)
            data_analise = datetime.now().isoformat()

            # Armazenar no cache em memória
            self.cache_memory[hash_contrato] = {
                "analise": analise,
                "data": data_analise,
                "tamanho": tamanho_contrato,
                "tipo": "contrato",
            }

            # Verificar limite de histórico
            self._remove_oldest_entries()

            # Persistir em arquivo
            self._save_history()

            logger.info(f"Análise salva em cache com hash: {hash_contrato}")
            return hash_contrato
        except Exception as e:
            logger.error(f"Erro ao salvar análise no cache: {e}")
            raise

    def clear_cache(self) -> None:
        """Limpa todo o histórico de análises."""
        try:
            self.cache_memory = {}
            self._save_history()
            logger.warning("Cache foi limpo completamente")
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            raise

    def get_history(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna o histórico completo de análises.

        Returns:
            Dicionário com todas as análises em cache
        """
        try:
            logger.debug(f"Retornando histórico com {len(self.cache_memory)} entradas")
            return self.cache_memory.copy()
        except Exception as e:
            logger.error(f"Erro ao recuperar histórico: {e}")
            return {}

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.

        Returns:
            Dicionário com informações sobre o estado do cache
        """
        try:
            total_entries = len(self.cache_memory)
            total_size = sum(
                entry.get("tamanho", 0) for entry in self.cache_memory.values()
            )

            stats = {
                "total_entries": total_entries,
                "max_entries": self.max_history,
                "total_size_bytes": total_size,
                "cache_file": str(self.history_file),
                "cache_file_exists": self.history_file.exists(),
            }

            logger.info(f"Estatísticas do cache: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do cache: {e}")
            return {}

    def remove_entry(self, texto_contrato: str) -> bool:
        """
        Remove uma entrada específica do cache.

        Args:
            texto_contrato: Texto do contrato

        Returns:
            True se a entrada foi removida, False caso contrário
        """
        try:
            hash_contrato = self._compute_hash(texto_contrato)

            if hash_contrato in self.cache_memory:
                self.cache_memory.pop(hash_contrato)
                self._save_history()
                logger.info(f"Entrada removida do cache: {hash_contrato}")
                return True
            else:
                logger.debug(f"Entrada não encontrada para remoção: {hash_contrato}")
                return False
        except Exception as e:
            logger.error(f"Erro ao remover entrada do cache: {e}")
            return False

    def export_history(self, filepath: str) -> bool:
        """
        Exporta o histórico para um arquivo JSON externo.

        Args:
            filepath: Caminho do arquivo para exportar

        Returns:
            True se exportado com sucesso, False caso contrário
        """
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.cache_memory, f, ensure_ascii=False, indent=2)
            logger.info(f"Histórico exportado para: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Erro ao exportar histórico: {e}")
            return False

    def import_history(self, filepath: str) -> bool:
        """
        Importa o histórico de um arquivo JSON externo.

        Args:
            filepath: Caminho do arquivo para importar

        Returns:
            True se importado com sucesso, False caso contrário
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                imported_data = json.load(f)

            # Mesclar com dados existentes, removendo mais antigas se necessário
            self.cache_memory.update(imported_data)
            self._remove_oldest_entries()
            self._save_history()

            logger.info(f"Histórico importado de: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Erro ao importar histórico: {e}")
            return False


if __name__ == "__main__":
    # Exemplo de uso
    print("=== Teste do CacheManager ===\n")

    # Inicializar gerenciador
    cache = CacheManager(cache_dir="cache", max_history=10)

    # Criar alguns contratos de exemplo
    contratos = [
        "Contrato 1: Este é um contrato de exemplo...",
        "Contrato 2: Este é outro contrato diferente...",
        "Contrato 1: Este é um contrato de exemplo...",  # Duplicado
    ]

    # Simular análises
    for i, contrato in enumerate(contratos, 1):
        analise_existente = cache.get_analysis(contrato)

        if analise_existente:
            print(f"✓ Contrato {i}: Análise encontrada em cache!")
        else:
            print(f"✗ Contrato {i}: Analisando contrato...")
            analise_simulada = {
                "id": i,
                "resultado": f"Análise do contrato {i}",
                "pontos_importantes": ["Ponto 1", "Ponto 2"],
            }
            hash_salvo = cache.save_analysis(contrato, analise_simulada)
            print(f"  Hash: {hash_salvo}")

    print("\n=== Estatísticas do Cache ===")
    stats = cache.get_cache_stats()
    for chave, valor in stats.items():
        print(f"{chave}: {valor}")

    print("\n=== Histórico ===")
    historico = cache.get_history()
    print(f"Total de entradas: {len(historico)}")
    for hash_key, dados in list(historico.items())[:3]:
        print(f"Hash: {hash_key[:16]}...")
        print(f"  Data: {dados.get('data')}")
        print(f"  Tamanho: {dados.get('tamanho')} bytes")
