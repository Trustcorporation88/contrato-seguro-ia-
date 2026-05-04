"""
clause_service.py - Serviço de Sugestão de Cláusulas Alternativas

Identifica cláusulas problemáticas na análise e gera redações alternativas
usando IA, com biblioteca de cláusulas-padrão por tipo de contrato.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

CLAUSULAS_PADRAO = {
    "multa_rescisoria": """
CLÁUSULA X - MULTA RESCISÓRIA
Em caso de rescisão contratual por qualquer das partes, a parte que der causa 
à rescisão pagará à outra multa compensatória de 10% (dez por cento) sobre o 
valor total do contrato, desde que comprovado o prejuízo, nos termos do art. 408 
do Código Civil Brasileiro.
""",
    "foro_eleicao": """
CLÁUSULA X - FORO DE ELEIÇÃO
Fica eleito o foro da comarca do domicílio do contratante para dirimir quaisquer 
questões oriundas deste contrato, em detrimento de qualquer outro, por mais 
privilegiado que seja.
""",
    "confidencialidade": """
CLÁUSULA X - CONFIDENCIALIDADE
As partes se comprometem a manter absoluto sigilo sobre todas as informações 
trocadas durante a vigência deste contrato, inclusive após seu término, pelo 
prazo mínimo de 5 (cinco) anos, sob pena de indenização por perdas e danos.
""",
    "lgpd": """
CLÁUSULA X - PROTEÇÃO DE DADOS (LGPD)
As partes declaram estar em conformidade com a Lei nº 13.709/2018 (LGPD), 
comprometendo-se a tratar os dados pessoais apenas para os fins estritamente 
necessários à execução deste contrato, observando os princípios da finalidade, 
adequação e necessidade.
""",
    "reajuste": """
CLÁUSULA X - REAJUSTE DE VALORES
Os valores previstos neste contrato serão reajustados anualmente com base no 
IPCA (Índice de Preços ao Consumidor Amplo), ou, na sua falta, pelo índice que 
vier a substituí-lo.
""",
}


def sugerir_clausula_alternativa(
    clausula_original: str,
    tipo_problema: str,
    base_legal: str,
    tipo_contrato: str = "geral",
) -> Tuple[bool, str]:
    """
    Gera sugestão de redação alternativa para uma cláusula problemática.

    Args:
        clausula_original: Texto original da cláusula
        tipo_problema: Descrição do problema identificado
        base_legal: Fundamentação legal do problema
        tipo_contrato: Tipo de contrato para contextualizar

    Returns:
        Tuple (sucesso, clausula_sugerida)
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return False, "Erro: GEMINI_API_KEY não configurada"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)

        prompt = f"""Você é um especialista em Direito Contratual brasileiro.

CONTEXTO:
- Tipo de contrato: {tipo_contrato}
- Cláusula original problemática:
{clausula_original}

- Problema identificado:
{tipo_problema}

- Base legal:
{base_legal}

TAREFA:
Reescreva a cláusula acima de forma equilibrada e juridicamente segura, 
respeitando o Código Civil Brasileiro, o CDC (quando aplicável) e a LGPD 
(quando aplicável).

FORMATO DA RESPOSTA:
1. Redação sugerida (texto completo da cláusula revisada)
2. Principais mudanças (2-3 bullet points)
3. Por que esta versão é mais equilibrada (1 parágrafo curto)

Seja direto, objetivo e técnico. Use linguagem jurídica adequada."""

        response = model.generate_content(
            prompt,
            request_options={"timeout": 60},
            generation_config={"temperature": 0.5},
        )

        return True, response.text

    except Exception as e:
        logger.error(f"Erro ao gerar sugestão: {e}")
        return False, f"Erro ao gerar sugestão: {str(e)}"


