# 🌐 Setup Ollama Cloud API

## ✅ O que você já fez

✅ Criou conta em ollama.ai  
✅ Criou uma API Key  
✅ Agora precisa configurar na aplicação

---

## 🔗 API Endpoint

```
Endpoint: https://api.ollama.ai/api/generate
Autenticação: Bearer Token (sua chave API)
```

---

## ⚙️ Configurar .env

Edite o arquivo `.env` na raiz do projeto:

```env
# === GEMINI (Opcional) ===
GEMINI_API_KEY=sua_chave_gemini

# === OLLAMA CLOUD (Obrigatório) ===
OLLAMA_API_URL=https://api.ollama.ai/api/generate
OLLAMA_API_KEY=sua_chave_api_aqui
OLLAMA_MODEL=mistral
```

### **Onde colocar a chave?**

1. Abra o arquivo `.env` (na raiz do projeto)
2. Procure por `OLLAMA_API_KEY=`
3. Cole sua chave:
   ```env
   OLLAMA_API_KEY=ollama_sk_seu_token_aqui
   ```

---

## 🔑 Encontrar sua Chave API

### **Passo 1:** Acesse ollama.ai
```
https://ollama.ai
```

### **Passo 2:** Faça login
- Email e senha que você criou

### **Passo 3:** Vá para API Keys
```
Menu → API Keys (ou Settings)
```

### **Passo 4:** Copie a chave
- Formato: `ollama_sk_xxxxxxxxxxxxxxxxxxxxx`

### **Passo 5:** Cole no .env
```env
OLLAMA_API_KEY=ollama_sk_xxxxxxxxxxxxxxxxxxxxx
```

---

## 🚀 Como Usar

### **1. Configurar .env**
```env
OLLAMA_API_KEY=sua_chave_aqui
OLLAMA_API_URL=https://api.ollama.ai/api/generate
OLLAMA_MODEL=mistral
```

### **2. Executar Aplicação**
```bash
streamlit run app.py
```

### **3. Selecionar Modelo**
- Barra lateral
- Escolha: **"Ollama (Cloud)"**
- Carregue um contrato
- Clique em "Analisar"

---

## ✨ Vantagens API Cloud

✅ **Sem instalação** - Não precisa rodar Ollama local  
✅ **Acesso de qualquer lugar** - Funciona da internet  
✅ **Modelos atualizados** - Sempre a versão mais nova  
✅ **Computação na cloud** - Não usa seu CPU/GPU  
✅ **Confiável** - Infraestrutura profissional  

---

## 📊 Requisição/Resposta

### **Requisição:**
```json
{
  "model": "mistral",
  "prompt": "Analise este contrato...",
  "stream": false,
  "temperature": 0.7,
  "top_p": 0.9
}
```

### **Headers:**
```
Authorization: Bearer ollama_sk_xxxxx
Content-Type: application/json
```

### **Resposta:**
```json
{
  "response": "Análise completa do contrato...",
  "done": true
}
```

---

## 🔄 Modelos Disponíveis

Na API Cloud você pode usar:

```
mistral          (Recomendado)
llama2           (Alternativa)
neural-chat      (Chat otimizado)
orca-mini        (Leve e rápido)
```

Configure no `.env`:
```env
OLLAMA_MODEL=mistral
```

---

## 🆘 Troubleshooting

### **Problema: "Unauthorized"**
```
Solução: Verifique a chave API
- Copie novamente da conta ollama.ai
- Cole sem espaços extras
```

### **Problema: "Connection refused"**
```
Solução: Verifique a URL
OLLAMA_API_URL=https://api.ollama.ai/api/generate
(Certifique-se que é HTTPS, não HTTP)
```

### **Problema: "Model not found"**
```
Solução: Verifique o nome do modelo
OLLAMA_MODEL=mistral (padrão)
ou
OLLAMA_MODEL=llama2
```

### **Problema: Resposta lenta**
```
Solução: Pode ser limite de requisições
- Aguarde alguns segundos
- Tente novamente
```

---

## 📋 Checklist

- [ ] Criar conta em ollama.ai
- [ ] Gerar API Key
- [ ] Copiar chave
- [ ] Editar arquivo .env
- [ ] Colar chave em OLLAMA_API_KEY
- [ ] Salvar .env
- [ ] Executar: `streamlit run app.py`
- [ ] Selecionar "Ollama (Cloud)"
- [ ] Testar com um contrato

---

## 🎯 Resumo

| Item | Valor |
|------|-------|
| **API URL** | `https://api.ollama.ai/api/generate` |
| **Autenticação** | Bearer Token (sua chave) |
| **Variável .env** | `OLLAMA_API_KEY` |
| **Modelo Padrão** | `mistral` |
| **Tipo** | Cloud (sem instalação local) |

---

## 🚀 Próximas Etapas

1. Configure o `.env` com sua chave
2. Execute: `streamlit run app.py`
3. Teste o compartilhamento WhatsApp
4. Aproveite a análise jurídica com IA!

---

**Versão:** 1.0  
**Status:** ✅ Pronto para usar  
**Tipo:** Ollama Cloud API com autenticação

Sucesso! 🎉
