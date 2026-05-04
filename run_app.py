#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ContratoSeguro AI v2.0 - Script de Inicialização
Executa a aplicação Streamlit
"""

import os
import subprocess
import sys


def main():
    """Executa a aplicação Streamlit"""

    print("\n" + "=" * 50)
    print("   ContratoSeguro AI v2.0")
    print("   Iniciando aplicacao...")
    print("=" * 50 + "\n")

    # Mudar para diretório do script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Executar streamlit
    try:
        cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
        print(f"Executando: {' '.join(cmd)}\n")
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("[ERRO] Streamlit nao encontrado!")
        print("\nTente instalar com:")
        print("  pip install streamlit")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Aplicacao finalizada pelo usuario")
        sys.exit(0)
    except Exception as e:
        print(f"[ERRO] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
