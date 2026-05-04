# 🏗️ Arquitetura do Módulo config.py

Documentação da estrutura e fluxo do módulo de configuração centralizada.

## 📊 Diagrama Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                    ContratoSeguro AI                            │
│                    app.py / analyzer.py                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ imports
                         │
                         ▼
        ┌────────────────────────────────────────┐
        │          config.py (CENTRAL)          │
        │  ─────────────────────────────────    │
        │                                        │
        │  1. CONSTANTES                         │
        │  2. FUNÇÕES DE CARREGAMENTO            │
        │  3. VALIDAÇÕES                         │
        │  4. LOGGING                            │
        │                                        │
        └─┬──────────┬──────────┬────────────┬──┘
          │          │          │            │
          ▼          ▼          ▼            ▼
      .env.example  .env      logs/      cache/
      (template)   (secrets)  (logs)     (temp)
```

## 🔄 Fluxo de Inicialização

```
Aplicação Inicia
    │
    ▼
┌─────────────────────────┐
│ from config import ...  │
└────────────┬────────────┘
             │
             ▼
┌──────────────────────────────┐
│ load_env_config()            │
├──────────────────────────────┤
│ 1. Procura .env              │
│ 2. Carrega variáveis         │
│ 3. Cria diretórios           │
│ 4. Valida configurações      │
│ 5. Retorna Dict com config   │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ setup_logging()              │
├──────────────────────────────┤
│ 1. Cria diretório logs/      │
│ 2. Configura formatação      │
│ 3. Handler para arquivo      │
│ 4. Handler para console      │
│ 5. Retorna Logger            │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ App Pronta!                  │
│ config, logger, pronto       │
└──────────────────────────────┘
```

## 🎯 Estrutura de Constantes

```python
config.py
├── 📦 LIMITES
│   ├── MAX_FILE_SIZE = 50MB
│   └── MIN_TEXT_LENGTH = 10
│
├── 🤖 MODELOS IA
│   ├── GEMINI_MODEL = "gemini-2.0-flash"
│   └── OLLAMA_MODEL = "mistral"
│
├── 🌐 URLs
│   └── OLLAMA_URL = "http://localhost:11434/api/generate"
│
├── ⏱️ TIMEOUTS
│   ├── REQUEST_TIMEOUT = 30s
│   └── ANALYSIS_TIMEOUT = 300s
│
├── 🔄 RETRIES
│   ├── MAX_RETRIES = 3
│   └── RETRY_DELAY = 2s
│
├── 📁 DIRETÓRIOS
│   ├── CACHE_DIR = "cache/"
│   ├── TEMP_DIR = "temp/"
│   └── LOGS_DIR = "logs/"
│
├── 💾 CACHE
│   ├── MAX_CACHE_SIZE = 100
│   └── CACHE_EXPIRY_HOURS = 24
│
└── 📝 LOGGING
    ├── LOG_LEVEL = "INFO"
    ├── LOG_FORMAT = "%(asctime)s..."
    ├── LOG_MAX_BYTES = 10MB
    └── LOG_BACKUP_COUNT = 5
```

## 📋 Estrutura de Funções

```
config.py
│
├── CARREGAMENTO
│   ├── load_env_config()              → Dict[str, Any]
│   └── _validate_config()             → None (lança erro se inválido)
│
├── VALIDAÇÕES
│   ├── check_dependencies()           → Dict[str, bool]
│   ├── check_api_keys()               → Dict[str, bool]
│   ├── _module_exists()               → bool
│   └── _validate_directories()        → Dict[str, bool]
│
├── LOGGING
│   └── setup_logging()                → Logger
│
├── UTILIDADES
│   ├── print_config_summary()         → None (exibe resumo)
│   ├── _create_directories()          → None
│   └── __main__ (teste)               → None (roda testes)
│
└── CONSTANTES
    ├── MAX_FILE_SIZE
    ├── GEMINI_MODEL
    ├── REQUIRED_PACKAGES
    └── ... (todas as constantes)
