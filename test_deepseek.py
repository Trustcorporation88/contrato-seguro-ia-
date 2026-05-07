import os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from analyzer import tentar_deepseek

api_key = os.getenv('DEEPSEEK_API_KEY')
model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
print(f'DeepSeek Key: {api_key[:15]}...')
print(f'Model: {model}')
print()

resultado = tentar_deepseek(
    'Clausula 1: O contratante pagara multa de 50% em caso de atraso. '
    'Analise este trecho brevemente.'
)
if resultado.startswith('[ERRO]'):
    print('FALHA:', resultado)
else:
    print('OK - DeepSeek funcionando!')
    print('Resposta:', resultado[:300].encode('ascii', 'ignore').decode())
