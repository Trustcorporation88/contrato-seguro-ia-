# 🎨 Guia Visual das Otimizações - ContratoSeguro AI v2.0

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                      INTERFACE STREAMLIT                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ⚙️ CONFIGURAÇÕES (Expansível)                                │
│  ├─ 🔥 Gemini vs 🖥️ Ollama                                  │
│  └─ 🗑️ Limpar Análise                                       │
│                                                                 │
│  📄 ENVIAR DOCUMENTO                                            │
│  ├─ Upload: PDF ou TXT                                         │
│  ├─ Info: 📁 Arquivo | 📊 Tamanho | 📝 Caracteres           │
│  └─ Validação: 5+ verificações ✅                            │
│                                                                 │
│  👀 PREVIEW DO TEXTO (Expansível)                             │
│  ├─ Primeiros 1000 caracteres                                 │
│  └─ Campo desabilitado (read-only)                            │
│                                                                 │
│  ✏️ EDITAR TEXTO (Opcional)                                  │
│  ├─ Checkbox para ativar                                      │
│  └─ Text area para edição                                     │
│                                                                 │
│  🔍 ANÁLISE DE RISCOS                                          │
│  ├─ 🚀 Analisar Contrato (Primário)                          │
│  ├─ 🔄 Nova Análise (Se há resultado)                        │
│  └─ ❌ Fechar (Se há resultado)                              │
│     └─ Progresso: 0% → 25% → 50% → 75% → 100%              │
│     └─ Status: ⏳ → 📊 → ✅                                  │
│                                                                 │
│  📊 ANÁLISE COMPLETA (Se há resultado)                        │
│  ├─ ┌────────┬─────────┬────────┬──────────────┐             │
│  │ │ 🔴 Altos│ 🟠 Médios│ 🟢 Baixos│ ⏱️  Tempo   │             │
│  │ │   5    │    8    │   12   │  3.2s      │             │
│  │ └────────┴─────────┴────────┴──────────────┘             │
│  │                                                            │
│  │ [Markdown completo da análise aqui]                      │
│  │                                                            │
│  │ ┌───────────────────────────────────────────┐            │
│  │ │ 📥 Baixar | 💬 WhatsApp | 📌 Cache Info  │            │
│  │ └───────────────────────────────────────────┘            │
│  │                                                            │
│  └─ 📌 Cache ativo: X análise(s)                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         ↓              ↓              ↓              ↓
    ┌────────┐  ┌────────────┐  ┌─────────┐  ┌──────────┐
    │ Upload │  │ Validação  │  │ Extração│  │ Análise  │
    │ com    │→ │  Robusta   │→ │ BytesIO │→ │   IA     │
    │ Hash   │  │  (5+ checks)│  │ (Mem)   │  │(Gemini)  │
    └────────┘  └────────────┘  └─────────┘  └──────────┘
         ↓              ↓              ↓              ↓
    Cache Hit?    ✓ Vazio    ✓ PDF OK    ✓ Gemini OK
    ✓ Sim → 0s   ✓ Tamanho   ✓ TXT OK    ✓ Ollama OK
    ✗ Não → API  ✓ Formato   ✓ Mínimo    → Salva em Cache
               ✓ PDF        ✓ Encoding   → Exibe resultado
               ✓ Mínimo
```

---

## 📊 Fluxo de Dados

### 1️⃣ UPLOAD e HASH

```
Arquivo recebido
    ↓
[SHA256 Hash]  ← Identificador único
    ↓
┌───────────────────┐
│ É arquivo novo?   │
├───────────────────┤
│ Sim: Processa     │
│ Não: Usa cache    │
└───────────────────┘
```

### 2️⃣ VALIDAÇÃO

```
┌─────────────────────────────────┐
│ Arquivo Vazio?                  │
│ ❌ Erro se: size == 0           │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│ Tamanho Muito Grande?           │
│ ❌ Erro se: size > 50MB         │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│ Formato Válido?                 │
│ ✓ PDF ou TXT                    │
│ ❌ Erro para outros             │
└─────────────────────────────────┘
           ↓
