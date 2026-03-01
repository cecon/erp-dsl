"""Skill: classify_ncm — suggest NCM codes by product description.

Three strategies executed in order:
1. **Web search** — DuckDuckGo search, extract 8-digit NCM patterns, validate
   against the local ``ncm`` table.  Flag ``source: 'web'``.
2. **Local search** — ILIKE text search + keyword mapping + prefix matching +
   relaxed single-term.  Flag ``source: 'local'``.
3. **Fallback** — returns ``needs_user_input: true`` so the orchestrator can
   ask the user.

Contract: async def classify_ncm(params: dict, context: dict) -> dict
"""

from __future__ import annotations

import logging
import re

from sqlalchemy import or_, select

from src.application.agent import skill_registry
from src.infrastructure.persistence.sqlalchemy.models import Base

logger = logging.getLogger(__name__)

_MAX_RESULTS = 5

# ── NCM 8-digit extraction patterns ────────────────────────────────
_NCM_8_DOT = re.compile(r"\b(\d{4}\.\d{2}\.\d{2})\b")
_NCM_8_RAW = re.compile(r"\b(\d{8})\b")

# ── Keyword → NCM prefix mapping ────────────────────────────────────
# Common retail product terms mapped to their likely NCM 4-digit prefixes.
# This bridges the gap between consumer language and TIPI nomenclature.
_KEYWORD_NCM_MAP: dict[str, list[str]] = {
    # Beverages
    "refrigerante": ["2202"],
    "coca": ["2202"],
    "pepsi": ["2202"],
    "fanta": ["2202"],
    "guarana": ["2202"],
    "guaraná": ["2202"],
    "sprite": ["2202"],
    "suco": ["2202", "2009"],
    "energetico": ["2202"],
    "energético": ["2202"],
    "agua": ["2201"],
    "água": ["2201"],
    "cerveja": ["2203"],
    "vinho": ["2204"],
    "whisky": ["2208"],
    "uísque": ["2208"],
    "vodca": ["2208"],
    "vodka": ["2208"],
    "rum": ["2208"],
    "gin": ["2208"],
    "licor": ["2208"],
    "cachaça": ["2208"],
    "cachaca": ["2208"],
    "destilado": ["2208"],
    # Dairy
    "leite": ["0401", "0402"],
    "iogurte": ["0403"],
    "queijo": ["0406"],
    "requeijão": ["0406"],
    "requeijao": ["0406"],
    "manteiga": ["0405"],
    # Meat
    "carne": ["0201", "0202", "0207"],
    "frango": ["0207"],
    "peixe": ["0302", "0303"],
    "presunto": ["0210"],
    "bacon": ["0210"],
    "linguiça": ["0210", "1601"],
    "linguica": ["0210", "1601"],
    "salsicha": ["1601"],
    # Grains & Bakery
    "macarrao": ["1902"],
    "macarrão": ["1902"],
    "massa": ["1902"],
    "pao": ["1905"],
    "pão": ["1905"],
    "biscoito": ["1905"],
    "bolacha": ["1905"],
    "bolo": ["1905"],
    "cereal": ["1904"],
    "arroz": ["1006"],
    "feijao": ["0713"],
    "feijão": ["0713"],
    # Hygiene
    "shampoo": ["3305"],
    "xampu": ["3305"],
    "condicionador": ["3305"],
    "creme dental": ["3306"],
    "pasta de dente": ["3306"],
    "desodorante": ["3307"],
    "sabonete": ["3401"],
    "perfume": ["3303"],
    # Cleaning
    "detergente": ["3402"],
    "sabão": ["3402"],
    "sabao": ["3402"],
    "amaciante": ["3402"],
    "inseticida": ["3808"],
    "desinfetante": ["3402", "3808"],
    # Electronics
    "notebook": ["8471"],
    "computador": ["8471"],
    "laptop": ["8471"],
    "celular": ["8517"],
    "smartphone": ["8517"],
    "telefone": ["8517"],
    "iphone": ["8517"],
    "samsung": ["8517"],
    # Clothing
    "camiseta": ["6109", "6110"],
    "camisa": ["6105"],
    "calça": ["6103", "6104"],
    "calca": ["6103", "6104"],
    "vestido": ["6104"],
    "bermuda": ["6103", "6104"],
    "short": ["6103", "6104"],
    # Footwear
    "tênis": ["6404"],
    "tenis": ["6404"],
    "sapato": ["6403"],
    "sandália": ["6402"],
    "sandalia": ["6402"],
    "bota": ["6403"],
    "chinelo": ["6402"],
    # Tobacco
    "cigarro": ["2402"],
    "tabaco": ["2401", "2402"],
    # Fuel
    "gasolina": ["2710"],
    "diesel": ["2710"],
    "etanol": ["2207"],
    "combustível": ["2710"],
    "combustivel": ["2710"],
    # Cola / soft drink brands
    "cola": ["2202"],
    "lata": ["2202"],  # "lata" most commonly refers to canned beverages
}


