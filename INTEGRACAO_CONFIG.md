# 🔗 Guia de Integração: config.py → app.py

Instruções passo a passo para integrar o novo módulo `config.py` com sua aplicação Streamlit existente.

## 📋 Índice

1. [Visão Geral da Integração](#visão-geral)
2. [Passo a Passo](#passo-a-passo)
3. [Modificações no app.py](#modificações-no-apppy)
4. [Testando a Integração](#testando-a-integração)
5. [Benefícios](#benefícios)

---

## Visão Geral

### Antes (Atual)
```python
# app.py
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB (hardcoded)
MIN_TEXT_LENGTH = 10               # Hardcoded

# Valores espalhados pelo código
# Sem logging centralizado
# Sem validações automáticas
```

### Depois (Com config.py)
```python
# app.py
from config import load_env_config, setup_logging

config = load_env_config()
logger = setup_logging()

# Valores centralizados e carregados
max_size = config['MAX_FILE_SIZE']
min_length = config['MIN_TEXT_LENGTH']

# Logging automático
logger.info("Aplicação iniciada")
```

---

## Passo a Passo

### 1. Adicionar Imports no Início de app.py

Abra seu arquivo `app.py` e adicione no topo (após os imports padrão):

```python
import hashlib
import time
from io import BytesIO

import streamlit as st

# ✅ ADICIONAR ESTAS LINHAS
from config import load_env_config, setup_logging, check_dependencies

from analyzer import analisar_contrato, set_model
from pdf_extractor import extrair_texto_pdf_bytes
```

### 2. Inicializar Config e Logger

Logo após `st.set_page_config()`, adicione:

```python
st.set_page_config(page_title="ContratoSeguro AI", page_icon="📋", layout="wide")

# ✅ ADICIONAR ESTAS LINHAS
try:
    config = load_env_config(verbose=False)
    logger = setup_logging(verbose=False)
except Exception as e:
    st.error(f"Erro ao carregar configurações: {e}")
    st.stop()

# Usar config ao invés de valores hardcoded
MAX_FILE_SIZE = config['MAX_FILE_SIZE']
MIN_TEXT_LENGTH = config['MIN_TEXT_LENGTH']
```

### 3. Remover Valores Hardcoded

**Antes:**
```python
# Antigo - hardcoded
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MIN_TEXT_LENGTH = 10  # Mínimo de caracteres para análise
```

**Depois:**
```python
# Novo - do config.py
MAX_FILE_SIZE = config['MAX_FILE_SIZE']
MIN_TEXT_LENGTH = config['MIN_TEXT_LENGTH']
```

### 4. Adicionar Logging em Pontos Estratégicos

#### Quando arquivo é enviado:
```python
if uploaded_file:
    file_hash = calcular_hash_arquivo(bytes(uploaded_file.getbuffer()))
    logger.info(f"Arquivo enviado: {uploaded_file.name} ({uploaded_file.size} bytes)")
```

#### Quando análise inicia:
```python
if btn_analisar and st.session_state.texto_extraido:
    logger.info(f"Iniciando análise com modelo: {modelo_escolhido}")
    # ... resto do código
```

#### Quando análise completa:
```python
tempo_analise = time.time() - tempo_inicio
logger.info(f"Análise concluída em {tempo_analise:.2f}s")
```

#### Quando há erro:
```python
except Exception as e:
    logger.error(f"Erro durante análise: {str(e)}")
    st.error(f"❌ Erro durante a análise: {str(e)}")
```

---

## Modificações no app.py

### Versão Simplificada (Principais Mudanças)

```python
import hashlib
import time
from io import BytesIO

import streamlit as st

# ✅ NOVA LINHA - Importar config
from config import load_env_config, setup_logging

from analyzer import analisar_contrato, set_model
from pdf_extractor import extrair_texto_pdf_bytes

st.set_page_config(page_title="ContratoSeguro AI", page_icon="📋", layout="wide")

# ✅ NOVA LINHA - Inicializar config
try:
    config = load_env_config(verbose=False)
    logger = setup_logging(verbose=False)
except Exception as e:
    st.error(f"Erro ao carregar configurações: {e}")
    st.stop()

# ✅ MUDADO - Usar valores do config
MAX_FILE_SIZE = config['MAX_FILE_SIZE']
MIN_TEXT_LENGTH = config['MIN_TEXT_LENGTH']

# CSS para melhorias visuais (mesmo que antes)
st.markdown("""...""", unsafe_allow_html=True)

# ... resto do código igual, mas com logging adicionado ...
```

### Exemplo: Função com Logging

**Antes:**
```python
def validar_arquivo(uploaded_file) -> tuple[bool, str]:
    if uploaded_file is None:
        return False, "Nenhum arquivo foi enviado"
    
    if uploaded_file.size == 0:
        return (False, "❌ Arquivo vazio detectado...")
    
    if uploaded_file.size > MAX_FILE_SIZE:
        return (False, "❌ Arquivo muito grande...")
    
    return True, ""
```

**Depois (com logging):**
```python
def validar_arquivo(uploaded_file) -> tuple[bool, str]:
    if uploaded_file is None:
        logger.warning("Tentativa de validação com arquivo None")
        return False, "Nenhum arquivo foi enviado"
    
    if uploaded_file.size == 0:
        logger.warning(f"Arquivo vazio detectado: {uploaded_file.name}")
        return (False, "❌ Arquivo vazio detectado...")
    
    if uploaded_file.size > MAX_FILE_SIZE:
        logger.warning(f"Arquivo muito grande: {uploaded_file.name} ({uploaded_file.size} bytes)")
        return (False, "❌ Arquivo muito grande...")
    
    logger.info(f"Arquivo validado com sucesso: {uploaded_file.name}")
    return True, ""
```

---

## Testando a Integração

### Teste 1: Verificar Carregamento

Execute e verifique se aparece a mensagem:

```bash
streamlit run app.py
```

Procure no console ou no arquivo de log se há mensagens como:
```
INFO - ContratoSeguro - Logging configurado
INFO - ContratoSeguro - Arquivo .env carregado
```

### Teste 2: Verificar Arquivo de Log

Verifique se os logs estão sendo escritos:

```bash
# Verificar último log
tail -f logs/contrato_seguro.log

# Windows PowerShell
Get-Content logs/contrato_seguro.log -Tail 20 -Wait
```

### Teste 3: Verificar Valores de Config

Adicione temporariamente (ao lado do título):

```python
st.markdown("### 📋 ContratoSeguro AI")

# TESTE - Remover depois
with st.expander("🔧 Debug - Configurações"):
    st.write(f"MAX_FILE_SIZE: {config['MAX_FILE_SIZE'] / (1024*1024):.1f} MB")
    st.write(f"GEMINI_MODEL: {config['GEMINI_MODEL']}")
    st.write(f"CACHE_DIR: {config['CACHE_DIR']}")
```

---

## Benefícios

### ✅ Configuração Centralizada
- Todos os valores em um único lugar
- Fácil de modificar
- Consistência garantida

### ✅ Variáveis de Ambiente
- Diferentes configs por ambiente (dev/prod)
- Segurança das chaves de API
- Sem hardcoding de valores sensíveis

### ✅ Logging Automático
- Rastreamento de eventos
- Debugging facilitado
- Histórico de execução

### ✅ Validações Automáticas
- Verificação de dependências ao iniciar
- Validação de chaves de API
- Erros claros e informativos

### ✅ Escalabilidade
- Fácil de adicionar novas configurações
- Suporte a múltiplos ambientes
- Desenvolvimento mais rápido

---

## Arquivo .env Necessário

Crie o arquivo `.env` na raiz do projeto:

```bash
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-2.0-flash
LOG_LEVEL=INFO
```

Ou copie do template:

```bash
cp .env.example .env
# Edite e preencha os valores
```

---

## Próximos Passos (Opcional)

### 1. Integrar em analyzer.py

```python
# No início de analyzer.py
from config import setup_logging

logger = setup_logging(verbose=False)

def analisar_contrato(texto: str) -> str:
    logger.info(f"Analisando contrato com {len(texto)} caracteres")
    # ... seu código ...
    logger.info("Análise concluída")
```

### 2. Integrar em cache_manager.py

```python
# Usar config para MAX_CACHE_SIZE
from config import load_env_config

config = load_env_config(verbose=False)
MAX_CACHE = config['MAX_CACHE_SIZE']
```

### 3. Integrar em pdf_extractor.py

```python
# Usar config para timeouts
from config import load_env_config

config = load_env_config(verbose=False)
TIMEOUT = config['REQUEST_TIMEOUT']
```

---

## Checklist de Integração

- [ ] Importar funções do config no app.py
- [ ] Inicializar config e logger
- [ ] Remover valores hardcoded
- [ ] Usar config['KEY'] ao invés de constantes
- [ ] Adicionar logging em pontos importantes
- [ ] Criar arquivo .env com chave de API
- [ ] Testar carregamento de config
- [ ] Verificar arquivo de log
- [ ] Remover código de teste/debug
- [ ] Documentar em docstring

---

## Troubleshooting

### "config não foi encontrado"
Certifique-se que `config.py` está na mesma pasta que `app.py`

### "GEMINI_API_KEY não configurada"
Crie ou edite `.env` e adicione: `GEMINI_API_KEY=sua_chave`

### "Logs não aparecem"
Verifique se a pasta `logs/` foi criada automaticamente

### "Erro de encoding nos logs"
Use Python 3.7+ ou configure encoding UTF-8

---

## Suporte

Se tiver dúvidas:
1. Leia o `CONFIG_GUIDE.md`
2. Execute `python config.py` para testar
3. Verifique os logs em `logs/contrato_seguro.log`
4. Veja os exemplos em `config.py` (docstrings)

---

**Data:** 2024  
**Versão:** 1.0  
**Status:** Pronto para integração ✅
