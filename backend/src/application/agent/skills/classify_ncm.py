"""Skill: classify_ncm — suggest NCM codes by product description.

Searches the ``ncm`` table using three strategies in order:
1. **ILIKE** — text search splitting description into terms
2. **Keyword mapping** — maps common product keywords to NCM prefixes
3. **Prefix fallback** — extracts 4-digit NCM codes from text and searches
4. **Relaxed single-term** — tries each long word individually

Contract: async def classify_ncm(params: dict, context: dict) -> dict
"""

from __future__ import annotations

import re

from sqlalchemy import or_, select

from src.application.agent import skill_registry
from src.infrastructure.persistence.sqlalchemy.models import Base

_MAX_RESULTS = 5

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


async def classify_ncm(params: dict, context: dict) -> dict:
    """Suggest NCM codes based on a product description.

    Strategy 1 — Text search via ILIKE on description terms.
    Strategy 2 — Keyword mapping (product brand/category → NCM prefix).
    Strategy 3 — Extract NCM-like numbers from text and search by prefix.
    Strategy 4 — Relaxed single-term ILIKE search.

    Args:
        params: Must contain ``descricao`` (str).
        context: Must contain ``db`` (SQLAlchemy Session).

    Returns:
        dict with key ``candidates``: list of up to 5 dicts, each with
        ``codigo``, ``descricao``, ``sujeito_is``, and ``match_strategy``.
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

    terms = descricao.split()

    def _rows_to_candidates(rows, strategy: str) -> dict:
        return {
            "candidates": [
                {
                    "codigo": row["codigo"],
                    "descricao": row["descricao"],
                    "sujeito_is": bool(row["sujeito_is"]),
                    "match_strategy": strategy,
                }
                for row in rows
            ]
        }

    # ── Strategy 1: ILIKE multi-term ────────────────────────
    stmt1 = select(
        ncm_table.c.codigo,
        ncm_table.c.descricao,
        ncm_table.c.sujeito_is,
    )
    meaningful = [t for t in terms if len(t) >= 3]
    if meaningful:
        for term in meaningful:
            stmt1 = stmt1.where(ncm_table.c.descricao.ilike(f"%{term}%"))
        rows = db.execute(stmt1.limit(_MAX_RESULTS)).mappings().all()
        if rows:
            return _rows_to_candidates(rows, "ilike")

    # ── Strategy 2: Keyword → NCM prefix mapping ───────────
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
            return _rows_to_candidates(rows, "keyword")

    # ── Strategy 3: Extract NCM codes from text ─────────────
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
            return _rows_to_candidates(rows, "prefix")

    # ── Strategy 4: Relaxed single-term ILIKE ───────────────
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
            return _rows_to_candidates(rows, "relaxed")

    return {"candidates": []}


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="classify_ncm",
    fn=classify_ncm,
    description=(
        "Search the NCM catalog table for codes matching a product "
        "description. Returns up to 5 candidates with codigo, "
        "descricao, and sujeito_is. Uses ILIKE text search, keyword "
        "mapping, prefix matching, and relaxed single-term fallback."
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
