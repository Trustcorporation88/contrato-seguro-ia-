import logging
import os
import re
import base64
from functools import lru_cache
from io import BytesIO
from typing import Dict, Optional, Tuple

import fitz  # PyMuPDF
import requests

logger = logging.getLogger(__name__)
_OCR_LANGUAGES = tuple(
    lang.strip()
    for lang in os.getenv("OCR_LANGUAGES", "por,por+eng,eng").split(",")
    if lang.strip()
)
_WORD_PATTERN = re.compile(r"[0-9A-Za-zÀ-ÿ]{2,}")
_OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY", "")

try:
    import pytesseract
    from PIL import Image

    _TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(_TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = _TESSERACT_PATH

    _TESSDATA_USER = os.path.join(
        os.environ.get("LOCALAPPDATA", ""), r"Tesseract-OCR\tessdata"
    )
    if os.path.isdir(_TESSDATA_USER) and os.listdir(_TESSDATA_USER):
        os.environ["TESSDATA_PREFIX"] = _TESSDATA_USER

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.info("pytesseract/Pillow não instalados. OCR desabilitado.")


@lru_cache(maxsize=1)
def get_ocr_status() -> Tuple[bool, str, Tuple[str, ...]]:
    """
    Retorna o estado real do OCR no ambiente.

    Diferente de OCR_AVAILABLE, valida também se o executável do Tesseract e os
    idiomas estão acessíveis em tempo de execução.
    """
    if not OCR_AVAILABLE:
        return False, "pytesseract/Pillow não instalados", ()

    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        return False, "executável do Tesseract não encontrado", ()
    except Exception as exc:
        return False, f"falha ao validar Tesseract: {exc}", ()

    try:
        languages = tuple(sorted(set(pytesseract.get_languages(config=""))))
    except Exception as exc:
        return False, f"falha ao listar idiomas do Tesseract: {exc}", ()

    if not languages:
        return False, "nenhum idioma OCR disponível no Tesseract", ()

    return True, "OCR disponível", languages


def _get_candidate_ocr_languages(available_languages: Tuple[str, ...]) -> Tuple[str, ...]:
    """Retorna combinações de idioma válidas para o ambiente atual."""
    valid_languages = []

    for lang in _OCR_LANGUAGES:
        lang_parts = tuple(part.strip() for part in lang.split("+") if part.strip())
        if lang_parts and all(part in available_languages for part in lang_parts):
            valid_languages.append(lang)

    if valid_languages:
        return tuple(valid_languages)

    for fallback in ("por", "eng"):
        if fallback in available_languages:
            return (fallback,)

    return available_languages[:1]


def _normalize_text(text: str) -> str:
    """Normaliza espaços para comparar qualidade do texto extraído."""
    return re.sub(r"\s+", " ", text or "").strip()


def _text_quality_score(text: str) -> float:
    """Calcula uma pontuação simples de legibilidade do texto."""
    normalized = _normalize_text(text)
    if not normalized:
        return 0.0

    words = _WORD_PATTERN.findall(normalized)
    long_words = [word for word in words if len(word) >= 4]
    alnum_chars = sum(char.isalnum() for char in normalized)

    return (
        len(normalized)
        + (len(words) * 12)
        + (len(long_words) * 8)
        + (alnum_chars * 0.5)
    )


def _page_has_usable_text(text: str) -> bool:
    """Verifica se o texto extraído da página parece aproveitável."""
    normalized = _normalize_text(text)
    if len(normalized) < 40:
        return False

    words = _WORD_PATTERN.findall(normalized)
    if len(words) < 6:
        return False

    alnum_chars = sum(char.isalnum() for char in normalized)
    alnum_ratio = alnum_chars / len(normalized)
    return alnum_ratio >= 0.45


def _ocr_page_with_api(page) -> str:
    """
    Aplica OCR em uma página usando OCR.space API como fallback.

    Args:
        page: Página do PyMuPDF

    Returns:
        Texto extraído via OCR API
    """
    if not _OCR_SPACE_API_KEY:
        logger.warning(
            f"OCR_SPACE_API_KEY não configurada - página {page.number + 1} sem OCR"
        )
        return ""

    try:
        # Renderiza página como imagem
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        # Chama API OCR.space com multipart/form-data
        url = "https://api.ocr.space/parse/image"
        payload = {
            "apikey": _OCR_SPACE_API_KEY,
            "language": "por",
            "isOverlayRequired": "false",
            "base64Image": f"data:image/png;base64,{img_base64}",
        }

        # Usa data (form-encoded) ao invés de json
        response = requests.post(url, data=payload, timeout=60)
        
        # Log detalhado da resposta para debug
        logger.info(f"OCR.space response status: {response.status_code}")
        
        response.raise_for_status()
        result = response.json()
        
        # Log completo da resposta para diagnóstico
        logger.info(f"OCR.space response: IsErrored={result.get('IsErroredOnProcessing')}, "
                   f"OCRExitCode={result.get('OCRExitCode')}, "
                   f"ProcessingTime={result.get('ProcessingTimeInMilliseconds')}ms")

        if result.get("IsErroredOnProcessing"):
            error_msg = result.get("ErrorMessage", ["Erro desconhecido"])
            if isinstance(error_msg, list):
                error_msg = error_msg[0] if error_msg else "Erro desconhecido"
            logger.error(
                f"OCR.space erro na página {page.number + 1}: {error_msg}"
            )
            return ""

        parsed_results = result.get("ParsedResults", [])
        if not parsed_results:
            logger.warning(f"OCR.space sem resultado para página {page.number + 1}")
            logger.warning(f"Response completa: {result}")
            return ""

        text = parsed_results[0].get("ParsedText", "").strip()
        logger.info(
            f"OCR.space sucesso na página {page.number + 1}: "
            f"{len(text)} caracteres extraídos"
        )
        return text

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de rede ao chamar OCR.space na página {page.number + 1}: {str(e)}")
        return ""
    except Exception as e:
        logger.error(f"Erro ao aplicar OCR API na página {page.number + 1}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return ""


def _ocr_page(page) -> str:
    """
    Aplica OCR em uma página usando pytesseract (local) ou OCR.space API (fallback).

    Args:
        page: Página do PyMuPDF

    Returns:
        Texto extraído via OCR
    """
    ocr_ready, ocr_reason, available_languages = get_ocr_status()
    
    # Tenta Tesseract local primeiro (mais rápido e privado)
    if ocr_ready:
        try:
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            best_text = ""
            best_lang = None

            for lang in _get_candidate_ocr_languages(available_languages):
                try:
                    texto = pytesseract.image_to_string(img, lang=lang).strip()
                except pytesseract.TesseractError as lang_error:
                    logger.warning(
                        f"OCR falhou na página {page.number + 1} com idioma '{lang}': {str(lang_error)}"
                    )
                    continue

                if _text_quality_score(texto) > _text_quality_score(best_text):
                    best_text = texto
                    best_lang = lang

            if best_text and best_lang:
                logger.info(
                    f"Tesseract OCR selecionou idioma '{best_lang}' para a página {page.number + 1}"
                )
                return best_text

        except Exception as e:
            logger.warning(f"Erro ao aplicar Tesseract OCR na página {page.number + 1}: {str(e)}")
    
    # Fallback para API externa se Tesseract não disponível ou falhou
    logger.info(
        f"Tesseract indisponível ({ocr_reason}), tentando OCR.space API para página {page.number + 1}"
    )
    return _ocr_page_with_api(page)


def _extract_page_text(page, enable_ocr: bool) -> Tuple[str, bool]:
    """
    Extrai o melhor texto possível da página.

    PDFs escaneados às vezes possuem uma camada de texto ruim o bastante para
    impedir a análise, então o OCR é tentado quando a extração direta parece
    pouco aproveitável.
    """
    direct_text = page.get_text("text").strip()
    direct_score = _text_quality_score(direct_text)
    direct_usable = _page_has_usable_text(direct_text)

    if direct_usable or not enable_ocr or not OCR_AVAILABLE:
        return direct_text, False

    ocr_text = _ocr_page(page)
    ocr_score = _text_quality_score(ocr_text)

    if ocr_score > direct_score:
        logger.info(
            f"Página {page.number + 1}: OCR substituiu texto direto "
            f"(score direto={direct_score:.1f}, OCR={ocr_score:.1f})"
        )
        return ocr_text, True

    if direct_text:
        logger.info(
            f"Página {page.number + 1}: mantendo texto direto apesar do OCR "
            f"(score direto={direct_score:.1f}, OCR={ocr_score:.1f})"
        )

    return direct_text, False


def extrair_texto_pdf_bytes(
    pdf_bytes: BytesIO, enable_ocr: bool = True
) -> str:
    """
    Extrai texto de um arquivo PDF em memória usando BytesIO.
    Suporta OCR automático para páginas escaneadas.

    Args:
        pdf_bytes: Objeto BytesIO contendo os dados do PDF
        enable_ocr: Se True, aplica OCR em páginas sem texto extraível

    Returns:
        Texto extraído do PDF

    Raises:
        Exception: Se o PDF estiver corrompido ou inválido
    """
    try:
        pdf_bytes.seek(0)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        if not doc or doc.page_count == 0:
            raise ValueError("PDF não contém páginas ou está vazio")

        texto = ""
        pages_with_ocr = 0

        for page_num, page in enumerate(doc, 1):
            try:
                page_text, used_ocr = _extract_page_text(page, enable_ocr=enable_ocr)

                if page_text:
                    texto += page_text + "\n"

                if used_ocr:
                    pages_with_ocr += 1
                    logger.info(f"OCR aplicado na página {page_num}")
                elif not page_text and enable_ocr and not OCR_AVAILABLE:
                    logger.warning(
                        f"Página {page_num} sem texto extraível e OCR indisponível"
                    )
                elif not page_text and enable_ocr:
                    logger.warning(
                        f"Página {page_num} sem texto aproveitável mesmo após OCR"
                    )
                elif not page_text:
                    logger.info(
                        f"Página {page_num} sem texto aproveitável (OCR desabilitado)"
                    )
            except Exception as page_error:
                logger.warning(
                    f"Aviso ao processar página {page_num}: {str(page_error)}"
                )
                continue

        doc.close()

        if pages_with_ocr > 0:
            logger.info(f"OCR aplicado em {pages_with_ocr} página(s)")

        texto_final = texto.strip()

        if not texto_final and enable_ocr:
            ocr_ready, ocr_reason, available_languages = get_ocr_status()
            if not ocr_ready and not _OCR_SPACE_API_KEY:
                raise Exception(
                    f"OCR indisponível para PDF escaneado: {ocr_reason}. "
                    "Configure OCR_SPACE_API_KEY para usar OCR via API."
                )
            if ocr_ready:
                raise Exception(
                    "Nenhum texto foi extraído do PDF. O arquivo parece escaneado, "
                    f"mas o OCR não conseguiu reconhecer conteúdo legível. "
                    f"Idiomas disponíveis: {', '.join(available_languages)}"
                )
            raise Exception(
                "Nenhum texto foi extraído do PDF. O arquivo parece escaneado, "
                "mas o OCR via API não conseguiu reconhecer conteúdo legível."
            )

        return texto_final

    except (fitz.FileDataError, fitz.EmptyFileError, ValueError) as e:
        logger.error(f"Erro ao abrir PDF: {str(e)}")
        raise Exception(f"PDF corrompido ou inválido: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF: {str(e)}")
        raise Exception(f"Erro ao processar PDF: {str(e)}")


def extrair_texto_pdf(caminho_pdf: str, enable_ocr: bool = True) -> str:
    """
    Extrai texto de um arquivo PDF no disco (compatibilidade com código antigo).

    Args:
        caminho_pdf: Caminho do arquivo PDF
        enable_ocr: Se True, aplica OCR em páginas escaneadas

    Returns:
        Texto extraído do PDF

    Raises:
        Exception: Se o PDF estiver corrompido ou inválido
    """
    try:
        with open(caminho_pdf, "rb") as f:
            return extrair_texto_pdf_bytes(BytesIO(f.read()), enable_ocr=enable_ocr)
    except FileNotFoundError:
        raise Exception(f"Arquivo PDF não encontrado: {caminho_pdf}")
    except Exception as e:
        raise Exception(f"Erro ao extrair texto do PDF: {str(e)}")


def extrair_metadados_pdf(pdf_bytes: BytesIO) -> Dict[str, str]:
    """
    Extrai metadados de um PDF.

    Args:
        pdf_bytes: Objeto BytesIO contendo os dados do PDF

    Returns:
        Dicionário com metadados (título, autor, assunto, data de criação, etc.)
    """
    try:
        pdf_bytes.seek(0)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        metadata = doc.metadata or {}
        page_count = doc.page_count
        doc.close()

        return {
            "titulo": metadata.get("title", "N/A"),
            "autor": metadata.get("author", "N/A"),
            "assunto": metadata.get("subject", "N/A"),
            "criador": metadata.get("creator", "N/A"),
            "data_criacao": metadata.get("creationDate", "N/A"),
            "data_modificacao": metadata.get("modDate", "N/A"),
            "total_paginas": str(page_count),
            "formato": metadata.get("format", "PDF"),
        }
    except Exception as e:
        logger.warning(f"Erro ao extrair metadados: {str(e)}")
        return {}
