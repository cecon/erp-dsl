"""DSL schemas for the Workflows pages (grid listing + form editor)."""

from __future__ import annotations

from typing import Any

# ─── Workflows Grid Page ─────────────────────────────────────────

WORKFLOWS_PAGE_SCHEMA: dict[str, Any] = {
    "title": "Workflows",
    "description": "Automações e comandos personalizados",
    "layout": "grid",
    "dataSource": {
        "endpoint": "/workflows",
        "tableName": "workflows",
        "method": "GET",
    },
    "columns": [
        {"id": "col-name", "key": "name", "label": "Nome"},
        {"id": "col-command", "key": "command", "label": "Comando"},
        {
            "id": "col-status",
            "key": "status",
            "label": "Status",
        },
        {"id": "col-version", "key": "version", "label": "Versão"},
    ],
    "actions": [
        {
            "id": "action-create",
            "type": "create",
            "label": "Novo Workflow",
            "navigateTo": "/pages/workflows_form",
        },
        {
            "id": "action-edit",
            "type": "edit",
            "label": "Editar",
            "navigateTo": "/pages/workflows_form",
        },
        {
            "id": "action-delete",
            "type": "delete",
            "label": "Excluir",
        },
    ],
}

# ─── Workflows Form Page ─────────────────────────────────────────

WORKFLOWS_FORM_SCHEMA: dict[str, Any] = {
    "title": "Editor de Workflow",
    "description": "Defina os steps e configurações do workflow",
    "layout": "form",
    "dataSource": {
        "endpoint": "/workflows",
        "tableName": "workflows",
    },
    "components": [
        {
            "id": "workflow-form",
            "type": "form",
            "components": [
                {
                    "id": "name",
                    "type": "text",
                    "label": "Nome do Workflow",
                },
                {
                    "id": "command",
                    "type": "text",
                    "label": "Comando (ex: /cadastrar-produto)",
                },
                {
                    "id": "description",
                    "type": "textarea",
                    "label": "Descrição",
                },
                {
                    "id": "status",
                    "type": "select",
                    "label": "Status",
                    "options": [
                        {"value": "draft", "label": "Rascunho"},
                        {"value": "published", "label": "Publicado"},
                        {"value": "archived", "label": "Arquivado"},
                    ],
                },
                {
                    "id": "steps",
                    "type": "workflow_step_editor",
                    "label": "Steps do Workflow",
                },
            ],
        },
    ],
}
