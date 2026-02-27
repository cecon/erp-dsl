"""Skill: fetch_by_ean — look up product data by EAN barcode.

Uses the Open Food Facts public API. Returns None fields on failure
instead of raising exceptions, so the agent can gracefully handle
missing products.

Contract: async def fetch_by_ean(params: dict, context: dict) -> dict
"""

from __future__ import annotations

import httpx

from src.application.agent import skill_registry

_OFF_URL = "https://mundo.openfoodfacts.org/api/v0/product/{ean}.json"
_TIMEOUT = 10  # seconds


async def fetch_by_ean(params: dict, context: dict) -> dict:
    """Fetch product info from Open Food Facts by EAN code.

    Args:
        params: Must contain ``ean`` (str).
        context: Ignored by this skill.

    Returns:
        dict with keys: name, brand, description, foto_url.
        All values are None if the product is not found.
    """
    ean = params.get("ean", "").strip()
    empty = {"name": None, "brand": None, "description": None, "foto_url": None}

    if not ean:
        return empty

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(_OFF_URL.format(ean=ean))
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError):
        return empty

    if data.get("status") != 1:
        return empty

    product = data.get("product", {})
    return {
        "name": product.get("product_name") or None,
        "brand": product.get("brands") or None,
        "description": product.get("generic_name") or None,
        "foto_url": product.get("image_front_url") or None,
    }


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="fetch_by_ean",
    fn=fetch_by_ean,
    description=(
        "Look up product data (name, brand, description, photo URL) "
        "by EAN/GTIN barcode using the Open Food Facts public API."
    ),
    params_schema={
        "type": "object",
        "properties": {
            "ean": {"type": "string", "description": "EAN/GTIN barcode (8 or 13 digits)"},
        },
        "required": ["ean"],
    },
)
