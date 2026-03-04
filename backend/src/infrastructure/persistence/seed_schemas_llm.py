"""DSL schema definitions for LLM Provider configuration.

Allows tenants to configure their LLM provider (e.g. Gemini API key)
directly from the UI, without needing environment variables.
"""

from __future__ import annotations

from typing import Any

# ── Shared dataSource fields ─────────────────────────────────────

_LLM_PROVIDER_DS_FIELDS: list[dict[str, Any]] = [
    {
        "id": "provider",
        "dbType": "string",
        "required": True,
    },
    {
        "id": "model",
        "dbType": "string",
        "required": True,
    },
    {
        "id": "api_key_encrypted",
        "dbType": "string",
        "required": True,
    },
    {
        "id": "base_url",
        "dbType": "string",
        "required": False,
    },
    {
        "id": "is_active",
        "dbType": "boolean",
        "required": False,
        "defaultValue": True,
    },
]


# ── Grid Page (list) ─────────────────────────────────────────────

LLM_PROVIDERS_PAGE_SCHEMA: dict[str, Any] = {
    "title": "Provedores LLM",
    "description": "Configuração de provedores de inteligência artificial",
    "layout": "grid",
    "dataSource": {
        "endpoint": "/entities/llm_providers",
        "tableName": "llm_providers",
        "method": "GET",
        "paginationParams": {"offset": "offset", "limit": "limit"},
        "fields": _LLM_PROVIDER_DS_FIELDS,
    },
    "components": [],
    "columns": [
        {"id": "col-provider", "key": "provider", "label": "Provedor"},
        {"id": "col-model", "key": "model", "label": "Modelo"},
        {"id": "col-active", "key": "is_active", "label": "Ativo"},
    ],
    "actions": [
        {
            "id": "action-create",
            "type": "create",
            "label": "Novo Provedor",
            "navigateTo": "/pages/llm_providers_form",
        },
        {
            "id": "action-edit",
            "type": "edit",
            "label": "Editar",
            "navigateTo": "/pages/llm_providers_form",
        },
        {"id": "action-delete", "type": "delete", "label": "Excluir"},
    ],
}


# ── Form Page ────────────────────────────────────────────────────

LLM_PROVIDERS_FORM_SCHEMA: dict[str, Any] = {
    "title": "Configuração do Provedor LLM",
    "description": "Configure a API Key e modelo do provedor de IA",
    "layout": "form",
    "dataSource": {
        "endpoint": "/entities/llm_providers",
        "tableName": "llm_providers",
        "method": "POST",
        "fields": _LLM_PROVIDER_DS_FIELDS,
    },
    "components": [
        {
            "id": "llm-form-main",
            "type": "form",
            "components": [
                {
                    "id": "section-provider",
                    "type": "section",
                    "label": "Provedor",
                    "components": [
                        {
                            "id": "grid-provider",
                            "type": "grid",
                            "columns": 2,
                            "components": [
                                {
                                    "id": "provider",
                                    "type": "select",
                                    "label": "Provedor",
                                    "options": [
                                        {"value": "google", "label": "Google (Gemini)"},
                                        {"value": "openai", "label": "OpenAI"},
                                        {"value": "anthropic", "label": "Anthropic"},
                                    ],
                                },
                                {
                                    "id": "model",
                                    "type": "select",
                                    "label": "Modelo",
                                    "dataSource": "/llm/models",
                                    "dataSourceParams": {
                                        "api_key_encrypted": "api_key",
                                    },
                                    "options": [
                                        {"value": "gemini-3-flash-preview", "label": "Gemini 3 Flash Preview"},
                                        {"value": "gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
                                        {"value": "gemini-2.5-pro", "label": "Gemini 2.5 Pro"},
                                        {"value": "gemini-2.0-flash", "label": "Gemini 2.0 Flash"},
                                    ],
                                },
                            ],
                        },
                    ],
                },
                {
                    "id": "section-credentials",
                    "type": "section",
                    "label": "Credenciais",
                    "components": [
                        {
                            "id": "api_key_encrypted",
                            "type": "text",
                            "label": "API Key",
                            "placeholder": "Cole sua API Key aqui",
                        },
                        {
                            "id": "base_url",
                            "type": "text",
                            "label": "URL Base (opcional)",
                            "placeholder": "Deixe vazio para usar o padrão do provedor",
                        },
                    ],
                },
                {
                    "id": "section-status",
                    "type": "section",
                    "label": "Status",
                    "components": [
                        {
                            "id": "is_active",
                            "type": "checkbox",
                            "label": "Provedor Ativo",
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
                    "navigateTo": "/pages/llm_providers",
                },
            ],
        },
    ],
}
