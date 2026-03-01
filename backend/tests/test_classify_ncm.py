"""Tests for classify_ncm skill — three-strategy pipeline.

Tests use lightweight mocks to avoid hitting the real database or web.
The web_search module is stubbed in sys.modules before importing classify_ncm
to avoid the bs4 dependency.  SQLAlchemy's ``select`` and ``or_`` are also
patched so we don't need real Column objects.
"""

from __future__ import annotations

import asyncio
import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Stub the web_search module before importing classify_ncm
# ---------------------------------------------------------------------------

_ws_module = types.ModuleType("src.application.agent.skills.web_search")
_ws_mock = AsyncMock(return_value={"results": []})
_ws_module.web_search = _ws_mock  # type: ignore[attr-defined]
sys.modules["src.application.agent.skills.web_search"] = _ws_module

if "bs4" not in sys.modules:
    _bs4_stub = types.ModuleType("bs4")
    _bs4_stub.BeautifulSoup = MagicMock()  # type: ignore[attr-defined]
    sys.modules["bs4"] = _bs4_stub


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_db(rows: list[dict]):
    """Return a MagicMock session whose execute().mappings().all() returns *rows*."""
    db = MagicMock()
    mappings_mock = MagicMock()
    mappings_mock.all.return_value = rows
    result_mock = MagicMock()
    result_mock.mappings.return_value = mappings_mock
    db.execute.return_value = result_mock
    return db


# ---------------------------------------------------------------------------
# Common test data
# ---------------------------------------------------------------------------

NCM_ROW_2202 = {
    "codigo": "22021000",
    "descricao": "Águas, incluindo águas minerais e gaseificadas, adicionadas de açúcar",
    "sujeito_is": False,
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_web_strategy_finds_ncm():
    """Strategy 1 (web) should return candidates with source='web'."""

    fake_db = _make_fake_db([NCM_ROW_2202])

    web_result = {
        "results": [
            {
                "title": "NCM Coca-Cola",
                "url": "https://example.com",
                "snippet": "O NCM para refrigerantes é 2202.10.00 conforme TIPI.",
            }
        ]
    }

    _ws_module.web_search = AsyncMock(return_value=web_result)

    # Mock select & or_ so SQLAlchemy doesn't validate column types
    fake_select = MagicMock()
    fake_stmt = MagicMock()
    fake_select.return_value = fake_stmt
    fake_stmt.where.return_value = fake_stmt
    fake_stmt.limit.return_value = fake_stmt

    async def _run():
        with (
            patch("src.application.agent.skills.classify_ncm.Base") as mock_base,
            patch("src.application.agent.skills.classify_ncm.select", fake_select),
            patch("src.application.agent.skills.classify_ncm.or_", MagicMock()),
        ):
            # Build a minimal fake table with MagicMock columns
            fake_table = MagicMock()
            mock_base.metadata.tables.get.return_value = fake_table

            from src.application.agent.skills.classify_ncm import classify_ncm
            return await classify_ncm(
                {"descricao": "coca cola lata 350ml"},
                {"db": fake_db},
            )

    result = asyncio.run(_run())

    assert result["candidates"]
    assert result["candidates"][0]["source"] == "web"
    assert result["candidates"][0]["codigo"] == "22021000"


def test_local_strategy_when_web_fails():
    """Strategy 2 (local) should kick in when web returns nothing useful."""

    # Web returns results with NO 8-digit NCM codes
    _ws_module.web_search = AsyncMock(return_value={
        "results": [
            {"title": "Algo", "url": "", "snippet": "nenhum código aqui"}
        ]
    })

    fake_select = MagicMock()
    fake_stmt = MagicMock()
    fake_select.return_value = fake_stmt
    fake_stmt.where.return_value = fake_stmt
    fake_stmt.limit.return_value = fake_stmt

    # Track db.execute calls: web strategy won't call db (no NCM codes in text),
    # so all calls come from local strategy
    fake_db = _make_fake_db([NCM_ROW_2202])

    async def _run():
        with (
            patch("src.application.agent.skills.classify_ncm.Base") as mock_base,
            patch("src.application.agent.skills.classify_ncm.select", fake_select),
            patch("src.application.agent.skills.classify_ncm.or_", MagicMock()),
        ):
            fake_table = MagicMock()
            mock_base.metadata.tables.get.return_value = fake_table

            from src.application.agent.skills.classify_ncm import classify_ncm
            return await classify_ncm(
                {"descricao": "coca cola lata 350ml"},
                {"db": fake_db},
            )

    result = asyncio.run(_run())

    assert result["candidates"]
    assert result["candidates"][0]["source"] == "local"


def test_fallback_needs_user_input():
    """Strategy 3 (fallback) should return needs_user_input when nothing matches."""

    _ws_module.web_search = AsyncMock(return_value={"results": []})

    fake_select = MagicMock()
    fake_stmt = MagicMock()
    fake_select.return_value = fake_stmt
    fake_stmt.where.return_value = fake_stmt
    fake_stmt.limit.return_value = fake_stmt

    fake_db = _make_fake_db([])  # always empty

    async def _run():
        with (
            patch("src.application.agent.skills.classify_ncm.Base") as mock_base,
            patch("src.application.agent.skills.classify_ncm.select", fake_select),
            patch("src.application.agent.skills.classify_ncm.or_", MagicMock()),
        ):
            fake_table = MagicMock()
            mock_base.metadata.tables.get.return_value = fake_table

            from src.application.agent.skills.classify_ncm import classify_ncm
            return await classify_ncm(
                {"descricao": "produto desconhecido xyz"},
                {"db": fake_db},
            )

    result = asyncio.run(_run())

    assert result["needs_user_input"] is True
    assert result["candidates"] == []
    assert "message" in result


def test_empty_description_returns_empty():
    """Empty description should return empty candidates without errors."""

    async def _run():
        with patch("src.application.agent.skills.classify_ncm.Base"):
            from src.application.agent.skills.classify_ncm import classify_ncm
            return await classify_ncm({"descricao": ""}, {"db": MagicMock()})

    result = asyncio.run(_run())
    assert result == {"candidates": []}


def test_no_db_returns_error():
    """Missing db in context should return an error."""

    async def _run():
        with patch("src.application.agent.skills.classify_ncm.Base"):
            from src.application.agent.skills.classify_ncm import classify_ncm
            return await classify_ncm({"descricao": "coca cola"}, {})

    result = asyncio.run(_run())
    assert "error" in result