# ── Helpers ──────────────────────────────────────────────────────────

def _extract_ncm_codes_from_text(text: str) -> list[str]:
    """Extract 8-digit NCM codes from text (dotted or raw format).

    Returns deduplicated codes normalised to raw 8-digit strings.
    """
    codes: list[str] = []
    # Dotted format: 2202.10.00
    for m in _NCM_8_DOT.findall(text):
        raw = m.replace(".", "")
        if raw not in codes:
            codes.append(raw)
    # Raw 8-digit format: 22021000
    for m in _NCM_8_RAW.findall(text):
        if m not in codes:
            codes.append(m)
    return codes


def _extract_ncm_prefixes(text: str) -> list[str]:
    """Extract potential 4-digit NCM prefixes from text."""
    candidates = re.findall(r"\b(\d{4,8})\b", text)
    return list(dict.fromkeys(c[:4] for c in candidates))[:5]


def _keywords_to_prefixes(terms: list[str]) -> list[str]:
    """Map product keywords to NCM prefixes using the synonym table."""
    prefixes: list[str] = []
    for term in terms:
        lower = term.lower()
        if lower in _KEYWORD_NCM_MAP:
            for p in _KEYWORD_NCM_MAP[lower]:
                if p not in prefixes:
                    prefixes.append(p)
    return prefixes[:6]


def _rows_to_candidates(rows, source: str) -> dict:
    """Convert SQLAlchemy row mappings to the standard return dict."""
    return {
        "candidates": [
            {
                "codigo": row["codigo"],
                "descricao": row["descricao"],
                "sujeito_is": bool(row["sujeito_is"]),
                "source": source,
            }
            for row in rows
        ]
    }


# ── Strategy 1: Web search ──────────────────────────────────────────

async def _strategy_web(descricao: str, db, ncm_table) -> dict | None:
    """Search the web for NCM codes and validate against the local table.

    Returns a result dict if valid NCM codes are found, else ``None``.
    """
    from src.application.agent.skills.web_search import web_search as _web_search_fn

    query = f"NCM {descricao} Brasil"
    try:
        web_result = await _web_search_fn({"query": query, "max_results": 5}, {})
    except Exception as exc:
        logger.warning("classify_ncm web search failed: %s", exc)
        return None

    results = web_result.get("results", [])
    if not results:
        return None

    # Aggregate all text from the web results
    all_text = " ".join(
        f"{r.get('title', '')} {r.get('snippet', '')}" for r in results
    )

    # Extract 8-digit NCM codes
    ncm_codes = _extract_ncm_codes_from_text(all_text)
    if not ncm_codes:
        return None

    # Validate each candidate against the local NCM table
    conditions = [ncm_table.c.codigo == code for code in ncm_codes]
    stmt = (
        select(
            ncm_table.c.codigo,
            ncm_table.c.descricao,
            ncm_table.c.sujeito_is,
        )
        .where(or_(*conditions))
        .limit(_MAX_RESULTS)
    )
    rows = db.execute(stmt).mappings().all()
    if rows:
        return _rows_to_candidates(rows, "web")

    # If exact codes not found, try prefix matching (first 4 digits)
    prefixes = list(dict.fromkeys(c[:4] for c in ncm_codes))[:5]
    if prefixes:
        prefix_conditions = [ncm_table.c.codigo.startswith(p) for p in prefixes]
        stmt_prefix = (
            select(
                ncm_table.c.codigo,
                ncm_table.c.descricao,
                ncm_table.c.sujeito_is,
            )
            .where(or_(*prefix_conditions))
            .limit(_MAX_RESULTS)
        )
        rows = db.execute(stmt_prefix).mappings().all()
        if rows:
            return _rows_to_candidates(rows, "web")

    return None


# ── Strategy 2: Local search ────────────────────────────────────────

