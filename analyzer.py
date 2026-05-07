import json as _json
import logging
import os
import time
from pathlib import Path
from typing import Callable, Generator, Optional

import requests

logger = logging.getLogger(__name__)

try:
    from config import load_env_config

    config = load_env_config()
    GEMINI_MODEL = config.get("GEMINI_MODEL", "gemini-2.5-flash")
    DEEPSEEK_MODEL = config.get("DEEPSEEK_MODEL", "deepseek-chat")
except Exception:
    GEMINI_MODEL = "gemini-2.5-flash"
    DEEPSEEK_MODEL = "deepseek-chat"
    logger.warning("Config nao carregada, usando modelos padrao")

try:
    from google import genai
    GEMINI_AVAILABLE = True
except Exception as import_error:
    GEMINI_AVAILABLE = False
    logger.warning(f"google-genai indisponivel. Gemini desabilitado. Motivo: {import_error}")

try:
    SYSTEM_PROMPT = (Path(__file__).resolve().parent / "SYSTEM_PROMPT.txt").read_text(
        encoding="utf-8"
    )
except Exception as prompt_error:
    logger.error(f"Falha ao carregar SYSTEM_PROMPT.txt: {prompt_error}")
    SYSTEM_PROMPT = (
        "Você é um assistente jurídico especializado em análise de contratos. "
        "Analise o texto recebido com clareza e objetividade."
    )

SELECTED_MODEL = "deepseek"

MAX_RETRIES = 3
RETRY_DELAY = 5
TIMEOUT = 120

FALLBACK_ENABLED = True

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


def set_model(model: str) -> bool:
    """Altera o modelo a ser utilizado para análise."""
    global SELECTED_MODEL
    SELECTED_MODEL = model.lower()
    logger.info(f"Modelo alterado para: {SELECTED_MODEL.upper()}")
    try:
        print(f"[OK] Modelo alterado para: {SELECTED_MODEL.upper()}")
    except UnicodeEncodeError:
        print(
            f"[OK] Modelo alterado para: {SELECTED_MODEL.upper()}".encode(
                "ascii", errors="ignore"
            ).decode()
        )
    return True


def set_fallback(enabled: bool) -> None:
    """Ativa/desativa fallback automático entre modelos."""
    global FALLBACK_ENABLED
    FALLBACK_ENABLED = enabled
    logger.info(f"Fallback automático: {'ativado' if enabled else 'desativado'}")


def estimate_tokens(texto: str) -> int:
    """Estima o número de tokens de um texto (~4 chars por token)."""
    return len(texto) // 4


def _construir_prompt(texto_contrato: str) -> str:
    """Constrói o prompt completo para análise."""
    return f"""{SYSTEM_PROMPT}

Aqui está o contrato para análise:

{texto_contrato}

Por favor, faça a análise completa seguindo exatamente o formato definido no System Prompt."""


def tentar_deepseek(
    texto_contrato: str, stream_callback: Optional[Callable[[str], None]] = None
) -> str:
    """
    Analisa o contrato usando a API DeepSeek (primária).

    DeepSeek usa API compatível com OpenAI Chat Completions.
    """
    import re as _re

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        api_key = api_key.strip()

    if not api_key:
        logger.error("DEEPSEEK_API_KEY não configurada")
        return "[ERRO] Chave da API DeepSeek não configurada"

    logger.info(f"DeepSeek key prefix: {api_key[:10]}... length={len(api_key)}")

    texto_limpo = _re.sub(r'[^\x20-\x7E\u00C0-\u00FF\u0100-\u017F\ufb00-\ufb04\u2010-\u2050\u2018-\u201D\u2022\u2026\u20A0-\u20CF]', ' ', texto_contrato)
    texto_limpo = _re.sub(r'\s{3,}', '\n\n', texto_limpo)
    texto_limpo = _re.sub(r'data:image[^;]+;base64,[A-Za-z0-9+/=]+', '[IMAGEM REMOVIDA]', texto_limpo)
    texto_limpo = _re.sub(r'<img[^>]+>', '[IMAGEM REMOVIDA]', texto_limpo)
    texto_limpo = texto_limpo.strip()[:150000]

    full_prompt = _construir_prompt(texto_limpo)
    tokens_estimados = estimate_tokens(full_prompt)
    logger.info(f"Tokens estimados para análise (DeepSeek): {tokens_estimados}")

    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Tentativa {tentativa}/{MAX_RETRIES} de análise com DeepSeek")

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": texto_limpo},
                ],
                "temperature": 0.3,
                "max_tokens": 16000,
                "stream": stream_callback is not None,
            }

            if stream_callback:
                response = requests.post(
                    DEEPSEEK_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=TIMEOUT,
                    stream=True,
                )

                if response.status_code == 200:
                    texto_completo = ""
                    for line in response.iter_lines(decode_unicode=True):
                        if line and line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                data = _json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    texto_completo += content
                                    stream_callback(content)
                            except Exception:
                                continue
                    logger.info("[OK] Analise gerada com sucesso pelo DeepSeek (stream)!")
                    try:
                        print("[OK] Analise gerada com sucesso via DeepSeek!")
                    except UnicodeEncodeError:
                        pass
                    return texto_completo
                else:
                    error_text = response.text[:200]
                    logger.warning(
                        f"DeepSeek Status {response.status_code} na tentativa {tentativa}: {error_text}"
                    )
                    if tentativa < MAX_RETRIES:
                        logger.info(f"Aguardando {RETRY_DELAY}s...")
                        time.sleep(RETRY_DELAY)
                    else:
                        return f"[ERRO] DeepSeek (Status {response.status_code})"
            else:
                response = requests.post(
                    DEEPSEEK_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=TIMEOUT,
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content:
                        logger.info("[OK] Analise gerada com sucesso pelo DeepSeek!")
                        try:
                            print("[OK] Analise gerada com sucesso via DeepSeek!")
                        except UnicodeEncodeError:
                            pass
                        return content
                    return "[ERRO] Resposta vazia do DeepSeek"
                else:
                    error_text = response.text[:200]
                    logger.warning(
                        f"DeepSeek Status {response.status_code}: {error_text}"
                    )
                    if response.status_code == 401:
                        return "[ERRO] Autenticacao DeepSeek: Verifique sua chave da API"
                    if tentativa < MAX_RETRIES:
                        logger.info(f"Aguardando {RETRY_DELAY}s...")
                        time.sleep(RETRY_DELAY)
                    else:
                        return f"[ERRO] DeepSeek (Status {response.status_code})"

        except requests.exceptions.Timeout as e:
            logger.warning(f"Timeout DeepSeek na tentativa {tentativa}")
            if tentativa < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return f"[ERRO] Timeout DeepSeek após {MAX_RETRIES} tentativas"

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Erro DeepSeek tentativa {tentativa} ({error_type}): {str(e)}")
            if tentativa < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return f"[ERRO] Analise DeepSeek: {str(e)}"

    return "[ERRO] Desconhecido ao analisar com DeepSeek"


def tentar_gemini(
    texto_contrato: str, stream_callback: Optional[Callable[[str], None]] = None
) -> str:
    """Tenta analisar o contrato usando a API Gemini com retry automático."""
    if not GEMINI_AVAILABLE:
        return "[ERRO] google-genai não instalado"

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY não configurada")
        return "[ERRO] Chave da API Gemini não configurada"

    full_prompt = _construir_prompt(texto_contrato)
    logger.info(f"Tokens estimados (Gemini): {estimate_tokens(full_prompt)}")

    for tentativa in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Tentativa {tentativa}/{MAX_RETRIES} Gemini")
            client = genai.Client(api_key=api_key)

            if stream_callback:
                texto_completo = ""
                for chunk in client.models.generate_content_stream(
                    model=GEMINI_MODEL,
                    contents=full_prompt,
                    config={"temperature": 0.7},
                ):
                    if chunk.text:
                        texto_completo += chunk.text
                        stream_callback(chunk.text)
                logger.info("[OK] Gemini (stream)!")
                return texto_completo
            else:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=full_prompt,
                    config={"temperature": 0.7},
                )
                logger.info("[OK] Gemini!")
                return response.text

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Erro Gemini tentativa {tentativa} ({error_type}): {str(e)}")
            if "authentication" in str(e).lower():
                return "[ERRO] Autenticacao Gemini: Verifique sua chave"
            if tentativa < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return f"[ERRO] Analise Gemini: {str(e)}"

    return "[ERRO] Desconhecido Gemini"


