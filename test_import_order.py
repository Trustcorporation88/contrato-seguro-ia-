"""
Simula EXATAMENTE a ordem de imports do Streamlit.
"""
import sys, os
sys.path.insert(0, ".")

# Simula o import do analyzer (igual app.py linha 17)
from analyzer import SELECTED_MODEL, analisar_contrato, set_model, set_fallback, responder_duvida_clausula

# Simula linha 30 do app.py
from dotenv import load_dotenv
load_dotenv()

# Verifica
dk = os.getenv("DEEPSEEK_API_KEY")
gk = os.getenv("GEMINI_API_KEY")
print(f"DEEPSEEK_API_KEY: {dk[:20] if dk else 'NAO DEFINIDO'}... (len={len(dk) if dk else 0})")
print(f"GEMINI_API_KEY: {gk[:20] if gk else 'NAO DEFINIDO'}... (len={len(gk) if gk else 0})")
print(f"Modelo selecionado: {SELECTED_MODEL}")
