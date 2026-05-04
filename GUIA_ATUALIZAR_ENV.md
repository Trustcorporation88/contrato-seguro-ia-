# 📝 Guia - Atualizar .env com Ollama

## 🎯 O que você precisa fazer

Seu `.env` atual só tem Gemini. Vamos adicionar as variáveis do Ollama Cloud.

---

## 📋 Passo a Passo

### **Passo 1: Abrir o .env**

1. Navegue até a pasta do projeto
2. Abra o arquivo `.env` em um editor de texto
   - Notepad (Windows)
   - VS Code
   - Sublime Text
   - Qualquer editor

### **Passo 2: Copiar sua chave API do Ollama**

1. Acesse: https://ollama.ai
2. Faça login com sua conta
3. Vá para: **Settings** ou **API Keys**
4. Copie sua chave (formato: `ollama_sk_xxxxx`)

### **Passo 3: Adicionar as linhas ao .env**

Adicione estas linhas ao final do seu `.env`:

```env
# ================================================================
# OLLAMA - Ollama Cloud API
# ================================================================
OLLAMA_API_URL=https://api.ollama.ai/api/generate
OLLAMA_API_KEY=paste_sua_chave_aqui
OLLAMA_MODEL=mistral
```

### **Passo 4: Substituir a chave**

Procure por: `paste_sua_chave_aqui`

Substitua por: Sua chave real (ex: `ollama_sk_1234567890abcdef`)

**Resultado:**
```env
OLLAMA_API_KEY=ollama_sk_1234567890abcdef
```

### **Passo 5: Salvar**

- CTRL + S (ou Cmd + S no Mac)
- Feche o editor

---

## ✅ Arquivo .env Completo (Exemplo)

```env
# === GEMINI ===
GEMINI_API_KEY=sua_chave_gemini_aqui
GEMINI_MODEL=gemini-2.5-flash

# === OLLAMA CLOUD ===
OLLAMA_API_URL=https://api.ollama.ai/api/generate
OLLAMA_API_KEY=ollama_sk_seu_token_aqui
OLLAMA_MODEL=mistral
```

---

## 🔍 Verificar se está correto

### **Checklist:**
- [ ] Tem `GEMINI_API_KEY` com sua chave Gemini
- [ ] Tem `OLLAMA_API_URL=https://api.ollama.ai/api/generate`
- [ ] Tem `OLLAMA_API_KEY=ollama_sk_...`
- [ ] Tem `OLLAMA_MODEL=mistral`
- [ ] Não há espaços extras antes/depois das chaves
- [ ] Não há `#` no começo da linha (comentado)

---

## 🚀 Testar

### **1. Executar a app:**
```bash
streamlit run app.py
```

### **2. Barra lateral:**
- Escolha **"Ollama (Cloud)"**

### **3. Testar análise:**
- Carregue um contrato
- Clique "Analisar"
- Aguarde resposta

✅ Se funcionar, está correto!

---

## ⚠️ Erros Comuns

### **Erro: "Unauthorized"**
```
Problema: Chave API incorreta ou expirada
Solução: Copie novamente da conta ollama.ai
```

### **Erro: "Connection refused"**
```
Problema: URL errada
Solução: Use: https://api.ollama.ai/api/generate (HTTPS, não HTTP)
```

### **Erro: "Model not found"**
```
Problema: Nome do modelo errado
Solução: Use: mistral, llama2, neural-chat, ou orca-mini
```

### **Erro: "No module named 'urllib'"**
```
Problema: Arquivo analyzer.py não foi atualizado
Solução: Execute: git pull ou reinstale os arquivos
```

---

## 📊 Modelos Disponíveis

Configure `OLLAMA_MODEL` com um dos valores:

```env
OLLAMA_MODEL=mistral          # Recomendado - Muito bom
OLLAMA_MODEL=llama2           # Alternativa - Também bom
OLLAMA_MODEL=neural-chat      # Otimizado para chat
OLLAMA_MODEL=orca-mini        # Leve e rápido
```

---

## 💡 Dicas

- **Teste com Gemini primeiro** para validar a app
- **Depois mude para Ollama** (mais barato/sem custos)
- **Não compartilhe sua chave API** com ninguém
- **Guarde em local seguro** (arquivo .env local)

---

## 🎯 Resultado Final

Depois de atualizar, você terá:

✅ **Gemini** - Para análises de alta qualidade  
✅ **Ollama Cloud** - Para análises privadas/sem limites  
✅ Seleção na barra lateral da app  
✅ Compartilhamento WhatsApp funcionando  

---

## ❓ Dúvidas?

Se tiver problema:

1. Verifique se a chave está correta (sem espaços)
2. Verifique se a URL é HTTPS (não HTTP)
3. Reinicie a app (`Ctrl + C` e execute novamente)
4. Verifique os logs de erro

---

**Pronto! Agora você tem acesso aos dois modelos! 🚀**
