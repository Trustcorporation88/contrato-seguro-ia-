# 🔧 ContratoSeguro AI - Módulo de Configuração

Módulo centralizado para gerenciar configurações, logging e validações da aplicação.

## ⚡ Quick Start

### 1. Instalação

O arquivo `config.py` já está incluso no projeto. Nenhuma instalação adicional necessária além de `python-dotenv`:

```bash
pip install python-dotenv
```

### 2. Criar arquivo .env

```bash
# Copiar template
cp .env.example .env

# Editar e adicionar sua chave de API
# GEMINI_API_KEY=sua_chave_aqui
```

### 3. Usar em sua aplicação

```python
from config import load_env_config, setup_logging

# Carregar configurações
config = load_env_config()

# Configurar logging
logger = setup_logging()

# Usar!
logger.info("Aplicação iniciada")
print(config['MAX_FILE_SIZE'])
```

## 📚 Documentação

### Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `config.py` | Módulo principal com todas as funções |
| `CONFIG_GUIDE.md` | Documentação completa e detalhada |
| `INTEGRACAO_CONFIG.md` | Guia passo a passo para integrar no app.py |
| `.env.example` | Template do arquivo de variáveis de ambiente |

### O que você encontra em config.py

✅ **Constantes Centralizadas**
- Limites de arquivo (MAX_FILE_SIZE = 50MB)
- Modelos de IA (GEMINI, OLLAMA)
- Timeouts e retries
- Configurações de cache e logging

✅ **Funções de Carregamento**
- `load_env_config()` - Carrega todas as configurações
- `setup_logging()` - Configura o sistema de logs

✅ **Validações**
- `check_dependencies()` - Verifica se libs estão instaladas
- `check_api_keys()` - Valida chaves de API
- `_validate_config()` - Valida configurações

✅ **Logging Estruturado**
- Logger centralizado com rotação automática
- Saída para arquivo e console
- Formatação com timestamp

## 🚀 Uso

### Carregamento Básico

```python
from config import load_env_config, setup_logging

config = load_env_config()
logger = setup_logging()
```

### Verificar Dependências

```python
from config import check_dependencies, check_api_keys

# Verificar tudo ao iniciar
try:
    check_dependencies()
    check_api_keys()
except ImportError as e:
    print(f"Erro: {e}")
    exit(1)
```

### Usar Logging

```python
logger.debug("Debug info")
logger.info("Informação")
logger.warning("Aviso")
logger.error("Erro")
logger.critical("Crítico")
```

### Acessar Configurações

```python
config = load_env_config()

# Limites
max_size = config['MAX_FILE_SIZE']  # 50MB
min_text = config['MIN_TEXT_LENGTH']  # 10

# Modelos
gemini = config['GEMINI_MODEL']  # gemini-2.0-flash
ollama = config['OLLAMA_MODEL']  # mistral

# Timeouts
timeout = config['REQUEST_TIMEOUT']  # 30s

# Diretórios
cache_dir = config['CACHE_DIR']  # Path('cache/')
```

## 📖 Exemplos

### Exemplo 1: App Simples

```python
from config import load_env_config, setup_logging

def main():
    config = load_env_config()
    logger = setup_logging()
    
    logger.info(f"Usando modelo: {config['GEMINI_MODEL']}")
    logger.info(f"Cache size: {config['MAX_CACHE_SIZE']}")
    
    # Seu código aqui...

if __name__ == "__main__":
    main()
```

### Exemplo 2: Com Validações

```python
from config import (
    load_env_config,
    setup_logging,
    check_dependencies,
    check_api_keys
)

try:
    # Validar tudo
    check_dependencies()
    check_api_keys()
    
    # Carregar config
    config = load_env_config()
    logger = setup_logging()
    
    logger.info("Aplicação pronta!")
    
except ImportError as e:
    print(f"Erro de dependência: {e}")
    exit(1)
except ValueError as e:
    print(f"Erro de configuração: {e}")
    exit(1)
```

### Exemplo 3: Em Streamlit

