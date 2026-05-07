"""
Testes para o módulo pdf_extractor.py.
"""
from io import BytesIO
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pdf_extractor


class _FakePage:
    def __init__(self, text: str, number: int = 0):
        self._text = text
        self.number = number

    def get_text(self, mode: str) -> str:
        assert mode == "text"
        return self._text


def test_page_has_usable_text_with_contract_content():
    """Texto jurídico normal deve ser tratado como utilizável."""
    texto = (
        "Cláusula 1 - O contratante pagará o valor mensal até o quinto dia útil, "
        "sob pena de multa e juros conforme previsto neste instrumento."
    )
    assert pdf_extractor._page_has_usable_text(texto) is True


def test_extract_page_text_prefers_ocr_when_direct_text_is_poor():
    """OCR deve substituir camada de texto ruim de PDF escaneado."""
    page = _FakePage("a i / 1\nx z\n::\n", number=0)
    original_ocr_available = pdf_extractor.OCR_AVAILABLE
    original_ocr_page = pdf_extractor._ocr_page

    try:
        pdf_extractor.OCR_AVAILABLE = True
        pdf_extractor._ocr_page = lambda current_page: (
            "CONTRATO DE PRESTAÇÃO DE SERVIÇOS ENTRE AS PARTES, "
            "COM PRAZO DE 12 MESES E MULTA POR INADIMPLEMENTO."
        )
        texto, used_ocr = pdf_extractor._extract_page_text(page, enable_ocr=True)
    finally:
        pdf_extractor.OCR_AVAILABLE = original_ocr_available
        pdf_extractor._ocr_page = original_ocr_page

    assert used_ocr is True
    assert "PRESTAÇÃO DE SERVIÇOS" in texto


def test_extract_page_text_keeps_direct_text_when_it_is_good():
    """PDF nativo deve manter a extração direta sem forçar OCR."""
    texto_direto = (
        "Cláusula 5 - O foro eleito para resolução de controvérsias "
        "será o da comarca de São Paulo."
    )
    page = _FakePage(texto_direto, number=1)
    original_ocr_available = pdf_extractor.OCR_AVAILABLE
    original_ocr_page = pdf_extractor._ocr_page

    try:
        pdf_extractor.OCR_AVAILABLE = True
        pdf_extractor._ocr_page = lambda current_page: "texto pior"
        texto, used_ocr = pdf_extractor._extract_page_text(page, enable_ocr=True)
    finally:
        pdf_extractor.OCR_AVAILABLE = original_ocr_available
        pdf_extractor._ocr_page = original_ocr_page

    assert used_ocr is False
    assert texto == texto_direto


def test_get_candidate_ocr_languages_prefers_supported_configurations():
    """Deve selecionar apenas combinações de idioma suportadas pelo ambiente."""
    idiomas = pdf_extractor._get_candidate_ocr_languages(("eng", "por"))
    assert idiomas[0] == "por"
    assert "por+eng" in idiomas


def test_get_candidate_ocr_languages_falls_back_when_config_is_unavailable():
    """Deve cair para idioma disponível quando combinações configuradas não existem."""
    idiomas = pdf_extractor._get_candidate_ocr_languages(("eng",))
    assert idiomas == ("eng",)


def test_extrair_texto_pdf_bytes_handles_invalid_pdf_error():
    """Deve converter erro de PDF inválido sem depender de exceção inexistente."""
    original_open = pdf_extractor.fitz.open

    def _raise_file_data_error(*args, **kwargs):
        raise pdf_extractor.fitz.FileDataError("arquivo invalido")

    try:
        pdf_extractor.fitz.open = _raise_file_data_error
        try:
            pdf_extractor.extrair_texto_pdf_bytes(BytesIO(b"nao-e-pdf"), enable_ocr=True)
            assert False, "Era esperado erro para PDF inválido"
        except Exception as exc:
            assert "PDF corrompido ou inválido" in str(exc)
    finally:
        pdf_extractor.fitz.open = original_open


if __name__ == "__main__":
    test_page_has_usable_text_with_contract_content()
    test_extract_page_text_prefers_ocr_when_direct_text_is_poor()
    test_extract_page_text_keeps_direct_text_when_it_is_good()
    test_get_candidate_ocr_languages_prefers_supported_configurations()
    test_get_candidate_ocr_languages_falls_back_when_config_is_unavailable()
    test_extrair_texto_pdf_bytes_handles_invalid_pdf_error()
    print("Todos os testes de pdf_extractor.py passaram!")
