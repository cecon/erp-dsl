"""Skill: classify_ncm — suggest NCM codes by product description.

Searches the ``ncm`` table using ILIKE for similarity matching.
Requires a SQLAlchemy Session available in ``context["db"]``.

Contract: async def classify_ncm(params: dict, context: dict) -> dict
"""

from __future__ import annotations

from sqlalchemy import select

from src.application.agent import skill_registry
from src.infrastructure.persistence.sqlalchemy.models import Base

_MAX_RESULTS = 5


async def classify_ncm(params: dict, context: dict) -> dict:
    """Suggest NCM codes based on a product description.

    Args:
        params: Must contain ``descricao`` (str).
        context: Must contain ``db`` (SQLAlchemy Session).

    Returns:
        dict with key ``candidates``: list of up to 5 dicts, each with
        ``codigo``, ``descricao``, ``sujeito_is``.
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

    # Build ILIKE query — split terms for broader matching
    terms = descricao.split()
    stmt = select(
        ncm_table.c.codigo,
        ncm_table.c.descricao,
        ncm_table.c.sujeito_is,
    )
    for term in terms:
        stmt = stmt.where(ncm_table.c.descricao.ilike(f"%{term}%"))

    stmt = stmt.limit(_MAX_RESULTS)

    rows = db.execute(stmt).mappings().all()
    return {
        "candidates": [
            {
                "codigo": row["codigo"],
                "descricao": row["descricao"],
                "sujeito_is": bool(row["sujeito_is"]),
            }
            for row in rows
        ]
    }


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="classify_ncm",
    fn=classify_ncm,
    description=(
        "Search the NCM catalog table for codes matching a product "
        "description. Returns up to 5 candidates with codigo, "
        "descricao, and sujeito_is."
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
