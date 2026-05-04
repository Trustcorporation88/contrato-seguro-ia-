# 📋 Guia de Configuração - ContratoSeguro AI

Documentação completa do módulo `config.py` que centraliza todas as configurações da aplicação.

## 📖 Índice

1. [Visão Geral](#visão-geral)
2. [Uso Rápido](#uso-rápido)
3. [Constantes Centralizadas](#constantes-centralizadas)
4. [Funções de Carregamento](#funções-de-carregamento)
5. [Validações](#validações)
6. [Logging](#logging)
7. [Arquivo .env](#arquivo-env)
8. [Exemplos Práticos](#exemplos-práticos)

## Visão Geral

O módulo `config.py` fornece:

✅ **Constantes centralizadas** - Todos os valores hardcoded em um único lugar  
✅ **Carregamento de variáveis de ambiente** - Suporte a arquivo `.env`  
✅ **Validações automáticas** - Verifica dependências e chaves de API  
✅ **Logging estruturado** - Sistema de logs com rotação automática  
✅ **Documentação integrada** - Docstrings completas e exemplos  

---

## Uso Rápido

### Inicialização Básica

```python
from config import load_env_config, setup_logging

# Carregar configurações
config = load_env_config()

# Configurar logging
logger = setup_logging()

# Usar em sua aplicação
logger.info("Aplicação iniciada")
max_size = config['MAX_FILE_SIZE']
```

### Validações Iniciais

```python
from config import check_dependencies, check_api_keys

# Verificar dependências
check_dependencies()  # Lança erro se faltar alguma lib

# Verificar chaves de API
check_api_keys()  # Mostra avisos se faltarem chaves
```

---

## Constantes Centralizadas

### Limites de Arquivo

```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MIN_TEXT_LENGTH = 10               # Mínimo 10 caracteres
```

### Modelos de IA

```python
GEMINI_MODEL = "gemini-2.0-flash"  # Modelo Google
OLLAMA_MODEL = "mistral"            # Modelo local
```

### URLs e Endpoints

```python
OLLAMA_URL = "http://localhost:11434/api/generate"
```

### Timeouts (segundos)

```python
REQUEST_TIMEOUT = 30      # Timeout padrão para requisições
ANALYSIS_TIMEOUT = 300    # 5 minutos para análise completa
```

### Retries

```python
MAX_RETRIES = 3      # Número de tentativas
RETRY_DELAY = 2      # Intervalo entre tentativas (segundos)
```

### Diretórios

```python
CACHE_DIR = "cache/"   # Cache de análises
TEMP_DIR = "temp/"     # Arquivos temporários
LOGS_DIR = "logs/"     # Arquivos de log
```

### Cache

```python
MAX_CACHE_SIZE = 100         # Máximo 100 análises em cache
CACHE_EXPIRY_HOURS = 24      # Cache válido por 24 horas
```

### Logging

```python
LOG_LEVEL = "INFO"                         # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 10 * 1024 * 1024          # 10MB por arquivo
LOG_BACKUP_COUNT = 5                       # Manter 5 backups
```

---

## Funções de Carregamento

### `load_env_config()`

Carrega todas as configurações da aplicação.

**Parâmetros:**
- `env_file` (str, opcional): Caminho do arquivo `.env`
- `validate` (bool): Se deve validar as configs (default: True)
- `verbose` (bool): Exibir mensagens (default: True)

**Retorna:** Dict com todas as configurações

**Exemplo:**
```python
from config import load_env_config

# Uso padrão
config = load_env_config()

# Sem validações (mais rápido)
config = load_env_config(validate=False)

# Arquivo .env customizado
config = load_env_config(env_file="/custom/path/.env")

# Modo silencioso
config = load_env_config(verbose=False)

# Acessar valores
print(config['GEMINI_MODEL'])
print(config['MAX_FILE_SIZE'])
print(config['CACHE_DIR'])
```

### `setup_logging()`

Configura o sistema de logging da aplicação.

**Parâmetros:**
- `log_level` (str, opcional): Nível de log (DEBUG, INFO, etc)
- `log_file` (str, opcional): Caminho do arquivo de log
- `verbose` (bool): Exibir mensagens (default: True)

**Retorna:** Logger configurado e pronto

**Exemplo:**
```python
from config import setup_logging

# Uso padrão (INFO level)
logger = setup_logging()

# Nível DEBUG para desenvolvimento
logger = setup_logging(log_level="DEBUG")

# Arquivo de log customizado
logger = setup_logging(log_file="/custom/path/app.log")

# Modo silencioso
logger = setup_logging(verbose=False)

# Usar o logger
logger.debug("Mensagem de debug")
logger.info("Aplicação iniciada")
logger.warning("Aviso importante")
logger.error("Ocorreu um erro")
logger.critical("Erro crítico!")
```

---

## Validações

### `check_dependencies()`

Verifica se todas as bibliotecas obrigatórias estão instaladas.

**Parâmetros:**
- `raise_error` (bool): Lançar exceção se faltar libs (default: True)
- `verbose` (bool): Exibir mensagens (default: True)

**Retorna:** Dict com status de cada pacote

**Exemplo:**
```python
from config import check_dependencies

# Validar e lançar erro se necessário
check_dependencies()

# Validar sem lançar erro
status = check_dependencies(raise_error=False)
if not status['streamlit']:
    print("Streamlit não instalado!")

# Modo silencioso
status = check_dependencies(verbose=False)
```

### `check_api_keys()`

Verifica se as chaves de API estão configuradas.

**Parâmetros:**
- `verbose` (bool): Exibir mensagens (default: True)

**Retorna:** Dict com status de cada chave

**Exemplo:**
```python
from config import check_api_keys

# Validar chaves
keys = check_api_keys()

if not keys['GEMINI_API_KEY']:
    print("GEMINI_API_KEY não configurada!")
    print("Configure no arquivo .env")

# Modo silencioso
keys = check_api_keys(verbose=False)
```

### `print_config_summary()`

Exibe um resumo formatado das configurações.

**Exemplo:**
```python
from config import load_env_config, print_config_summary

config = load_env_config()
print_config_summary(config)
```

**Saída:**
```
============================================================
📋 RESUMO DE CONFIGURAÇÕES
============================================================

📊 Limites:
  • MAX_FILE_SIZE: 50.0 MB
  • MIN_TEXT_LENGTH: 10 caracteres

🤖 Modelos:
  • GEMINI_MODEL: gemini-2.0-flash
  • OLLAMA_MODEL: mistral
  
[... mais configurações ...]
```

---

## Logging

### Configuração Automática

O logging é configurado automaticamente com:

- ✅ Saída para arquivo em `logs/contrato_seguro.log`
- ✅ Saída para console/stdout
- ✅ Rotação automática em 10MB
- ✅ Manutenção de 5 backups
- ✅ Formatação com timestamp

### Usar Logger em Seu Código

```python
from config import setup_logging

logger = setup_logging()

# Log em diferentes níveis
logger.debug("Informação de debug")      # Nível DEBUG
logger.info("Operação realizada")        # Nível INFO
logger.warning("Algo pode estar errado") # Nível WARNING
logger.error("Ocorreu um erro")          # Nível ERROR
logger.critical("Erro crítico!")         # Nível CRITICAL
```

### Exemplo Completo de Integração

```python
from config import load_env_config, setup_logging, check_dependencies

# Setup inicial
try:
    # Verificar dependências
    check_dependencies()
    
    # Carregar config
    config = load_env_config()
    
    # Setup logging
    logger = setup_logging()
    
    logger.info("Aplicação iniciada com sucesso")
    logger.info(f"Usando modelo: {config['GEMINI_MODEL']}")
    
except ImportError as e:
    print(f"Erro: Dependências faltando - {e}")
    exit(1)
except ValueError as e:
    print(f"Erro: Configuração inválida - {e}")
    exit(1)
except Exception as e:
    print(f"Erro inesperado: {e}")
    exit(1)
```

---

## Arquivo .env

### Criar arquivo `.env`

Crie um arquivo `.env` na raiz do projeto com suas configurações:

```bash
# Modelos
GEMINI_MODEL=gemini-2.0-flash
OLLAMA_MODEL=mistral

# URLs
OLLAMA_URL=http://localhost:11434/api/generate

# API Keys
GEMINI_API_KEY=sua_chave_aqui
OLLAMA_API_KEY=sua_chave_opcional

# Limites
MAX_FILE_SIZE=52428800
MIN_TEXT_LENGTH=10

# Timeouts
REQUEST_TIMEOUT=30
ANALYSIS_TIMEOUT=300

# Retries
MAX_RETRIES=3
RETRY_DELAY=2

# Diretórios
CACHE_DIR=cache/
TEMP_DIR=temp/
LOGS_DIR=logs/

# Logging
LOG_LEVEL=INFO

# Cache
MAX_CACHE_SIZE=100
CACHE_EXPIRY_HOURS=24
```

### Variáveis Obrigatórias

- `GEMINI_API_KEY` - Chave da API Google Gemini

### Variáveis Opcionais

Todas as outras podem ser omitidas e usarão valores padrão.

---

## Exemplos Práticos

### Exemplo 1: Inicialização Mínima

```python
from config import load_env_config, setup_logging

config = load_env_config()
logger = setup_logging()

print(f"Arquivo: {config['CACHE_DIR']}")
logger.info("Pronto!")
```

### Exemplo 2: Aplicação com Validações

```python
from config import (
    load_env_config,
    setup_logging,
    check_dependencies,
    check_api_keys,
)

def main():
    # Validar tudo
    check_dependencies()
    check_api_keys()
    
    # Carregar config
    config = load_env_config()
    logger = setup_logging(log_level="DEBUG")
    
    logger.info(f"Cache dir: {config['CACHE_DIR']}")
    logger.info(f"Timeout: {config['ANALYSIS_TIMEOUT']}s")
    
    # Seu código aqui...

if __name__ == "__main__":
    main()
```

### Exemplo 3: Uso em Streamlit

```python
import streamlit as st
from config import load_env_config, setup_logging

# Inicializar (cache para evitar recarregar)
@st.cache_resource
def init_config():
    config = load_env_config()
    logger = setup_logging(verbose=False)
    return config, logger

config, logger = init_config()

st.title("ContratoSeguro AI")
logger.info(f"Usuário acessou a aplicação")

# Usar configs
max_size = config['MAX_FILE_SIZE'] / (1024 * 1024)
st.info(f"Tamanho máximo: {max_size:.0f} MB")
```

### Exemplo 4: Tratamento de Erros

```python
from config import load_env_config, check_dependencies, setup_logging

try:
    # Verificar tudo
    check_dependencies(raise_error=True)
    
    # Carregar config
    config = load_env_config(validate=True)
    
    # Setup logging
    logger = setup_logging()
    
    logger.info("Tudo pronto!")
    
except ImportError as e:
    print(f"❌ Erro de dependência: {e}")
    print("Execute: pip install -r requirements.txt")
    exit(1)
    
except ValueError as e:
    print(f"❌ Erro de configuração: {e}")
    print("Verifique seu arquivo .env")
    exit(1)
    
except Exception as e:
    print(f"❌ Erro: {e}")
    exit(1)
```

### Exemplo 5: Customizar Logging

```python
from config import load_env_config, setup_logging

# Config padrão
config = load_env_config()

# Logger para desenvolvimento (DEBUG)
dev_logger = setup_logging(log_level="DEBUG")

# Logger para produção (INFO)
prod_logger = setup_logging(log_level="INFO")

# Logger customizado com arquivo específico
custom_logger = setup_logging(
    log_level="DEBUG",
    log_file="custom_app.log"
)

dev_logger.debug("Informação detalhada (apenas dev)")
prod_logger.info("Informação importante")
custom_logger.error("Arquivo em custom_app.log")
```

---

## Testando a Configuração

Execute o script de teste:

```bash
python config.py
```

Saída esperada:
```
🔍 Testando Configurações do ContratoSeguro AI

1️⃣  Verificando dependências...
✅ Pacote instalado: streamlit
✅ Pacote instalado: pymupdf
... (mais pacotes)

2️⃣  Verificando chaves de API...
✅ Chave de API configurada: GEMINI_API_KEY

3️⃣  Carregando configurações...
✅ Configurações carregadas com sucesso!

4️⃣  Configurando logging...
✅ Logging configurado

📋 RESUMO DE CONFIGURAÇÕES
... (mais detalhes)
```

---

## Integração com app.py

Para integrar no seu `app.py` existente:

```python
# No topo de app.py
from config import load_env_config, setup_logging, check_dependencies

# Inicializar (adicionar ao startup)
try:
    check_dependencies()
    config = load_env_config()
    logger = setup_logging(verbose=False)
    logger.info("App iniciada com sucesso")
except Exception as e:
    print(f"Erro na inicialização: {e}")
    exit(1)

# Usar valores de config onde estão hardcoded:
# MAX_FILE_SIZE = config['MAX_FILE_SIZE']
# MIN_TEXT_LENGTH = config['MIN_TEXT_LENGTH']
```

---

## Troubleshooting

### "Chave de API faltando: GEMINI_API_KEY"

**Solução:**
1. Crie ou edite o arquivo `.env`
2. Adicione: `GEMINI_API_KEY=sua_chave_aqui`
3. Salve o arquivo

### "Pacotes obrigatórios faltando"

**Solução:**
```bash
pip install -r requirements.txt
```

### "Diretórios não encontrados"

**Solução:**
O script cria automaticamente. Se o problema persistir, crie manualmente:
```bash
mkdir cache temp logs
```

### Erro de encoding no console (⚠️ Windows)

**Causa:** Console Windows não suporta totalmente Unicode  
**Solução:** Use um terminal moderno (Windows Terminal, VS Code)

---

## Referência Rápida

| Função | Descrição | Retorna |
|--------|-----------|---------|
| `load_env_config()` | Carrega todas as configs | Dict |
| `setup_logging()` | Configura logging | Logger |
| `check_dependencies()` | Valida libs | Dict[str, bool] |
| `check_api_keys()` | Valida chaves API | Dict[str, bool] |
| `print_config_summary()` | Exibe resumo | None |

---

## Suporte

Para dúvidas ou problemas:
1. Verifique este guia
2. Execute `python config.py` para diagnosticar
3. Verifique o arquivo `.env`
4. Consulte a documentação das funções (docstrings)

---

**Última atualização:** 2024  
**Versão:** 1.0