def extrair_clausulas_risco(analise_texto: str) -> List[Dict[str, str]]:
    """
    Extrai as cláusulas de risco da análise e as estrutura.

    Args:
        analise_texto: Texto completo da análise

    Returns:
        Lista de cláusulas com tipo, problema e base legal
    """
    import re

    clausulas = []

    bloco_pattern = re.compile(
        r"\*\*[🔴🟠🟢]\s*RISCO\s*(ALTO|M[ÉE]DIO|BAIXO)\*\*",
        re.IGNORECASE,
    )

    matches = list(bloco_pattern.finditer(analise_texto))

    for i, match in enumerate(matches):
        nivel_str = match.group(1).upper()
        if "ALTO" in nivel_str:
            nivel = "alto"
        elif "MÉDIO" in nivel_str or "MEDIO" in nivel_str:
            nivel = "medio"
        elif "BAIXO" in nivel_str:
            nivel = "baixo"
        else:
            nivel = ""

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(analise_texto)
        bloco = analise_texto[start:end]

        clausula = {"nivel": nivel, "texto_clausula": "", "problema": "", "base_legal": ""}

        clausula_match = re.search(
            r"Cl[aá]usula\S*\s*:?\s*(.+?)(?:\n|$)",
            bloco,
            re.IGNORECASE,
        )
        if clausula_match:
            clausula["texto_clausula"] = clausula_match.group(1).strip()

        problema_match = re.search(
            r"Problema\S*\s*:?\s*(.+?)(?:\n\*\*|\n$|\Z)",
            bloco,
            re.IGNORECASE | re.DOTALL,
        )
        if problema_match:
            clausula["problema"] = problema_match.group(1).strip()

        base_match = re.search(
            r"Base\s*[Ll]egal\S*\s*:?\s*(.+?)(?:\n\*\*|\n$|\Z)",
            bloco,
            re.IGNORECASE | re.DOTALL,
        )
        if base_match:
            clausula["base_legal"] = base_match.group(1).strip()

        if clausula["texto_clausula"] or clausula["problema"]:
            clausulas.append(clausula)

    return clausulas


def get_clausula_padrao(tipo: str) -> Optional[str]:
    """
    Retorna uma cláusula padrão da biblioteca, se disponível.

    Args:
        tipo: Tipo de cláusula (multa_rescisoria, foro_eleicao, etc.)

    Returns:
        Texto da cláusula padrão ou None
    """
    return CLAUSULAS_PADRAO.get(tipo)


def listar_tipos_clausulas() -> List[str]:
    """Lista os tipos de cláusulas disponíveis na biblioteca."""
    return list(CLAUSULAS_PADRAO.keys())


def comparar_clausulas(
    original: str, sugestao: str
) -> Dict[str, str]:
    """
    Compara cláusula original com a sugestão, destacando diferenças.

    Returns:
        Dict com 'original', 'sugestao' e 'diferencas'
    """
    import difflib

    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        sugestao.splitlines(keepends=True),
        fromfile="Original",
        tofile="Sugestão",
    )

    return {
        "original": original,
        "sugestao": sugestao,
        "diferencas": "".join(diff),
    }


if __name__ == "__main__":
    print("=== Teste do ClauseService ===\n")

    print("1. Extraindo cláusulas de uma análise simulada...")
    analise_teste = """
## Análise de Riscos

**🔴 RISCO ALTO**
**Cláusula:** 5.2 - Multa Contratual
**Problema:** Multa de 50% sobre o valor do contrato, excessiva
**Base legal:** Art. 412 CC - A multa não pode exceder o valor da obrigação principal

**🟠 RISCO MÉDIO**
**Cláusula:** 8.1 - Foro de Eleição
**Problema:** Foro eleito em comarca distante do domicílio do contratante
**Base legal:** Art. 421 CC - Função social do contrato
"""
    clausulas = extrair_clausulas_risco(analise_teste)
    for c in clausulas:
        print(f"  [{c['nivel'].upper()}] {c['texto_clausula']}")
        print(f"    Problema: {c['problema'][:60]}...")

    print("\n2. Biblioteca de cláusulas padrão:")
    for tipo in listar_tipos_clausulas():
        print(f"  - {tipo}")

    print("\n3. Cláusula padrão (multa_rescisoria):")
    print(get_clausula_padrao("multa_rescisoria")[:200] + "...")
