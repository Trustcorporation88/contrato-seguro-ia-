import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

try:
    from config import GEMINI_MODEL
except ImportError:
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

api_key = os.getenv("GEMINI_API_KEY")
print(f"Chave encontrada: {api_key[:20]}...")

if not api_key or "sua_chave" in api_key:
    print("❌ Chave não encontrada ou inválida")
else:
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents="Ola, responda apenas com a palavra 'OK' se estiver funcionando.",
        )
        print("OK - CHAVE DO GEMINI ESTA FUNCIONANDO!")
        print(f"Modelo: {GEMINI_MODEL}")
        print("Resposta do Gemini:", response.text)
    except Exception as e:
        print("ERRO na chave ou API:", str(e))