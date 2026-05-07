# 📋 ContratoSeguro AI - Versão 2.0 Otimizada

Sistema inteligente de análise de riscos contratuais com IA, desenvolvido para escritórios de advocacia.

## ✨ O que foi otimizado?

### 🔒 **1. Segurança Aprimorada**
- **BytesIO em Memória**: PDFs não são mais salvos em disco. Processamento direto em memória
- **Zero Arquivos Temporários**: Dados sensíveis nunca tocam o disco
- **Limpeza Automática**: Coleta de lixo Python limpa memória automaticamente

```python
# Antes (inseguro):
with open("temp.pdf", "wb") as f:
    f.write(uploaded_file.getbuffer())
texto = extrair_texto_pdf("temp.pdf")

# Depois (seguro):
texto = extrair_texto_pdf_bytes(BytesIO(file_content))
```

### ✔️ **2. Validação Robusta (5+ verificações)**

| Validação | Descrição | Limite |
|-----------|-----------|--------|
| 🔴 Arquivo Vazio | Rejeita uploads vazios | 0 bytes |
| 📦 Tamanho Máximo | Limite de upload | 50 MB |
| 🐛 PDF Corrompido | Detecta PDFs inválidos | - |
| 📝 Texto Mínimo | Rejeita arquivos com pouco texto | 10 caracteres |
| 🔤 Codificação | Suporta múltiplas codificações | UTF-8, Latin-1 |

Mensagens de erro claras com emojis:
```
❌ Arquivo vazio detectado. Por favor, envie um arquivo com conteúdo.
❌ Arquivo muito grande (75.5MB). Limite máximo: 50MB
❌ PDF corrompido ou inválido: ...
```

### 🎨 **3. Interface Melhorada**

#### Indicadores Visuais de Risco
```
🔴 Alto Risco      (cor vermelha)
🟠 Médio Risco     (cor laranja)  
🟢 Baixo Risco     (cor verde)
```

#### Estatísticas em Tempo Real
```
┌─────────────────────────────────────────┐
│ 🔴 Riscos Altos │ 🟠 Riscos Médios      │
│       5         │        8              │
├─────────────────┼──────────────────────┤
│ 🟢 Riscos Baixos │ ⏱️  Tempo de Análise │
│       12        │      3.2 segundos    │
└─────────────────────────────────────────┘
```

### 🎯 **4. Melhorias UX**

**Fluxo Completo:**
1. ⬆️ **Upload** - Valida automaticamente
2. 👀 **Preview** - Veja os primeiros 1000 caracteres
3. ✏️ **Editar** - Opção de editar texto antes de analisar
4. 🚀 **Analisar** - Barra de progresso em tempo real
5. 📊 **Ver Resultado** - Estatísticas + análise completa
6. 📥 **Exportar** - Download ou WhatsApp

**Botões Inteligentes:**
- 🗑️ **Limpar Análise** - Reinicia a aplicação
- 🔄 **Nova Análise** - Analisa novo arquivo
- ❌ **Fechar** - Fecha os resultados
- 📥 **Baixar** - Salva como Markdown
- 💬 **WhatsApp** - Compartilha resultado

### 💾 **5. Cache de Análises**

Usa hash SHA256 para identificar análises:
```python
# Primeira análise: 3.2 segundos
# Segunda análise (mesmo contrato): 0.0 segundos (do cache!)
```

**Benefícios:**
- ⚡ Análises instantâneas para documentos iguais
- 💰 Reduz custo de API (Gemini/Ollama)
- 📊 Indicador visual de cache ativo
- 🔄 Reutilização automática

### 🔧 **6. Tratamento de Exceções**

- ✓ Try-Except estruturado
- ✓ Diferentes tipos de erro tratados
- ✓ Barra de progresso com status
- ✓ Logging detalhado (INFO, WARNING, ERROR)
- ✓ Mensagens amigáveis ao usuário
- ✓ UI responsiva mesmo com erros

---

## 🚀 Quick Start

### Pré-requisitos
```bash
Python 3.8+
pip
```

### Instalação

1. **Clone ou acesse o diretório do projeto:**
```bash
cd C:\ContratoSeguro-IA
```

2. **Instale as dependências:**
```bash
pip install streamlit pymupdf google-generativeai python-dotenv requests
```

3. **Configure as variáveis de ambiente:**
```bash
# Crie um arquivo .env na raiz do projeto
GEMINI_API_KEY=sua_chave_aqui
```

### Executar a Aplicação

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`

---

## Render

O projeto está pronto para deploy no Render com `render.yaml` e `Dockerfile`.

### Start da aplicação

O container inicia com `python run_app.py`, que respeita:

```bash
PORT=<porta do ambiente>
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Dependências de OCR

O `Dockerfile` instala:

```bash
tesseract-ocr
tesseract-ocr-por
```