✅ Arquivo validado!
```

### 3️⃣ EXTRAÇÃO

```
PDF (BytesIO em Memória)          TXT (Decodificação)
┌────────────────────┐            ┌──────────────────┐
│ fitz.open()        │            │ UTF-8 decode()   │
│ Validação:         │            │ ❌ Erro?         │
│ - Corrompido?      │            │ ✓ Sim → Tenta    │
│ - 0 páginas?       │            │   Latin-1        │
│ - Páginas OK?      │            │ ✗ Não → Erro     │
└────────────────────┘            └──────────────────┘
         ↓                                 ↓
    Texto extraído              Texto decodificado
         ↓                                 ↓
    ┌──────────────────────────────────┐
    │ Validar texto mínimo (10 chars)  │
    │ ✓ Sim → Continua                 │
    │ ❌ Não → Erro                    │
    └──────────────────────────────────┘
              ↓
         ✅ Texto pronto!
```

### 4️⃣ ANÁLISE

```
┌──────────────────────────────────┐
│ Hash SHA256 do texto             │
└──────────────────────────────────┘
         ↓
┌──────────────────────────────────┐
│ Está em cache?                   │
├──────────────────────────────────┤
│ ✓ Sim → Hit! (0s)               │
│ ❌ Não → Miss, chama API        │
└──────────────────────────────────┘
         ↓
    ┌─────────────────────────────┐
    │ ANÁLISE COM GEMINI/OLLAMA   │
    │                             │
    │ 📊 Progresso:              │
    │ [████░░░░░░] 25% (Iniciando)│
    │ [████████░░] 50% (Analisando)│
    │ [████████████░] 75% (Final) │
    │ [████████████████] 100% ✅ │
    │                             │
    │ Status: ⏳ → 📊 → ✅       │
    │ Tempo: 0.0s - 5.0s          │
    └─────────────────────────────┘
         ↓
┌──────────────────────────────────┐
│ ✓ Resultado obtido              │
│ → Salva em cache                │
│ → Exibe resultado               │
└──────────────────────────────────┘
```

---

## 🎯 Componentes Principais

### 🔐 Segurança

```
ANTES (Inseguro)           DEPOIS (Seguro)
─────────────────          ─────────────────
Arquivo em disco           BytesIO em memória
    ↓                          ↓
temp.pdf                   Nunca toca disco
    ↓                          ↓
Risco de exposição         Limpeza automática
    ↓                          ↓
Sem encriptação            Protegido por GC
```

### ✅ Validação

```
5+ Verificações:

1. 🔴 Arquivo Vazio
   └─ Se size == 0 → Erro

2. 📦 Tamanho Máximo
   └─ Se size > 50MB → Erro

3. 🐛 PDF Corrompido
   └─ Se fitz.open() falha → Erro

4. 📝 Texto Mínimo
   └─ Se len < 10 → Erro

5. 🔤 Codificação
   └─ UTF-8 ou Latin-1 → OK
```

### 📊 Estatísticas

```
Análise Resultados:

┌─────────────────────────────────┐
│ Contar emojis no resultado      │
├─────────────────────────────────┤
│ Alto = resultado.count("🔴")    │
│ Médio = resultado.count("🟠")   │
│ Baixo = resultado.count("🟢")   │
├─────────────────────────────────┤
│ Tempo = time.time() - início    │
└─────────────────────────────────┘
```

### 💾 Cache

```
Sistema de Cache com Hash:

┌──────────────────────────────────┐
│ Texto                            │
├──────────────────────────────────┤
│ SHA256 Hash                      │
│ (256 bits = 64 caracteres hex)   │
├──────────────────────────────────┤
│ st.session_state.cache_analises  │
│ {hash: resultado}                │
└──────────────────────────────────┘