async def _strategy_local(descricao: str, db, ncm_table) -> dict | None:
    """Search the local NCM table using ILIKE, keyword mapping, prefix and relaxed.

    Returns a result dict if matches are found, else ``None``.
    """
    terms = descricao.split()
    meaningful = [t for t in terms if len(t) >= 3]

    # Sub-strategy 2a: ILIKE multi-term
    if meaningful:
        stmt = select(
            ncm_table.c.codigo,
            ncm_table.c.descricao,
            ncm_table.c.sujeito_is,
        )
        for term in meaningful:
            stmt = stmt.where(ncm_table.c.descricao.ilike(f"%{term}%"))
        rows = db.execute(stmt.limit(_MAX_RESULTS)).mappings().all()
        if rows:
            return _rows_to_candidates(rows, "local")

    # Sub-strategy 2b: Keyword → NCM prefix mapping
    prefixes = _keywords_to_prefixes(terms)
    if prefixes:
        conditions = [ncm_table.c.codigo.startswith(p) for p in prefixes]
        stmt2 = (
            select(
                ncm_table.c.codigo,
                ncm_table.c.descricao,
                ncm_table.c.sujeito_is,
            )
            .where(or_(*conditions))
            .limit(_MAX_RESULTS)
        )
        rows = db.execute(stmt2).mappings().all()
        if rows:
            return _rows_to_candidates(rows, "local")

    # Sub-strategy 2c: Extract NCM codes from text
    num_prefixes = _extract_ncm_prefixes(descricao)
    if num_prefixes:
        conditions = [ncm_table.c.codigo.startswith(p) for p in num_prefixes]
        stmt3 = (
            select(
                ncm_table.c.codigo,
                ncm_table.c.descricao,
                ncm_table.c.sujeito_is,
            )
            .where(or_(*conditions))
            .limit(_MAX_RESULTS)
        )
        rows = db.execute(stmt3).mappings().all()
        if rows:
            return _rows_to_candidates(rows, "local")

    # Sub-strategy 2d: Relaxed single-term ILIKE
    for term in meaningful:
        stmt4 = (
            select(
                ncm_table.c.codigo,
                ncm_table.c.descricao,
                ncm_table.c.sujeito_is,
            )
            .where(ncm_table.c.descricao.ilike(f"%{term}%"))
            .limit(_MAX_RESULTS)
        )
        rows = db.execute(stmt4).mappings().all()
        if rows:
            return _rows_to_candidates(rows, "local")

    return None


# ── Main skill function ─────────────────────────────────────────────

async def classify_ncm(params: dict, context: dict) -> dict:
    """Suggest NCM codes based on a product description.

    Strategy pipeline:
      1. Web search  → ``source: 'web'``
      2. Local search → ``source: 'local'``
      3. Fallback     → ``needs_user_input: true``

    Args:
        params: Must contain ``descricao`` (str).
        context: Must contain ``db`` (SQLAlchemy Session).

    Returns:
        dict with ``candidates`` list.  Each candidate has ``codigo``,
        ``descricao``, ``sujeito_is``, and ``source``.
        On fallback, returns ``needs_user_input: true`` and ``message``.
    """
    descricao = params.get("descricao", "").strip()
    if not descricao:
        return {"candidates": []}

    db = context.get("db")
    if db is None:
        return {"candidates": [], "error": "No database session in context"}

    ncm_table = Base.metadata.tables.get("ncm")
    if ncm_table is None:
        return {"candidates": [], "error": "Table 'ncm' not found in metadata"}

    # ── Strategy 1: Web search ──────────────────────────────
    web_result = await _strategy_web(descricao, db, ncm_table)
    if web_result:
        return web_result

    # ── Strategy 2: Local search ────────────────────────────
    local_result = await _strategy_local(descricao, db, ncm_table)
    if local_result:
        return local_result

    # ── Strategy 3: Fallback — ask user ─────────────────────
    return {
        "candidates": [],
        "needs_user_input": True,
        "message": (
            "Não consegui identificar o NCM automaticamente. "
            "Você pode informar?"
        ),
    }


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="classify_ncm",
    fn=classify_ncm,
    description=(
        "Search for NCM codes matching a product description. Uses a "
        "three-stage pipeline: (1) web search for NCM codes and "
        "validation against the local table, (2) local ILIKE / keyword / "
        "prefix search, (3) fallback asking the user. Returns up to 5 "
        "candidates with codigo, descricao, sujeito_is, and source."
    ),
    params_schema={
        "type": "object",
        "properties": {
            "descricao": {
                "type": "string",
                "description": "Product description to search for",
            },
        },
        "required": ["descricao"],
    },
)