Isso mantém a leitura de PDFs escaneados funcionando no servidor de forma confiável.

### Variáveis obrigatórias no Render

Configure no painel do Render ou via Blueprint:

```env
DEEPSEEK_API_KEY=
GEMINI_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://jus.trustcorp.com.br
```

Se usar integrações adicionais, configure também as variáveis de WhatsApp e SMTP.

---

## 📁 Estrutura do Projeto

```
ContratoSeguro-IA/
├── app.py                          # 🎯 Aplicação principal (450+ linhas)
├── analyzer.py                     # 🤖 Lógica de análise
├── pdf_extractor.py               # 📄 Extração de PDF (atualizado)
├── SYSTEM_PROMPT.txt              # 📝 Prompt para IA
├── .env                           # 🔑 Variáveis de ambiente
├── requirements.txt               # 📦 Dependências
├── README_OTIMIZADO.md           # 📖 Este documento
├── MELHORIAS.md                  # 📋 Documentação detalhada
└── RESUMO_OTIMIZACOES.txt       # ✅ Resumo executivo
```

---

## 📊 Funcionalidades

### ✅ Upload e Validação
- Suporta PDF e TXT
- Limite de 50MB (ajustável)
- Validação em tempo real
- Detecção de arquivo corrompido

### 👀 Preview e Edição
- Preview dos primeiros 1000 caracteres
- Editor de texto integrado
- Atualização em tempo real

### 🔍 Análise Inteligente
- Integração com Gemini ou Ollama
- Barra de progresso visual
- Status em tempo real
- Cronometragem de análise

### 📊 Estatísticas
- Contagem de riscos por nível (Alto/Médio/Baixo)
- Tempo de análise em segundos
- Cache ativo indicado

### 📥 Exportação
- Download como Markdown
- Compartilhamento no WhatsApp
- Informações de cache

---

## ⚙️ Configurações Ajustáveis

No arquivo `app.py`, linhas 12-13:

```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MIN_TEXT_LENGTH = 10               # 10 caracteres mínimo
```

### Exemplos de Ajuste

```python
# Para permitir arquivos maiores:
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Para ser mais restritivo:
MAX_FILE_SIZE = 10 * 1024 * 1024   # 10MB
MIN_TEXT_LENGTH = 50               # 50 caracteres mínimo
```

---

## 📚 Documentação Detalhada

Para entender melhor as otimizações, veja:

- **[MELHORIAS.md](MELHORIAS.md)** - Explicação técnica completa de cada otimização
- **[RESUMO_OTIMIZACOES.txt](RESUMO_OTIMIZACOES.txt)** - Sumário executivo com visual

---

## 🔑 Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# API Key do Google Gemini (obrigatório para Gemini)
GEMINI_API_KEY=sua_chave_api_aqui

# Endereço do Ollama (opcional, padrão: http://localhost:11434)
OLLAMA_API_URL=http://localhost:11434

# Modelo Ollama a usar (padrão: llama2)
OLLAMA_MODEL=llama2
```

### Como Obter Chaves

**Gemini (Google):**
1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crie uma nova API Key
3. Cole em `GEMINI_API_KEY`

**Ollama:**
1. Instale Ollama de [ollama.ai](https://ollama.ai)
2. Execute `ollama serve`
3. Deixe em `http://localhost:11434`

---

## 📈 Comparação Antes vs Depois

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Segurança** | Salva PDF em disco | BytesIO (memória) |
| **Validação** | Básica | 5+ verificações |
| **UI** | Simples | Estruturada |
| **Cache** | Não | Sim (SHA256) |
| **Tempo** | Não medido | Exibido em segundos |
| **Estatísticas** | Não | 4 métricas |
| **Edição** | Não | Sim |
| **Preview** | Não | Sim (1000 chars) |
| **Botões** | Mínimo | Limpar, Nova, Fechar |
| **Erros** | Genéricos | Específicos |
| **Linhas de código** | ~50 | ~450 |

---

## 🐛 Solução de Problemas

### "API Key não configurada"
```
❌ Erro: Chave da API Gemini não configurada

Solução:
1. Crie um arquivo .env
2. Adicione: GEMINI_API_KEY=sua_chave
3. Reinicie a aplicação
```

### "PDF corrompido ou inválido"
```
❌ PDF corrompido ou inválido: ...

Solução:
1. Verifique se o PDF abre em outro programa
2. Tente converter o PDF (às vezes PDFs antigos são incompatíveis)
3. Tente um PDF diferente
```

### "Arquivo muito grande"
```
❌ Arquivo muito grande (75.5MB). Limite máximo: 50MB

Solução:
1. Comprima o PDF
2. Divida em múltiplos arquivos
3. Edite MAX_FILE_SIZE em app.py se necessário
```

