import logging
from io import BytesIO
from typing import Dict, Optional, Tuple

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

try:
    import pytesseract
    from PIL import Image

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.info("pytesseract/Pillow não instalados. OCR desabilitado.")


def _page_has_text(page) -> bool:
    """Verifica se uma página tem texto extraível diretamente."""
    text = page.get_text("text")
    return len(text.strip()) > 20


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
        texto = pytesseract.image_to_string(img, lang="por")
        return texto.strip() or ""
    except Exception as e:
        logger.warning(f"Erro ao aplicar OCR na página {page.number + 1}: {str(e)}")
        return ""


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
                has_text = _page_has_text(page)

                if has_text:
                    page_text = page.get_text("text")
                    if page_text:
                        texto += page_text + "\n"
                elif enable_ocr and OCR_AVAILABLE:
                    ocr_text = _ocr_page(page)
                    if ocr_text:
                        texto += ocr_text + "\n"
                        pages_with_ocr += 1
                        logger.info(f"OCR aplicado na página {page_num}")
                elif not has_text and enable_ocr and not OCR_AVAILABLE:
                    logger.warning(
                        f"Página {page_num} sem texto extraível e OCR indisponível"
                    )
                elif not has_text:
                    logger.info(
                        f"Página {page_num} sem texto extraível (OCR desabilitado)"
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
