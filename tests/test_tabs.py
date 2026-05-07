"""
Testes para os módulos de tabs.
Verifica que todos os módulos de tab podem ser importados e têm funções render.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_tabs_init_exports():
    """__init__.py deve exportar todas as funções render."""
    from tabs import render_dashboard, render_clauses, render_chat, render_export
    assert callable(render_dashboard)
    assert callable(render_clauses)
    assert callable(render_chat)
    assert callable(render_export)


def test_dashboard_module():
    """Módulo dashboard deve ter render_dashboard."""
    from tabs.dashboard import render_dashboard
    assert callable(render_dashboard)


def test_clauses_module():
    """Módulo clauses deve ter render_clauses."""
    from tabs.clauses import render_clauses
    assert callable(render_clauses)


def test_chat_module():
    """Módulo chat deve ter render_chat."""
    from tabs.chat import render_chat
    assert callable(render_chat)


def test_export_module():
    """Módulo export deve ter render_export e helpers."""
    from tabs.export import render_export, _gerar_pdf, _gerar_word
    assert callable(render_export)
    assert callable(_gerar_pdf)
    assert callable(_gerar_word)


if __name__ == "__main__":
    test_tabs_init_exports()
    test_dashboard_module()
    test_clauses_module()
    test_chat_module()
    test_export_module()
    print("Todos os testes de tabs passaram!")
