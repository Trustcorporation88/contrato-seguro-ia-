"""
Testes para run_app.py.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from run_app import build_streamlit_command


def test_build_streamlit_command_defaults():
    """Deve montar comando padrão compatível com Streamlit local."""
    previous_port = os.environ.get("PORT")
    previous_address = os.environ.get("STREAMLIT_SERVER_ADDRESS")

    try:
        os.environ.pop("PORT", None)
        os.environ.pop("STREAMLIT_SERVER_ADDRESS", None)
        cmd = build_streamlit_command()
    finally:
        if previous_port is None:
            os.environ.pop("PORT", None)
        else:
            os.environ["PORT"] = previous_port

        if previous_address is None:
            os.environ.pop("STREAMLIT_SERVER_ADDRESS", None)
        else:
            os.environ["STREAMLIT_SERVER_ADDRESS"] = previous_address

    assert cmd[:4] == [sys.executable, "-m", "streamlit", "run"]
    assert "app.py" in cmd
    assert "--server.address" in cmd
    assert "--server.port" in cmd
    assert cmd[cmd.index("--server.address") + 1] == "0.0.0.0"
    assert cmd[cmd.index("--server.port") + 1] == "8501"


def test_build_streamlit_command_respects_environment():
    """Deve usar porta e endereço definidos pelo ambiente do Render."""
    previous_port = os.environ.get("PORT")
    previous_address = os.environ.get("STREAMLIT_SERVER_ADDRESS")

    try:
        os.environ["PORT"] = "10000"
        os.environ["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"
        cmd = build_streamlit_command()
    finally:
        if previous_port is None:
            os.environ.pop("PORT", None)
        else:
            os.environ["PORT"] = previous_port

        if previous_address is None:
            os.environ.pop("STREAMLIT_SERVER_ADDRESS", None)
        else:
            os.environ["STREAMLIT_SERVER_ADDRESS"] = previous_address

    assert cmd[cmd.index("--server.address") + 1] == "127.0.0.1"
    assert cmd[cmd.index("--server.port") + 1] == "10000"


if __name__ == "__main__":
    test_build_streamlit_command_defaults()
    test_build_streamlit_command_respects_environment()
    print("Todos os testes de run_app.py passaram!")
