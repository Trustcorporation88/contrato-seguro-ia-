import logging
import os
import re
from io import BytesIO
from typing import Dict, Optional, Tuple

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)
_OCR_LANGUAGES = tuple(
    lang.strip()
    for lang in os.getenv("OCR_LANGUAGES", "por,por+eng,eng").split(",")
    if lang.strip()
)
_WORD_PATTERN = re.compile(r"[0-9A-Za-zÀ-ÿ]{2,}")

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


def _ocr_page(page) -> str:
    """
    Aplica OCR em uma página usando pytesseract.

    Args:
        page: Página do PyMuPDF

    Returns:
        Texto extraído via OCR
    """
    if not OCR_AVAILABLE:
        return ""

    try:
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        best_text = ""
        best_lang = None

        for lang in _OCR_LANGUAGES:
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
                f"OCR selecionou idioma '{best_lang}' para a página {page.number + 1}"
            )

        return best_text
    except Exception as e:
        logger.warning(f"Erro ao aplicar OCR na página {page.number + 1}: {str(e)}")
        return ""


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

        return texto.strip()

    except fitz.FileError as e:
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
