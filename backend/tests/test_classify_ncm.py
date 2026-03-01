"""Tests for classify_ncm skill — category-based NCM search.

Uses lightweight mocks; no real database or network required.
"""

from __future__ import annotations

import asyncio
import sys
import types
from unittest.mock import MagicMock, patch

# Stub web_search module to avoid bs4 dependency during import
if "src.application.agent.skills.web_search" not in sys.modules:
    _ws_stub = types.ModuleType("src.application.agent.skills.web_search")
    _ws_stub.web_search = MagicMock()  # type: ignore[attr-defined]
    sys.modules["src.application.agent.skills.web_search"] = _ws_stub
if "bs4" not in sys.modules:
    _bs4 = types.ModuleType("bs4")
    _bs4.BeautifulSoup = MagicMock()  # type: ignore[attr-defined]
    sys.modules["bs4"] = _bs4


# ── Helpers ──────────────────────────────────────────────────────────

def _make_fake_db(rows: list[dict]):
    db = MagicMock()
    db.execute.return_value.mappings.return_value.all.return_value = rows
    return db


NCM_REFRIGERANTE = {
    "codigo": "22029010",
    "descricao": "Refrigerantes",
}

NCM_QUEIJO = {
    "codigo": "04061000",
    "descricao": "Queijo fresco (não curado), incluindo requeijão",
}


# ── Tests ────────────────────────────────────────────────────────────

def test_search_by_category_returns_candidates():
    """ILIKE on categoria should return matching NCM candidates."""
    fake_db = _make_fake_db([NCM_REFRIGERANTE])

    fake_select = MagicMock()
    fake_stmt = MagicMock()
    fake_select.return_value = fake_stmt
    fake_stmt.where.return_value = fake_stmt
    fake_stmt.limit.return_value = fake_stmt

    async def _run():
        with (
            patch("src.application.agent.skills.classify_ncm.Base") as mock_base,
            patch("src.application.agent.skills.classify_ncm.select", fake_select),
        ):
            mock_base.metadata.tables.get.return_value = MagicMock()
            from src.application.agent.skills.classify_ncm import classify_ncm
            return await classify_ncm(
                {"categoria": "refrigerante"},
                {"db": fake_db},
            )

    result = asyncio.run(_run())
    assert result["candidates"]
    assert result["candidates"][0]["codigo"] == "22029010"


def test_multi_word_category():
    """Multi-word categories like 'carne bovina' should work."""
    fake_db = _make_fake_db([{
        "codigo": "02013000",
        "descricao": "Carne bovina desossada, fresca ou refrigerada",
    }])

    fake_select = MagicMock()
    fake_stmt = MagicMock()
    fake_select.return_value = fake_stmt
    fake_stmt.where.return_value = fake_stmt
    fake_stmt.limit.return_value = fake_stmt

    async def _run():
        with (
            patch("src.application.agent.skills.classify_ncm.Base") as mock_base,
            patch("src.application.agent.skills.classify_ncm.select", fake_select),
        ):
            mock_base.metadata.tables.get.return_value = MagicMock()
            from src.application.agent.skills.classify_ncm import classify_ncm
            return await classify_ncm(
                {"categoria": "carne bovina"},
                {"db": fake_db},
            )

    result = asyncio.run(_run())
    assert result["candidates"]
    assert "02013000" == result["candidates"][0]["codigo"]


def test_empty_category_returns_empty():
    """Empty category should return empty candidates."""
    async def _run():
        with patch("src.application.agent.skills.classify_ncm.Base"):
            from src.application.agent.skills.classify_ncm import classify_ncm
            return await classify_ncm({"categoria": ""}, {"db": MagicMock()})

    result = asyncio.run(_run())
    assert result == {"candidates": []}


def test_no_db_returns_error():
    """Missing db in context should return an error."""
    async def _run():
        with patch("src.application.agent.skills.classify_ncm.Base"):
            from src.application.agent.skills.classify_ncm import classify_ncm
            return await classify_ncm({"categoria": "refrigerante"}, {})

    result = asyncio.run(_run())
    assert "error" in result


def test_no_matches_returns_empty_candidates():
    """Query with no matches should return empty candidates list."""
    fake_db = _make_fake_db([])

    fake_select = MagicMock()
    fake_stmt = MagicMock()
    fake_select.return_value = fake_stmt
    fake_stmt.where.return_value = fake_stmt
    fake_stmt.limit.return_value = fake_stmt

    async def _run():
        with (
            patch("src.application.agent.skills.classify_ncm.Base") as mock_base,
            patch("src.application.agent.skills.classify_ncm.select", fake_select),
        ):
            mock_base.metadata.tables.get.return_value = MagicMock()
            from src.application.agent.skills.classify_ncm import classify_ncm
            return await classify_ncm(
                {"categoria": "xyznotexist"},
                {"db": fake_db},
            )

    result = asyncio.run(_run())
    assert result["candidates"] == []