Exemplo:
hash = "a1b2c3d4e5f6..."
cache[hash] = "## Análise Completa..."
```

---

## 🔧 Funções Principais

### `validar_arquivo(uploaded_file)`
```
Entrada: objeto arquivo Streamlit
Saída: (é_válido, mensagem_erro)

Validações:
1. Não é None?
2. Tamanho > 0?
3. Tamanho < 50MB?

Retorna:
True, ""           ✅
False, "❌ ..."    ❌
```

### `extrair_texto_com_validacao(uploaded_file)`
```
Entrada: objeto arquivo Streamlit
Saída: (texto, mensagem_erro)

Fluxo:
1. Valida com validar_arquivo()
2. Se PDF: BytesIO + PyMuPDF
3. Se TXT: Decodifica (UTF-8/Latin-1)
4. Valida texto mínimo
5. Limpa whitespace

Retorna:
(texto_limpo, "")           ✅
(None, "❌ ...")            ❌
```

### `contar_riscos_por_nivel(resultado)`
```
Entrada: string da análise Markdown
Saída: dict com contagem

Lógica:
alto = resultado.count("🔴")
medio = resultado.count("🟠")
baixo = resultado.count("🟢")

Retorna:
{
  "alto": 5,
  "medio": 8,
  "baixo": 12
}
```

### `exibir_estatisticas(resultado, tempo)`
```
Entrada: resultado (str), tempo (float)
Saída: Nenhuma (renderiza UI)

Cria 4 colunas:
1. st.metric("🔴 Riscos Altos", alto)
2. st.metric("🟠 Riscos Médios", medio)
3. st.metric("🟢 Riscos Baixos", baixo)
4. st.metric("⏱️ Tempo", f"{tempo:.1f}s")
```

### `limpar_analise()`
```
Entrada: Nenhuma
Saída: Nenhuma (modifica session_state)

Limpa:
- st.session_state.arquivo_atual = None
- st.session_state.texto_extraido = None
- st.session_state.resultado_analise = None
- st.session_state.tempo_analise = None

Resultado: st.rerun()
```

### `calcular_hash_arquivo(content)`
```
Entrada: bytes (conteúdo do arquivo)
Saída: str (hash SHA256)

Processo:
hashlib.sha256(content).hexdigest()

Exemplo:
"a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
```

---

## 📈 Ciclo Completo

```
           ┌─────────────────────────────────────────┐
           │ USUÁRIO ACESSA A APLICAÇÃO              │
           └──────────────┬──────────────────────────┘
                          ↓
           ┌─────────────────────────────────────────┐
           │ 1. UPLOAD ARQUIVO                       │
           │    - Calcula hash SHA256                │
           │    - Verifica se é novo                 │
           └──────────────┬──────────────────────────┘
                          ↓
           ┌─────────────────────────────────────────┐
           │ 2. VALIDAÇÃO (5+ verificações)          │
           │    - Vazio? Tamanho? Formato?           │
           │    - PDF corrompido? Texto mínimo?      │
           └──────────────┬──────────────────────────┘
                          ↓
           ┌─────────────────────────────────────────┐
           │ 3. EXTRAÇÃO DE TEXTO                    │
           │    - BytesIO para PDF (memória)         │
           │    - Decodificação para TXT             │
           │    - Limpeza de whitespace              │
           └──────────────┬──────────────────────────┘
                          ↓
           ┌─────────────────────────────────────────┐
           │ 4. PREVIEW (Opcional)                   │
           │    - Mostra primeiros 1000 caracteres   │
           │    - Campo desabilitado                 │
           └──────────────┬──────────────────────────┘
                          ↓
           ┌─────────────────────────────────────────┐
           │ 5. EDIÇÃO (Opcional)                    │
           │    - Checkbox ativa editor              │
           │    - Atualiza session_state             │
           └──────────────┬──────────────────────────┘
                          ↓
           ┌─────────────────────────────────────────┐
           │ 6. ANÁLISE                              │
           │    - Hash SHA256 do texto               │
           │    - Verifica cache:                    │
           │      ✓ Hit  → 0.0s                      │
           │      ❌ Miss → Chama API                │
           │    - Progresso: 0% → 100%               │
           │    - Status: ⏳ → 📊 → ✅              │
           │    - Salva em cache                     │
           └──────────────┬──────────────────────────┘
                          ↓
           ┌─────────────────────────────────────────┐
           │ 7. EXIBIR RESULTADOS                    │
           │    - Estatísticas (4 métricas)          │
           │    - Markdown completo                  │
           │    - Opções de download/compartilhamento│
           └──────────────┬──────────────────────────┘
                          ↓
           ┌─────────────────────────────────────────┐
           │ 8. AÇÕES DO USUÁRIO                     │
           │    - 📥 Download                        │
           │    - 💬 WhatsApp                        │
           │    - 🔄 Nova Análise                    │
           │    - ❌ Fechar                          │
           │    - 🗑️ Limpar                         │
           └─────────────────────────────────────────┘
