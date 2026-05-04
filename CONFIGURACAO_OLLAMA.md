# 🚀 Guia Completo - Configuração Ollama

## 📋 O Que é Ollama?

**Ollama** é uma ferramenta para rodar LLMs (Large Language Models) localmente, sem internet.

- ✅ Gratuito
- ✅ Sem API keys
- ✅ Sem limites de requisições
- ✅ 100% privado (dados locais)
- ✅ Modelos abertos (Mistral, Llama2, etc)

---

## 🔗 API do Ollama

```
Endpoint: http://localhost:11434/api/generate
Método: POST
```

### Requisição:
```json
{
  "model": "mistral",
  "prompt": "Seu texto aqui",
  "stream": false,
  "temperature": 0.7
}
```

### Resposta:
```json
{
  "response": "Resposta gerada pelo modelo",
  "done": true
}
```

---

## 📥 Instalação do Ollama

### **1. Windows**
1. Baixe em: https://ollama.ai
2. Execute o instalador
3. Reinicie o computador

### **2. macOS**
```bash
brew install ollama
```

### **3. Linux**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

---

## 🎯 Configurar Modelos

### **Puxar Modelo (Download)**

```bash
# Mistral (Recomendado - 14GB, muito bom)
ollama pull mistral

# Llama 2 (Alternativa - 13GB)
ollama pull llama2

# Neural Chat (Bom para chat - 8GB)
ollama pull neural-chat

# Orca Mini (Leve - 4GB)
ollama pull orca-mini
```

### **Listar Modelos Baixados**
```bash
ollama list
```

### **Deletar Modelo**
```bash
ollama rm mistral
```

---

## ⚙️ Configurar Variáveis de Ambiente

Crie/Edite o arquivo `.env`:

```env
# === GEMINI (Cloud) ===
GEMINI_API_KEY=sua_chave_aqui

# === OLLAMA (Local) ===
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=mistral
```

---

## 🚀 Iniciar Ollama

### **Opção 1: Via Interface Gráfica**
- Abra o **Ollama Desktop**
- Ele roda em background

### **Opção 2: Via Terminal**

**Windows (PowerShell):**
```powershell
ollama serve
```

**macOS/Linux:**
```bash
ollama serve
```

Você verá:
```
time=2024-01-01T00:00:00.000Z level=INFO msg="Serving on http://localhost:11434"
```

---

## ✅ Testar Conexão

### **Via cURL:**
```bash
curl http://localhost:11434/api/generate -d "{
  \"model\": \"mistral\",
  \"prompt\": \"Olá, tudo bem?\",
  \"stream\": false
}"
```

### **Via Python:**
```python
import requests

url = "http://localhost:11434/api/generate"
payload = {
    "model": "mistral",
    "prompt": "Teste",
    "stream": False
}

response = requests.post(url, json=payload)
print(response.json()["response"])
```

---

## 🎮 Como Usar na Aplicação

### **1. Certifique-se que Ollama está rodando**
```bash
ollama serve
```

### **2. Configure o `.env`**
```env
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=mistral
```

### **3. Na Aplicação**
- Abra a barra lateral
- Escolha: **"Ollama (Local)"**
- Clique em "Analisar"
- ✅ Pronto!

---

## 📊 Comparação de Modelos

| Modelo | Tamanho | Qualidade | Velocidade | Uso |
|--------|---------|-----------|-----------|-----|
| Orca Mini | 4GB | ⭐⭐ | ⚡⚡⚡ | Teste/Demo |
| Neural Chat | 8GB | ⭐⭐⭐ | ⚡⚡ | Bom balanço |
| Mistral | 14GB | ⭐⭐⭐⭐ | ⚡ | **Recomendado** |
| Llama 2 | 13GB | ⭐⭐⭐⭐ | ⚡ | Alternativa |

---

## 💻 Requisitos de Hardware

### **Mínimo:**
- CPU: Quad-core (4 cores)
- RAM: 8GB
- Disco: 20GB

### **Recomendado:**
- CPU: 6+ cores
- RAM: 16GB+
- Disco: 30GB+
- GPU: NVIDIA/AMD (opcional, melhora muito)

### **Com GPU NVIDIA:**
```bash
# Instalar CUDA drivers
# Depois instalar Ollama normalmente
# Ollama detecta automaticamente
```

---

## 🔧 Troubleshooting

### **Problema: "Connection refused"**
```
Solução: Verifique se Ollama está rodando
$ ollama serve
```

### **Problema: "Model not found"**
```
Solução: Puxe o modelo
$ ollama pull mistral
```

### **Problema: Muito lento**
```
Solução: Use modelo menor
$ ollama pull orca-mini
$ (configure no .env)
```

### **Problema: Alto uso de RAM**
```
Solução: Feche outros programas
ou use modelo menor (orca-mini)
```

---

## 📈 Performance

### **Tempo de Resposta Típico**

| Modelo | Tempo |
|--------|-------|
| Orca Mini (4GB) | 10-20 seg |
| Neural Chat (8GB) | 20-40 seg |
| Mistral (14GB) | 30-60 seg |

*Varia conforme CPU/RAM disponível*

---

## 🔄 Gemini vs Ollama

| Aspecto | Gemini | Ollama |
|---------|--------|--------|
| **Custo** | Pago | Grátis |
| **Internet** | Requer | Não requer |
| **Privacidade** | Cloud | 100% Local |
| **Velocidade** | Muito rápido | Mais lento |
| **Qualidade** | Excelente | Boa/Muito Boa |
| **Limite** | Sim (quota) | Ilimitado |
| **Config** | API Key | Localhost |

---

## 📝 Usar Ollama na Aplicação

### **Passo 1: Baixar Modelo**
```bash
ollama pull mistral
```

### **Passo 2: Iniciar Ollama**
```bash
ollama serve
```

### **Passo 3: Configurar .env**
```env
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=mistral
```

### **Passo 4: Executar App**
```bash
streamlit run app.py
```

### **Passo 5: Selecionar Modelo**
- Barra lateral → "Ollama (Local)"
- Carregar contrato
- Analisar!

---

## ✨ Benefícios do Ollama

✅ **Sem custos** - Grátis e ilimitado  
✅ **Privado** - Tudo local, nenhum dado na cloud  
✅ **Offline** - Funciona sem internet  
✅ **Rápido** - Responde em segundos (com GPU)  
✅ **Flexível** - Troque modelos facilmente  
✅ **Escalável** - Use quanto quiser, quando quiser  

---

## 🎯 Recomendação

**Para uso em produção:**
- Use **Gemini** para melhor qualidade (custos)
- Use **Ollama** para privacidade/sem limites (mais lento)

**Para desenvolvimento/teste:**
- Use **Ollama** (grátis e ilimitado)

---

## 📖 Mais Informações

- **Site:** https://ollama.ai
- **GitHub:** https://github.com/jmorganca/ollama
- **Modelos disponíveis:** https://ollama.ai/library

---

**Versão:** 1.0  
**Data:** 2024  
**Status:** ✅ Pronto para Usar

Aproveite a análise jurídica com IA 100% local! 🚀