def analisar_contrato(
    texto: str,
    stream_callback: Optional[Callable[[str], None]] = None,
    enable_fallback: Optional[bool] = None,
) -> str:
    """
    Analisa um contrato usando o modelo selecionado, com fallback automático.
    Ordem de fallback: DeepSeek -> Gemini
    """
    if not texto or not texto.strip():
        return "[ERRO] Texto do contrato vazio"

    use_fallback = enable_fallback if enable_fallback is not None else FALLBACK_ENABLED

    logger.info(f"Modelo selecionado: {SELECTED_MODEL} | Fallback: {use_fallback}")

    if SELECTED_MODEL == "deepseek":
        resultado = tentar_deepseek(texto, stream_callback)
        if resultado.startswith("[ERRO]") and use_fallback:
            logger.info("DeepSeek falhou, fallback para Gemini...")
            resultado = tentar_gemini(texto, stream_callback)
        return resultado

    elif SELECTED_MODEL == "gemini":
        resultado = tentar_gemini(texto, stream_callback)
        if resultado.startswith("[ERRO]") and use_fallback:
            logger.info("Gemini falhou, fallback para DeepSeek...")
            resultado = tentar_deepseek(texto, stream_callback)
        return resultado

    else:
        logger.error(f"Modelo desconhecido: {SELECTED_MODEL}")
        return f"[ERRO] Modelo '{SELECTED_MODEL}' nao reconhecido"


def analisar_contrato_stream(
    texto: str,
    enable_fallback: Optional[bool] = None,
) -> Generator[str, None, None]:
    """Analisa com streaming, compatível com st.write_stream()."""
    chunks = []

    def collect(chunk: str):
        chunks.append(chunk)

    resultado = analisar_contrato(texto, stream_callback=collect, enable_fallback=enable_fallback)

    if resultado.startswith("[ERRO]"):
        yield resultado
    else:
        for chunk in chunks:
            yield chunk


def responder_duvida_clausula(duvida: str, contexto_analise: str) -> str:
    """
    Usa Gemini para responder dúvidas sobre o contrato analisado.

    Args:
        duvida: Pergunta do usuário sobre o contrato
        contexto_analise: Texto da análise do contrato

    Returns:
        Resposta gerada pela IA
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Erro: Chave da API Gemini não configurada. Configure GEMINI_API_KEY no arquivo .env"

        model_name = os.getenv("GEMINI_MODEL", GEMINI_MODEL)
        client = genai.Client(api_key=api_key)

        prompt = f"""Você é um assistente jurídico especializado em análise de contratos.
Responda a seguinte dúvida do usuário baseando-se na análise fornecida.

Análise do Contrato:
{contexto_analise}

Dúvida do usuário:
{duvida}

Forneça uma resposta clara, objetiva e fundamentada baseada apenas na análise fornecida."""

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

        return response.text

    except Exception as e:
        logger.error(f"Erro ao responder dúvida: {str(e)}")
        return f"Desculpe, não consegui processar sua pergunta. Erro: {str(e)}"
