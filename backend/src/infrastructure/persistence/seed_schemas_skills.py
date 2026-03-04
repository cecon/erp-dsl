"""DSL schema definitions for Skills CRUD pages."""

from __future__ import annotations

from typing import Any

# ─── Skills fields definition ─────────────────────────────────────

_SKILL_DS_FIELDS: list[dict[str, Any]] = [
    {"id": "name", "dbType": "string", "required": True},
    {"id": "description", "dbType": "string", "required": True},
    {"id": "params_schema", "dbType": "string", "required": False},
    {"id": "category", "dbType": "string", "required": False},
    {"id": "enabled", "dbType": "string", "required": False},
]

# ─── Skills Grid Page ─────────────────────────────────────────────

SKILLS_PAGE_SCHEMA: dict[str, Any] = {
    "title": "Skills",
    "description": "Manage agent skills — enable, disable and edit descriptions",
    "layout": "grid",
    "dataSource": {
        "endpoint": "/entities/skills",
        "tableName": "skills",
        "method": "GET",
        "paginationParams": {"offset": "offset", "limit": "limit"},
        "fields": _SKILL_DS_FIELDS,
    },
    "components": [],
    "columns": [
        {"id": "col-name", "key": "name", "label": "Nome"},
        {"id": "col-category", "key": "category", "label": "Categoria"},
        {"id": "col-enabled", "key": "enabled", "label": "Ativo"},
        {"id": "col-description", "key": "description", "label": "Descrição"},
    ],
    "actions": [
        {
            "id": "action-create",
            "type": "create",
            "label": "Nova Skill",
            "navigateTo": "/pages/skills_form",
        },
        {
            "id": "action-edit",
            "type": "edit",
            "label": "Editar",
            "navigateTo": "/pages/skills_form",
        },
        {"id": "action-delete", "type": "delete", "label": "Excluir"},
    ],
}

# ─── Skills Form Page ─────────────────────────────────────────────

SKILLS_FORM_SCHEMA: dict[str, Any] = {
    "title": "Cadastro de Skill",
    "description": "Crie ou edite os metadados de uma skill de agente",
    "layout": "form",
    "dataSource": {
        "endpoint": "/entities/skills",
        "tableName": "skills",
        "method": "POST",
        "fields": _SKILL_DS_FIELDS,
    },
    "components": [
        {
            "id": "skill-form-main",
            "type": "form",
            "components": [
                # ── Identificação ────────────────────────
                {
                    "id": "section-identificacao",
                    "type": "section",
                    "label": "Identificação",
                    "components": [
                        {
                            "id": "grid-identificacao",
                            "type": "grid",
                            "columns": 2,
                            "components": [
                                {
                                    "id": "name",
                                    "type": "text",
                                    "label": "Nome da Skill",
                                    "placeholder": "ex: classify_ncm",
                                },
                                {
                                    "id": "category",
                                    "type": "select",
                                    "label": "Categoria",
                                    "options": [
                                        {"value": "crud", "label": "CRUD"},
                                        {"value": "fiscal", "label": "Fiscal"},
                                        {"value": "search", "label": "Busca"},
                                        {"value": "admin", "label": "Administração"},
                                        {"value": "ai", "label": "Inteligência Artificial"},
                                        {"value": "general", "label": "Geral"},
                                    ],
                                },
                            ],
                        },
                    ],
                },
                # ── Status ──────────────────────────────
                {
                    "id": "section-status",
                    "type": "section",
                    "label": "Status",
                    "components": [
                        {
                            "id": "enabled",
                            "type": "checkbox",
                            "label": "Skill ativa (disponível para o Otto)",
                        },
                    ],
                },
                # ── Descrição (prompt pro LLM) ───────────
                {
                    "id": "section-descricao",
                    "type": "section",
                    "label": "Descrição (usada pelo LLM)",
                    "components": [
                        {
                            "id": "description",
                            "type": "textarea",
                            "label": "Descrição",
                            "placeholder": "Descreva o que esta skill faz — este texto é enviado ao LLM",
                        },
                    ],
                },
                # ── Params Schema ────────────────────────
                {
                    "id": "section-params",
                    "type": "section",
                    "label": "JSON Schema dos Parâmetros",
                    "components": [
                        {
                            "id": "params_schema",
                            "type": "textarea",
                            "label": "Params Schema (JSON)",
                            "placeholder": '{"type": "object", "properties": {...}}',
                        },
                    ],
                },
            ],
            "actions": [
                {
                    "id": "submit-btn",
                    "type": "submit",
                    "label": "Salvar",
                },
                {
                    "id": "cancel-btn",
                    "type": "cancel",
                    "label": "Cancelar",
                    "navigateTo": "/pages/skills",
                },
            ],
        },
    ],
}
