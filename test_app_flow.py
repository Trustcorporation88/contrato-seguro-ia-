"""
Simula exatamente o fluxo do app: carrega pdf, extrai texto, analisa.
"""
import sys, os
from io import BytesIO
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from pdf_extractor import extrair_texto_pdf_bytes
from analyzer import tentar_deepseek, set_model, set_fallback

set_model("deepseek")
set_fallback(True)

pdf_path = r"C:\ContratoSeguro-IA\temp.pdf"
with open(pdf_path, "rb") as f:
    pdf_bytes = BytesIO(f.read())

print("Extraindo texto...")
texto = extrair_texto_pdf_bytes(pdf_bytes, enable_ocr=True)
print(f"Texto: {len(texto)} caracteres")

print("Enviando para DeepSeek...")
resultado = tentar_deepseek(texto)
if resultado.startswith("[ERRO]"):
    print("FALHA:", resultado)
else:
    print(f"OK: {len(resultado)} caracteres")
    altos = resultado.count("RISCO ALTO")
    medios = resultado.count("RISCO MÉDIO")
    baixos = resultado.count("RISCO BAIXO")
    print(f"Riscos: ALTO={altos} MEDIO={medios} BAIXO={baixos}")
