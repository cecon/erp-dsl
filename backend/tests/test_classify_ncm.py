"""Tests for classify_ncm skill — three-strategy pipeline.

Tests use lightweight mocks to avoid hitting the real database or web.
Uses asyncio.run() instead of pytest-asyncio to avoid extra dependencies.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers to build a fake NCM table + DB session
# ---------------------------------------------------------------------------

def _make_fake_ncm_table():
    """Return a tiny fake table object with column accessors for WHERE clauses."""

    class _Col:
        def __init__(self, name: str):
            self.name = name

        def ilike(self, pattern: str):
            return ("ilike", self.name, pattern)

        def startswith(self, prefix: str):
            return ("startswith", self.name, prefix)

        def __eq__(self, other):
            return ("eq", self.name, other)

    class _Columns:
        codigo = _Col("codigo")
        descricao = _Col("descricao")
        sujeito_is = _Col("sujeito_is")

    table = MagicMock()
    table.c = _Columns()
    return table


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

    fake_table = _make_fake_ncm_table()
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

    mock_ws = AsyncMock(return_value=web_result)

    async def _run():
        with (
            patch(
                "src.application.agent.skills.classify_ncm.Base"
            ) as mock_base,
            patch(
                "src.application.agent.skills.web_search.web_search",
                mock_ws,
            ),
        ):
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
    """Strategy 2 (local) should kick in when web returns nothing."""

    fake_table = _make_fake_ncm_table()
    fake_db = MagicMock()
    call_count = {"n": 0}

    no_rows_mock = MagicMock()
    no_rows_mock.mappings.return_value.all.return_value = []
    yes_rows_mock = MagicMock()
    yes_rows_mock.mappings.return_value.all.return_value = [NCM_ROW_2202]

    def _side_effect(*_a, **_kw):
        call_count["n"] += 1
        # Web validation queries return empty; local queries return results
        if call_count["n"] <= 2:
            return no_rows_mock
        return yes_rows_mock

    fake_db.execute.side_effect = _side_effect

    web_result_with_no_ncm = {
        "results": [
            {"title": "Algo", "url": "", "snippet": "nenhum código aqui"}
        ]
    }

    mock_ws = AsyncMock(return_value=web_result_with_no_ncm)

    async def _run():
        with (
            patch(
                "src.application.agent.skills.classify_ncm.Base"
            ) as mock_base,
            patch(
                "src.application.agent.skills.web_search.web_search",
                mock_ws,
            ),
        ):
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

    fake_table = _make_fake_ncm_table()
    fake_db = _make_fake_db([])  # always empty

    mock_ws = AsyncMock(return_value={"results": []})

    async def _run():
        with (
            patch(
                "src.application.agent.skills.classify_ncm.Base"
            ) as mock_base,
            patch(
                "src.application.agent.skills.web_search.web_search",
                mock_ws,
            ),
        ):
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
        from src.application.agent.skills.classify_ncm import classify_ncm
        return await classify_ncm({"descricao": ""}, {"db": MagicMock()})

    result = asyncio.run(_run())
    assert result == {"candidates": []}


def test_no_db_returns_error():
    """Missing db in context should return an error."""

    async def _run():
        from src.application.agent.skills.classify_ncm import classify_ncm
        return await classify_ncm({"descricao": "coca cola"}, {})

    result = asyncio.run(_run())
    assert "error" in result