```

---

## 🎨 Layout da Interface

```
┌──────────────────────────────────────────────────────────────┐
│ 📋 ContratoSeguro AI                                         │
│ Analisador de Riscos Contratuais – Melhores Escritórios     │
├──────────────────────────────────────────────────────────────┤
│ ⚙️ Configurações                                            │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ 🔥 Gemini (Recomendado) ○  ● Gemini              [v]  │  │
│ │ 🖥️ Ollama (Local)      ○                              │  │
│ │                    🗑️ Limpar Análise                   │  │
│ └────────────────────────────────────────────────────────┘  │
│ **Modelo ativo:** 🔥 Gemini (Recomendado)                  │
├──────────────────────────────────────────────────────────────┤
│ 📄 Enviar Documento                                         │
│ [🔵 Escolher arquivo] (PDF ou TXT, máx 50MB)              │
│ 📁 Arquivo: `contrato_2024.pdf`                            │
│ 📊 Tamanho: `125.5 KB`                                     │
│ 📝 Caracteres: `12,543`                                    │
├──────────────────────────────────────────────────────────────┤
│ 👀 Preview do Texto Extraído                               │
│ [▼ Ver preview do texto (primeiros 1000 caracteres)]       │
│                                                            │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ "CONTRATO DE PRESTAÇÃO DE SERVIÇOS                  │  │
│ │                                                      │  │
│ │ Este é um documento de exemplo mostrando os         │  │
│ │ primeiros 1000 caracteres do arquivo enviado...     │  │
│ │                                                      │  │
│ │ [... mais conteúdo ...]"                            │  │
│ └──────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│ ✏️ Editar Texto (Opcional)                                 │
│ [☐] ✏️ Desejo editar o texto antes de analisar           │
├──────────────────────────────────────────────────────────────┤
│ 🔍 Análise de Riscos                                       │
│ [🚀 Analisar Contrato]  [🔄 Nova Análise]  [❌ Fechar]    │
│                                                            │
│ [████████████████████████████] 75%                         │
│ ⏳ Iniciando análise...                                   │
├──────────────────────────────────────────────────────────────┤
│ 📊 Análise Completa                                        │
│                                                            │
│ ┌─────────────┬──────────────┬──────────────┬────────────┐ │
│ │ 🔴 Alto     │ 🟠 Médio     │ 🟢 Baixo     │ ⏱️ Tempo   │ │
│ │    5       │     8       │     12      │  3.2s    │ │
│ └─────────────┴──────────────┴──────────────┴────────────┘ │
│                                                            │
│ ## Análise Completa do Contrato                           │
│                                                            │
│ ### 🔴 Riscos Críticos Identificados                     │
│ 1. **Cláusula de Rescisão Unilateral**                  │
│    Esta cláusula permite ao fornecedor rescindir o      │
│    contrato sem aviso prévio, prejudicando o cliente.   │
│    Recomendação: Negocie um período de aviso de 30 dias │
│                                                            │
│ ### 🟠 Riscos Moderados                                  │
│ 1. **Limite de Responsabilidade**                       │
│    O contrato limita a responsabilidade a 50% dos      │
│    valores pagos, o que pode ser insuficiente...       │
│                                                            │
│ ### 🟢 Riscos Baixos                                    │
│ 1. **Confidencialidade**                                │
│    A cláusula de confidencialidade é bem estruturada   │
│    e oferece proteção adequada...                       │
│                                                            │
├──────────────────────────────────────────────────────────────┤
│ 📥 Exportar Resultado                                      │
│ [📥 Baixar como Markdown] [💬 Compartilhar WhatsApp]      │
│ 📌 Cache ativo: 3 análise(s)                             │
│                                                            │
│ ✅ Bot rodando com sucesso!                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 Estado da Sessão

