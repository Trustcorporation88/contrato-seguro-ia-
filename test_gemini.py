import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"Chave encontrada: {api_key[:20]}...")  # mostra parte da chave

if not api_key or "sua_chave" in api_key:
    print("❌ Chave não encontrada ou inválida")
else:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Olá, responda apenas com a palavra 'OK' se estiver funcionando.")
        print("✅ CHAVE DO GEMINI ESTÁ FUNCIONANDO!")
        print("Resposta do Gemini:", response.text)
    except Exception as e:
        print("❌ ERRO na chave ou API:", str(e))