```python
import streamlit as st
from config import load_env_config, setup_logging

@st.cache_resource
def init():
    config = load_env_config(verbose=False)
    logger = setup_logging(verbose=False)
    return config, logger

config, logger = init()

st.title("Minha App")
logger.info("Usuário acessou")

max_size = config['MAX_FILE_SIZE'] / (1024*1024)
st.info(f"Tamanho máximo: {max_size:.0f} MB")
```

## 🧪 Testes

Testar configuração:

```bash
python config.py
```

Esperado:
```
🔍 Testando Configurações do ContratoSeguro AI

1️⃣  Verificando dependências...
✅ Pacote instalado: streamlit
✅ Pacote instalado: pymupdf
...

2️⃣  Verificando chaves de API...
✅ Chave de API configurada: GEMINI_API_KEY
...

3️⃣  Carregando configurações...
✅ Configurações carregadas com sucesso!
...
```

## 📝 Arquivo .env

Criar `.env` com valores:

```bash
# Obrigatório
GEMINI_API_KEY=sua_chave_aqui

# Opcional (usa defaults se omitido)
GEMINI_MODEL=gemini-2.0-flash
OLLAMA_URL=http://localhost:11434/api/generate
LOG_LEVEL=INFO
MAX_FILE_SIZE=52428800
```

Ver `.env.example` para lista completa.

## 🔍 Arquivos de Log

Logs são salvos em `logs/contrato_seguro.log`:

```bash
# Ver últimos logs
tail -f logs/contrato_seguro.log

# Windows PowerShell
Get-Content logs/contrato_seguro.log -Tail 20 -Wait
```

Formato:
```
2024-04-29 11:31:39,657 - ContratoSeguro - INFO - Aplicação iniciada
2024-04-29 11:31:40,123 - ContratoSeguro - ERROR - Ocorreu um erro
```

## 🐛 Troubleshooting

### Config não encontrado
```python
ModuleNotFoundError: No module named 'config'
```
**Solução:** Certifique-se que `config.py` está na mesma pasta que seu script.

### Chave de API faltando
```
❌ Chave de API faltando: GEMINI_API_KEY
```
**Solução:** Crie `.env` e adicione `GEMINI_API_KEY=sua_chave`

### Erro de validação
```
ValueError: Erros na validação de configuração
```
**Solução:** Verifique valores em `.env`, execute `python config.py` para diagnóstico

### Diretórios não encontrados
**Solução:** São criados automaticamente em `config/`, `temp/`, `logs/`

## 📊 Referência Rápida

| Função | O que faz |
|--------|-----------|
| `load_env_config()` | Carrega configurações do .env |
| `setup_logging()` | Configura sistema de logs |
| `check_dependencies()` | Valida pacotes instalados |
| `check_api_keys()` | Valida chaves de API |
| `print_config_summary()` | Exibe resumo visual |

## 🎯 Próximos Passos

1. **Ler Documentação:** `CONFIG_GUIDE.md` tem tudo detalhado
2. **Integrar no App:** Veja `INTEGRACAO_CONFIG.md`
3. **Testar:** Execute `python config.py`
4. **Customizar:** Edite `config.py` conforme necessário

## 💡 Boas Práticas

✅ Sempre validar ao iniciar:
```python
check_dependencies()
check_api_keys()
```

✅ Usar logging para debugging:
```python
logger.info("Evento importante")
logger.error("Erro encontrado")
```

✅ Não hardcoder valores:
```python
# ❌ Errado
MAX_SIZE = 52428800

# ✅ Correto
config = load_env_config()
MAX_SIZE = config['MAX_FILE_SIZE']
```

✅ Guardar .env com segurança:
```bash
# .gitignore
.env
*.log
```

## 📞 Suporte

Dúvidas?
1. Leia `CONFIG_GUIDE.md`
2. Execute `python config.py` para diagnosticar
3. Verifique logs em `logs/contrato_seguro.log`
4. Consulte docstrings no código

## 📄 Licença

Mesmo projeto que ContratoSeguro AI.

---

**Versão:** 1.0  
**Status:** ✅ Pronto para produção  
**Última atualização:** 2024