### "Não consegue decodificar TXT"
```
❌ Não foi possível decodificar o arquivo TXT

Solução:
1. Salve o TXT em UTF-8 (não ANSI ou CP1252)
2. Use um editor como VS Code
3. Encoding > Save with Encoding > UTF-8
```

---

## 🔄 Fluxo de Trabalho Detalhado

```
┌─────────────────────────────────────────────────────────┐
│ 1. UPLOAD (Calcula hash SHA256)                         │
│    ├─ Valida: vazio? | tamanho? | formato?            │
│    ├─ Se PDF: extrai com BytesIO (memória)            │
│    └─ Se TXT: decodifica (UTF-8 ou Latin-1)           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 2. PREVIEW (Opcional)                                   │
│    └─ Mostra primeiros 1000 caracteres                 │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 3. EDIÇÃO (Opcional)                                    │
│    └─ Checkbox ativa text area para editar             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 4. ANÁLISE (Hash SHA256 do texto)                      │
│    ├─ Cache hit? → resultado instantâneo (0s) ✅      │
│    └─ Cache miss? → executa análise                    │
│        ├─ Progresso: 0% → 25% → 50% → 75% → 100%    │
│        ├─ Status: ⏳ → 📊 → ✅                         │
│        └─ Salva em cache para próxima vez              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│ 5. RESULTADOS                                           │
│    ├─ Estatísticas: 🔴 Alto | 🟠 Médio | 🟢 Baixo    │
│    ├─ Tempo: ⏱️ X.X segundos                          │
│    ├─ Markdown: análise completa                       │
│    └─ Ações: Download | WhatsApp | Nova | Limpar      │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Casos de Uso

### 1. Análise Rápida de Contrato
```
1. Envie PDF
2. Clique "Analisar"
3. Veja estatísticas e riscos
4. Tome decisão
```

### 2. Análise com Edição
```
1. Envie PDF
2. Veja preview
3. Edite se necessário
4. Clique "Analisar"
5. Veja resultado
```

### 3. Compartilhamento
```
1. Análise realizada
2. Clique "Compartilhar no WhatsApp"
3. Envie para cliente/colega
```

### 4. Reutilização (Cache)
```
1. Primeiro contrato: 3.2s
2. Mesmo contrato: 0.0s (do cache!)
3. Economia de tempo e dinheiro
```

---

## 📝 Dependências

```
streamlit==1.28.0+        # Interface web
pymupdf==1.23.0+          # Extração PDF em memória
google-generativeai==0.3+ # API Gemini
python-dotenv==1.0.0+     # Variáveis de ambiente
requests==2.31.0+         # HTTP (para Ollama)
```

Instale com:
```bash
pip install streamlit pymupdf google-generativeai python-dotenv requests
```

---

## 🔒 Segurança

✅ **Implementações de Segurança:**
- ✓ Processamento em memória (sem disco)
- ✓ Validação de tipo de arquivo
- ✓ Limite de tamanho de arquivo
- ✓ Tratamento de exceções robusto
- ✓ Variáveis de ambiente para chaves
- ✓ Detecção de PDF corrompido

⚠️ **Boas Práticas:**
- Nunca comita `.env` no repositório
- Use variáveis de ambiente para chaves
- Mantenha dependências atualizadas
- Valide entrada do usuário sempre
- Trate exceções adequadamente

---

## 📊 Métricas de Performance

### Tamanho de Código
- **app.py original**: ~50 linhas
- **app.py otimizado**: ~450 linhas (+800%)
- **pdf_extractor.py**: ~80 linhas

### Funcionalidades
- **Validações robustas**: 5+
- **Melhorias UX**: 8+
- **Tratamentos de erro**: 6+
- **Funções utilitárias**: 4+

### Performance
- **Cache hit**: 0.0 segundos
- **Primeira análise**: ~2-5 segundos (depende da API)
- **Memória**: ~20-50MB (dependendo do tamanho do PDF)

---

## 📄 Licença

Este projeto é propriedade intelectual de ContratoSeguro AI.

---

## 👥 Autores

**ContratoSeguro AI Team**
- Versão 1.0: Sistema base
- Versão 2.0: Otimizações completas

---

## 🔗 Links Úteis

- [Google AI Studio](https://makersuite.google.com/app/apikey) - API Keys Gemini
- [Ollama](https://ollama.ai) - IA Local
- [Streamlit Docs](https://docs.streamlit.io) - Documentação Streamlit
- [PyMuPDF](https://pymupdf.readthedocs.io) - Documentação PyMuPDF

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique [MELHORIAS.md](MELHORIAS.md)
2. Consulte a seção "Solução de Problemas"
3. Verifique os logs da aplicação
4. Procure documentação do seu modelo de IA

---

**Versão**: 2.0 (Otimizada)  
**Status**: ✅ Pronto para Produção  
**Data**: 2024

═══════════════════════════════════════════════════════════════════════════════