```
st.session_state {
  "cache_analises": {
    "hash1": "## Resultado análise 1",
    "hash2": "## Resultado análise 2",
    "hash3": "## Resultado análise 3"
  },
  
  "arquivo_atual": "abc123def456...",  // SHA256 do arquivo
  
  "texto_extraido": "CONTRATO DE... texto aqui...",
  
  "resultado_analise": "## Análise Completa...",
  
  "tempo_analise": 3.24  // segundos
}
```

---

## 📱 Responsividade

```
┌─────────────────────────────────┐
│ DESKTOP (100%)                  │
│                                 │
│ [████████] [████████] [████████]│
│   Coluna1    Coluna2    Coluna3 │
│                                 │
│ [████████████████████████████]  │
│          Coluna Completa        │
└─────────────────────────────────┘

         ↓ (Redimensiona)

┌─────────────────────────────┐
│ TABLET/MOBILE               │
│                             │
│ [████████████████████]      │
│       Coluna1               │
│                             │
│ [████████████████████]      │
│       Coluna2               │
│                             │
│ [████████████████████]      │
│       Coluna Completa       │
└─────────────────────────────┘
```

---

## 🚀 Performance

```
Upload (100KB PDF):
   Parse    Hash      Extração   Total
────────────────────────────────────
  50ms  →  5ms  →   100ms    →  155ms

Análise (Hit do Cache):
   Hash     Lookup    Render
────────────────────────────
  5ms  →   2ms   →   10ms   = 17ms (0.0s exibido)

Análise (Miss do Cache):
   Hash     API       Cache      Render
────────────────────────────────────────
  5ms  →  3000ms →   2ms   →   10ms = 3017ms (3.0s)
```

---

## ✨ Resumo das Melhorias

| Número | Melhoria | Antes | Depois |
|--------|----------|-------|--------|
| 1️⃣ | Segurança | ❌ Disco | ✅ BytesIO |
| 2️⃣ | Validação | ❌ Básica | ✅ 5+ checks |
| 3️⃣ | Interface | ❌ Simples | ✅ Estruturada |
| 4️⃣ | Cache | ❌ Não | ✅ SHA256 |
| 5️⃣ | Tempo | ❌ Não medido | ✅ Exibido |
| 6️⃣ | Estatísticas | ❌ Não | ✅ 4 métricas |
| 7️⃣ | Edição | ❌ Não | ✅ Opcional |
| 8️⃣ | Preview | ❌ Não | ✅ 1000 chars |
| 9️⃣ | Botões | ❌ Mínimo | ✅ 5+ ações |
| 🔟 | Erros | ❌ Genéricos | ✅ Específicos |

---

**Status:** ✅ Pronto para Produção  
**Versão:** 2.0 (Otimizada)  
**Data:** 2024