```

## 🔀 Fluxo de Validação

```
check_dependencies()
    │
    ├─► Itera REQUIRED_PACKAGES
    │   └─► Verifica cada pacote
    │       ├─► Instalado? ✅
    │       └─► Faltando? ❌ (erro se raise_error=True)
    │
    └─► Itera OPTIONAL_PACKAGES
        └─► Verifica cada pacote
            ├─► Instalado? ✅
            └─► Faltando? ⚠️ (apenas aviso)

check_api_keys()
    │
    ├─► Itera REQUIRED_KEYS
    │   └─► GEMINI_API_KEY
    │       ├─► Definida? ✅
    │       └─► Faltando? ❌ (erro se não definida)
    │
    └─► Itera OPTIONAL_KEYS
        └─► OLLAMA_API_KEY
            ├─► Definida? ✅
            └─► Faltando? ⚠️ (apenas aviso)

_validate_config()
    │
    ├─► MAX_FILE_SIZE > 0?
    ├─► MIN_TEXT_LENGTH >= 0?
    ├─► REQUEST_TIMEOUT > 0?
    ├─► ANALYSIS_TIMEOUT > 0?
    ├─► MAX_RETRIES >= 0?
    ├─► MAX_CACHE_SIZE >= 0?
    └─► Diretórios existem?
        └─► Tudo válido? ✅
        └─► Algo errado? ❌ (ValueError)
```

## 📂 Estrutura de Diretórios

```
ContratoSeguro-IA/
│
├── config.py                    ← Módulo principal
├── .env                         ← Variáveis (privado)
├── .env.example                 ← Template
│
├── app.py                       ← Usa config
├── analyzer.py                  ← Pode usar config
├── pdf_extractor.py             ← Pode usar config
├── cache_manager.py             ← Pode usar config
│
├── logs/                        ← Criado automaticamente
│   └── contrato_seguro.log     ← Arquivo de log principal
│
├── cache/                       ← Criado automaticamente
│   └── *.pkl                   ← Cache de análises
│
├── temp/                        ← Criado automaticamente
│   └── *.tmp                   ← Temporários
│
├── CONFIG_GUIDE.md              ← Documentação completa
├── INTEGRACAO_CONFIG.md         ← Guia de integração
├── README_CONFIG.md             ← README rápido
└── ARQUITETURA_CONFIG.md        ← Este arquivo
```

## 🔗 Mapa de Dependências

```
app.py
├── imports config
│   ├── load_env_config()
│   ├── setup_logging()
│   └── check_dependencies()
│
├── analyzer.py
│   └── pode usar config
│
├── pdf_extractor.py
│   └── pode usar config
│
└── cache_manager.py
    └── pode usar config
```

## 💾 Formato de Arquivo .env

```
.env (privado, não commitar)
│
├── [API KEYS]
│   ├── GEMINI_API_KEY=xyz...
│   └── OLLAMA_API_KEY=xyz... (opcional)
│
├── [MODELOS]
│   ├── GEMINI_MODEL=...
│   └── OLLAMA_MODEL=...
│
├── [URLs]
│   └── OLLAMA_URL=...
│
├── [LIMITES]
│   ├── MAX_FILE_SIZE=...
│   └── MIN_TEXT_LENGTH=...
│
├── [TIMEOUTS]
│   ├── REQUEST_TIMEOUT=...
│   └── ANALYSIS_TIMEOUT=...
│
├── [CACHE]
│   ├── MAX_CACHE_SIZE=...
│   └── CACHE_EXPIRY_HOURS=...
│
└── [LOGGING]
    └── LOG_LEVEL=...
```

## 📊 Fluxo de Logging

```
logger.info("Mensagem")
    │
    ▼
┌─────────────────────────────────────┐
│ Logger formatação                   │
│ "2024-04-29 11:31:39,657 - ..."   │
└────────────┬────────────────────────┘
             │
     ┌───────┴──────────┐
     │                  │
     ▼                  ▼
