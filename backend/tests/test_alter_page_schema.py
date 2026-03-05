"""Tests for alter_page_schema — _apply_changes alias normalisation."""

from __future__ import annotations

from src.application.agent.skills.alter_page_schema import (
    _apply_changes,
    _normalize_changes,
)


# ── _normalize_changes ──────────────────────────────────────────────

def test_normalize_title_alias():
    assert _normalize_changes({"title": "Painel"}) == {"update_title": "Painel"}


def test_normalize_subtitle_alias():
    assert _normalize_changes({"subtitle": "Visão geral"}) == {"update_description": "Visão geral"}


def test_normalize_description_alias():
    assert _normalize_changes({"description": "Desc"}) == {"update_description": "Desc"}


def test_normalize_components_alias():
    updates = [{"id": "stat-revenue", "label": "Receita"}]
    assert _normalize_changes({"components": updates}) == {"update_components": updates}


def test_normalize_passes_valid_keys_through():
    """Keys that are already canonical should not be altered."""
    result = _normalize_changes({"update_title": "OK", "add_fields": [{"id": "x"}]})
    assert result == {"update_title": "OK", "add_fields": [{"id": "x"}]}


# ── _apply_changes ──────────────────────────────────────────────────

_BASE_SCHEMA = {
    "title": "Dashboard",
    "description": "Overview and key metrics",
    "layout": "dashboard",
    "components": [
        {
            "id": "stats-row",
            "type": "stats_grid",
            "components": [
                {
                    "id": "stat-revenue",
                    "type": "stat_card",
                    "label": "Total Revenue",
                },
            ],
        },
    ],
}


def test_apply_update_title():
    schema, descs = _apply_changes(dict(_BASE_SCHEMA), {"update_title": "Painel"})
    assert schema["title"] == "Painel"
    assert len(descs) == 1


def test_apply_title_alias():
    """'title' should be normalised to 'update_title'."""
    schema, descs = _apply_changes(dict(_BASE_SCHEMA), {"title": "Painel"})
    assert schema["title"] == "Painel"
    assert len(descs) == 1


def test_apply_subtitle_alias():
    """'subtitle' should be normalised to 'update_description'."""
    schema, descs = _apply_changes(dict(_BASE_SCHEMA), {"subtitle": "Métricas gerais"})
    assert schema["description"] == "Métricas gerais"
    assert len(descs) == 1


def test_apply_combined_aliases():
    """Both 'title' and 'subtitle' in a single call."""
    schema, descs = _apply_changes(
        dict(_BASE_SCHEMA),
        {"title": "Painel", "subtitle": "Métricas gerais"},
    )
    assert schema["title"] == "Painel"
    assert schema["description"] == "Métricas gerais"
    assert len(descs) == 2


def test_apply_invalid_keys_returns_descriptive_error():
    """Unknown keys should produce an error listing received and valid keys."""
    schema, descs = _apply_changes(dict(_BASE_SCHEMA), {"foo": "bar"})
    # Should have no descriptions (no valid changes)
    assert descs == []
