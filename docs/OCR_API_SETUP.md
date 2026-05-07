# Configuração de OCR via API (OCR.space)

## Por que usar OCR.space API?

Quando o aplicativo está rodando no Render (ou outro servidor sem Tesseract instalado), o OCR via API é usado automaticamente como fallback para processar PDFs escaneados.

**Vantagens:**
- ✅ Não precisa instalar Tesseract no servidor
- ✅ Funciona com deploy Python simples (não precisa Docker)
- ✅ 25,000 requisições grátis por mês
- ✅ Suporta português
- ✅ Fallback automático (usa Tesseract local quando disponível)

**Desvantagens:**
- ⚠️ Limite de 25,000 páginas/mês no plano gratuito
- ⚠️ PDFs são enviados para servidor externo (questão de privacidade)
- ⚠️ Pode ser mais lento que Tesseract local

## Como obter a chave gratuita

### Passo 1: Criar conta gratuita

1. Acesse: https://ocr.space/ocrapi
2. Role até a seção **"Free OCR API"**
3. Clique em **"Register"** ou **"Get your free API key"**
4. Preencha o formulário:
   - Nome
   - Email
   - Empresa (pode usar "Personal" ou "Trust Corporation")
5. Você receberá a chave por email imediatamente

### Passo 2: Configurar no projeto

**Localmente (.env):**
```bash
OCR_SPACE_API_KEY=sua-chave-aqui
```

**No Render:**
1. Acesse seu serviço no Render Dashboard
2. Vá em **Environment** > **Add Environment Variable**
3. Key: `OCR_SPACE_API_KEY`
4. Value: cole sua chave
5. Salve e faça redeploy

## Como funciona o fallback automático

O sistema tenta usar Tesseract local primeiro (mais rápido e privado):

1. **Tesseract disponível** → Usa OCR local (ideal)
2. **Tesseract não encontrado** → Usa OCR.space API automaticamente
3. **API não configurada** → Retorna erro informativo

Logs indicam qual método foi usado:
- `"Tesseract OCR selecionou idioma..."` = OCR local
- `"Tesseract indisponível, tentando OCR.space API..."` = Fallback para API

## Limites do plano gratuito

- **25,000 requisições/mês** = ~833 requisições/dia
- Sem limite de tamanho de arquivo
- Suporta múltiplos idiomas (português, inglês, espanhol, etc.)
- Rate limit: ~10 requisições/segundo

## Privacidade

⚠️ **IMPORTANTE:** Ao usar OCR.space, os PDFs são enviados para servidor externo.

**Para dados sensíveis:**
- Use Tesseract local (instalado na máquina)
- Ou use deploy Docker no Render (Tesseract incluído)

**Para uso geral:**
- OCR.space é seguro e confiável
- PDFs não são armazenados após processamento (segundo política deles)

## Troubleshooting

### Erro: "OCR_SPACE_API_KEY não configurada"
- Adicione a variável no .env (local) ou no Render Environment

### Erro: "API key invalid"
- Verifique se copiou a chave completa do email
- Chave deve começar com `K8` (exemplo: `K88888888888`)

### Erro: "Rate limit exceeded"
- Limite de 25,000 requisições/mês atingido
- Aguarde início do próximo mês ou faça upgrade

### OCR muito lento
- OCR via API é naturalmente mais lento que local
- Considere usar Docker deploy com Tesseract para performance

## Upgrade para plano pago (opcional)

Se precisar de mais requisições:
- **Pro 1:** $6.99/mês - 100,000 requisições
- **Pro 2:** $29.99/mês - 500,000 requisições
- **Pro PDF:** $59.99/mês - 1,000,000 requisições + features extras

Mais info: https://ocr.space/ocrapi/pricing