┌──────────────┐   ┌─────────────────┐
│ Console      │   │ Arquivo        │
│ (stdout)     │   │ logs/*.log      │
│              │   │ (com rotação)   │
│ tempo real   │   │ 10MB max        │
└──────────────┘   └─────────────────┘
```

## 🎬 Inicialização em Ordem

```
1. CARREGAMENTO
   app.py inicia
   └─► from config import ...
   
2. IMPORTS
   Funções disponíveis
   └─► load_env_config
   └─► setup_logging
   └─► check_dependencies

3. VALIDAÇÕES (opcional)
   check_dependencies()  ← Verifica libs
   check_api_keys()      ← Verifica chaves

4. CONFIGURAÇÃO
   config = load_env_config()
   ├─► Carrega .env
   ├─► Cria diretórios
   ├─► Valida valores
   └─► Retorna Dict

5. LOGGING
   logger = setup_logging()
   ├─► Cria logs/
   ├─► Handler arquivo
   ├─► Handler console
   └─► Pronto para usar

6. APLICAÇÃO
   Seu código roda
   └─► Usa config['KEY']
   └─► logger.info(...)
```

## 🔐 Segurança

```
.gitignore (proteger)
├── .env          ← NUNCA commitar
├── *.log         ← Logs privados
└── cache/        ← Cache privado

.env.example (compartilhar)
├── Sem valores sensíveis
├── Apenas estrutura
└── Serve como template
```

## 🧪 Teste de Inicialização

```
python config.py
    │
    ├─► check_dependencies()   ✅/❌
    ├─► check_api_keys()       ✅/⚠️
    ├─► load_env_config()      ✅/❌
    ├─► setup_logging()        ✅
    ├─► print_config_summary() 📊
    └─► teste logging          ✅/❌
```

## 📈 Escalabilidade

```
Fase 1: Básica
  └─► Constantes em config.py

Fase 2: Com Validações
  ├─► check_dependencies()
  └─► check_api_keys()

Fase 3: Com Logging
  ├─► setup_logging()
  └─► Logger em todo código

Fase 4: Avançada (futuro)
  ├─► Múltiplos ambientes (dev, prod, test)
  ├─► Secrets Manager integrado
  ├─► Config database
  └─► Hot reload de configs
```

## 🔗 Padrão de Design

**Padrão:** Singleton com Lazy Loading

```
┌─────────────────────┐
│ config.py           │
├─────────────────────┤
│ @lru_cache(1)       │ ← Cache a primeira chamada
│ setup_logging()     │   (evita duplicatas)
│                     │
│ load_env_config()   │ ← Carrega uma única vez
└─────────────────────┘
        │
        │ Sempre retorna
        │ mesma instância
        ▼
     Código (app.py, etc)
```

## 💡 Fluxo Recomendado

```
APLICAÇÃO INICIA
    │
    ├─► try:
    │   ├─► check_dependencies()
    │   ├─► load_env_config()
    │   ├─► setup_logging()
    │   └─► logger.info("OK!")
    │
    ├─► except ImportError:
    │   └─► print("Instale dependências")
    │
    ├─► except ValueError:
    │   └─► print("Configure .env")
    │
    └─► except Exception:
        └─► print("Erro desconhecido")
```

---

## 📞 Referência Rápida

| Função | Input | Output | Tempo |
|--------|-------|--------|-------|
| load_env_config() | - | Dict | ~50ms |
| setup_logging() | - | Logger | ~10ms |
| check_dependencies() | - | Dict | ~100ms |
| check_api_keys() | - | Dict | ~5ms |

## 🎓 Conceitos

- **Constantes:** Valores fixos imutáveis
- **Variáveis de Ambiente:** Valores externos (segurança)
- **Validação:** Verificação de integridade
- **Logging:** Rastreamento de eventos
- **Singleton:** Uma única instância
- **Lazy Loading:** Carregamento sob demanda

---

**Versão:** 1.0  
**Data:** 2024  
**Status:** Documentado ✅
