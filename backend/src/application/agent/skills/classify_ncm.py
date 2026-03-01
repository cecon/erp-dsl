"""Skill: classify_ncm — search NCM codes by product category.

Performs an ILIKE search on the ``ncm`` table using a category string
provided by the LLM.  The LLM is responsible for inferring the category
from the product description before calling this skill.

Contract: async def classify_ncm(params: dict, context: dict) -> dict
"""

from __future__ import annotations

from sqlalchemy import select

from src.application.agent import skill_registry
from src.infrastructure.persistence.sqlalchemy.models import Base

_DEFAULT_MAX_RESULTS = 5


async def classify_ncm(params: dict, context: dict) -> dict:
    """Search the NCM catalog table by product category.

    Args:
        params: Must contain ``categoria`` (str).
                Optional ``max_results`` (int, default 5).
        context: Must contain ``db`` (SQLAlchemy Session).

    Returns:
        dict with key ``candidates``: list of up to *max_results* dicts,
        each with ``codigo`` and ``descricao``.
    """
    categoria = params.get("categoria", "").strip()
    if not categoria:
        return {"candidates": []}

    max_results = int(params.get("max_results", _DEFAULT_MAX_RESULTS))

    db = context.get("db")
    if db is None:
        return {"candidates": [], "error": "No database session in context"}

    ncm_table = Base.metadata.tables.get("ncm")
    if ncm_table is None:
        return {"candidates": [], "error": "Table 'ncm' not found in metadata"}

    # Split into terms for multi-word category matching
    terms = [t for t in categoria.split() if len(t) >= 2]
    if not terms:
        return {"candidates": []}

    # Build query: each term must appear in the description
    stmt = select(
        ncm_table.c.codigo,
        ncm_table.c.descricao,
    )
    for term in terms:
        stmt = stmt.where(ncm_table.c.descricao.ilike(f"%{term}%"))
    stmt = stmt.limit(max_results)

    rows = db.execute(stmt).mappings().all()

    return {
        "candidates": [
            {
                "codigo": row["codigo"],
                "descricao": row["descricao"],
            }
            for row in rows
        ]
    }


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="classify_ncm",
    fn=classify_ncm,
    description=(
        "Search the NCM catalog for codes matching a product CATEGORY. "
        "The category should be a TIPI classification term in Portuguese "
        "(e.g., 'refrigerante', 'cerveja', 'queijo', 'carne bovina', "
        "'calçado', 'smartphone'). Returns up to max_results candidates "
        "with codigo and descricao. The LLM must infer the category "
        "from the product description before calling this skill."
    ),
    params_schema={
        "type": "object",
        "properties": {
            "categoria": {
                "type": "string",
                "description": (
                    "Product category in Portuguese for NCM search "
                    "(e.g., 'refrigerante', 'cerveja', 'carne bovina')"
                ),
            },
            "max_results": {
                "type": "integer",
                "description": "Max number of results to return (default: 5)",
                "default": 5,
            },
        },
        "required": ["categoria"],
    },
)
