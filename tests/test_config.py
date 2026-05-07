"""
Testes para o módulo config.py.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import compute_hash, check_dependencies


def test_compute_hash_deterministic():
    """Hash SHA256 deve ser determinístico para o mesmo input."""
    assert compute_hash("contrato teste") == compute_hash("contrato teste")


def test_compute_hash_different_inputs():
    """Inputs diferentes devem gerar hashes diferentes."""
    assert compute_hash("contrato A") != compute_hash("contrato B")


def test_compute_hash_not_empty():
    """Hash nunca deve ser vazio."""
    assert len(compute_hash("texto")) == 64


def test_compute_hash_unicode():
    """Hash deve funcionar com texto Unicode."""
    hash_result = compute_hash("contrato com acentuação e çedilha")
    assert len(hash_result) == 64


def test_check_dependencies_no_raise():
    """check_dependencies com raise_error=False não deve lançar exceção."""
    deps = check_dependencies(raise_error=False, verbose=False)
    assert "streamlit" in deps
    assert isinstance(deps["streamlit"], bool)


if __name__ == "__main__":
    test_compute_hash_deterministic()
    test_compute_hash_different_inputs()
    test_compute_hash_not_empty()
    test_compute_hash_unicode()
    test_check_dependencies_no_raise()
    print("Todos os testes de config.py passaram!")
