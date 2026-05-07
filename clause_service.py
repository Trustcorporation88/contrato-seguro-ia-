"""
clause_service.py - Serviço de Sugestão de Cláusulas Alternativas

Identifica cláusulas problemáticas na análise e gera redações alternativas
usando IA, com biblioteca de cláusulas-padrão por tipo de contrato.
"""

import logging
import os
import re as _re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from google import genai

    GEMINI_AVAILABLE = True
except Exception as import_error:
    GEMINI_AVAILABLE = False
    logger.warning(f"google-genai indisponivel em clause_service. Motivo: {import_error}")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

RISCO_BLOCO_PATTERN = _re.compile(
    r"\*\*[🔴🟠🟢]\s*RISCO\s*(ALTO|M[ÉE]DIO|BAIXO)\*\*",
    _re.IGNORECASE,
)

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
    if not GEMINI_AVAILABLE:
        return False, "Erro: google-genai não está disponível no ambiente"

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return False, "Erro: GEMINI_API_KEY não configurada"

    try:
        client = genai.Client(api_key=api_key)

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

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={"temperature": 0.5},
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
    clausulas = []

    matches = list(RISCO_BLOCO_PATTERN.finditer(analise_texto))

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

        clausula_match = _re.search(
            r"Cl[aá]usula\S*\s*:?\s*(.+?)(?:\n|$)",
            bloco,
            _re.IGNORECASE,
        )
        if clausula_match:
            clausula["texto_clausula"] = clausula_match.group(1).strip()

        problema_match = _re.search(
            r"Problema\S*\s*:?\s*(.+?)(?:\n\*\*|\n$|\Z)",
            bloco,
            _re.IGNORECASE | _re.DOTALL,
        )
        if problema_match:
            clausula["problema"] = problema_match.group(1).strip()

        base_match = _re.search(
            r"Base\s*[Ll]egal\S*\s*:?\s*(.+?)(?:\n\*\*|\n$|\Z)",
            bloco,
            _re.IGNORECASE | _re.DOTALL,
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


def extrair_numeros_riscos(analise_texto: str) -> Dict[str, int]:
    """
    Extrai estatísticas de riscos do texto da análise.

    Args:
        analise_texto: Texto da análise contendo os riscos

    Returns:
        Dicionário com contagem de riscos por nível
    """
    riscos_altos = len(_re.findall(r"🔴\s*RISCO\s*ALTO", analise_texto, _re.IGNORECASE))
    riscos_medios = len(_re.findall(r"🟠\s*RISCO\s*M[ÉE]DIO", analise_texto, _re.IGNORECASE))
    riscos_baixos = len(_re.findall(r"🟢\s*RISCO\s*BAIXO|🟢\s*BAIXO", analise_texto, _re.IGNORECASE))

    return {
        "altos": riscos_altos,
        "medios": riscos_medios,
        "baixos": riscos_baixos,
        "total": riscos_altos + riscos_medios + riscos_baixos,
    }


def extrair_pontos_atencao(analise_texto: str, max_linhas: int = 20) -> str:
    """
    Extrai um resumo executivo conciso com os pontos de atenção/riscos.
    Para cada risco identificado, extrai APENAS cláusula + problema (1 linha),
    ignorando base legal e sugestão para manter o resumo enxuto.

    Args:
        analise_texto: Texto completo da análise
        max_linhas: Número máximo de linhas para retornar

    Returns:
        Resumo executivo conciso (máx. 20 linhas)
    """
    pontos = []

    matches = list(RISCO_BLOCO_PATTERN.finditer(analise_texto))

    if matches:
        for i, match in enumerate(matches):
            nivel = match.group(1).upper()
            emoji = "🔴" if "ALTO" in nivel else ("🟠" if "MÉDIO" in nivel or "MEDIO" in nivel else "🟢")

            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else min(len(analise_texto), start + 2000)
            bloco = analise_texto[start:end]

            clausula_match = _re.search(
                r"Cl[aá]usula\S*\s*:?\s*(.+?)(?:\n|$)", bloco, _re.IGNORECASE
            )
            problema_match = _re.search(
                r"Problema\S*\s*:?\s*(.+?)(?:\.(?:\s|$))", bloco, _re.IGNORECASE | _re.DOTALL
            )

            clausula_texto = clausula_match.group(1).strip() if clausula_match else ""
            problema_texto = problema_match.group(1).strip() if problema_match else ""

            primeira_linha_problema = problema_texto.split(".")[0].strip() if problema_texto else ""

            if clausula_texto and primeira_linha_problema:
                pontos.append(f"{emoji} **{clausula_texto}**: {primeira_linha_problema[:140]}.")
            elif clausula_texto:
                pontos.append(f"{emoji} **{clausula_texto}**")
            elif primeira_linha_problema:
                pontos.append(f"{emoji} {primeira_linha_problema[:160]}.")

            if len(pontos) >= max_linhas:
                break

    if not pontos:
        linhas = analise_texto.split("\n")
        em_resumo = False
        for linha in linhas:
            if "resumo fiel" in linha.lower() or "resumo executivo" in linha.lower():
                em_resumo = True
                continue
            if em_resumo and (
                "tópicos" in linha.lower()
                or "análise de riscos" in linha.lower()
                or linha.startswith("##")
                or linha.startswith("###")
            ):
                em_resumo = False
                continue
            if em_resumo and linha.strip():
                clean = linha.strip()
                if any(clean.startswith(p) for p in ["- ", "• ", "* "]):
                    pontos.append(clean)
                elif clean and not clean.startswith("#"):
                    pontos.append(clean)
                if len(pontos) >= max_linhas:
                    break

    resumo = "\n".join(pontos[:max_linhas])

    if len(pontos) > max_linhas:
        resumo += f"\n\n... (mais {len(pontos) - max_linhas} pontos na análise completa)"

    return resumo if resumo else "Nenhum ponto crítico identificado."


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
