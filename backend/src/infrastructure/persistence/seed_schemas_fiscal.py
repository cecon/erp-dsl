"""DSL schema definitions for fiscal module seed data.

Separated from seed_schemas.py to respect the 300-line limit.
"""

from __future__ import annotations

from typing import Any

# ─── Tax Groups CRUD Page ────────────────────────────────────────

TAX_GROUPS_PAGE_SCHEMA: dict[str, Any] = {
    "title": "Grupo Tributário",
    "description": "Cadastro de grupos tributários",
    "layout": "grid",
    "dataSource": {
        "endpoint": "/entities/tax_groups",
        "tableName": "tax_groups",
        "method": "GET",
        "paginationParams": {"offset": "offset", "limit": "limit"},
        "fields": [
            {"id": "descricao", "dbType": "string", "required": True},
        ],
    },
    "components": [
        {
            "id": "tax-group-form",
            "type": "form",
            "components": [
                {
                    "id": "descricao",
                    "type": "text",
                    "label": "Descrição",
                },
            ],
        },
    ],
    "columns": [
        {"id": "col-descricao", "key": "descricao", "label": "Descrição"},
    ],
    "actions": [
        {
            "id": "action-create",
            "type": "create",
            "label": "Novo Grupo",
        },
        {"id": "action-edit", "type": "edit", "label": "Editar"},
        {"id": "action-delete", "type": "delete", "label": "Excluir"},
    ],
}

# ─── Operation Natures CRUD Page ─────────────────────────────────

OPERATION_NATURES_PAGE_SCHEMA: dict[str, Any] = {
    "title": "Natureza de Operação",
    "description": "Cadastro de naturezas de operação",
    "layout": "grid",
    "dataSource": {
        "endpoint": "/entities/operation_natures",
        "tableName": "operation_natures",
        "method": "GET",
        "paginationParams": {"offset": "offset", "limit": "limit"},
        "fields": [
            {"id": "descricao", "dbType": "string", "required": True},
            {"id": "tipo_movimento", "dbType": "string", "required": True},
        ],
    },
    "components": [
        {
            "id": "operation-nature-form",
            "type": "form",
            "components": [
                {
                    "id": "descricao",
                    "type": "text",
                    "label": "Descrição",
                },
                {
                    "id": "tipo_movimento",
                    "type": "select",
                    "label": "Tipo de Movimento",
                    "options": [
                        {"value": "Entrada", "label": "Entrada"},
                        {"value": "Saída", "label": "Saída"},
                    ],
                },
            ],
        },
    ],
    "columns": [
        {"id": "col-descricao", "key": "descricao", "label": "Descrição"},
        {
            "id": "col-tipo",
            "key": "tipo_movimento",
            "label": "Tipo Movimento",
        },
    ],
    "actions": [
        {
            "id": "action-create",
            "type": "create",
            "label": "Nova Natureza",
        },
        {"id": "action-edit", "type": "edit", "label": "Editar"},
        {"id": "action-delete", "type": "delete", "label": "Excluir"},
    ],
}

# ─── Fiscal Rules CRUD Page ──────────────────────────────────────

FISCAL_RULES_PAGE_SCHEMA: dict[str, Any] = {
    "title": "Regras Fiscais",
    "description": "Matriz de regras fiscais (Grupo x Natureza x UF)",
    "layout": "grid",
    "dataSource": {
        "endpoint": "/entities/fiscal_rules",
        "tableName": "fiscal_rules",
        "method": "GET",
        "paginationParams": {"offset": "offset", "limit": "limit"},
        "fields": [
            {"id": "id_grupo_tributario", "dbType": "string", "required": True},
            {"id": "id_natureza_operacao", "dbType": "string", "required": True},
            {"id": "uf_origem", "dbType": "string", "required": False},
            {"id": "uf_destino", "dbType": "string", "required": False},
            {"id": "tipo_contribuinte_dest", "dbType": "string", "required": False},
            {"id": "cfop", "dbType": "string", "required": False},
            {"id": "icms_cst", "dbType": "string", "required": False},
            {"id": "icms_csosn", "dbType": "string", "required": False},
            {"id": "icms_aliquota", "dbType": "decimal", "required": False},
            {"id": "icms_perc_reducao_bc", "dbType": "decimal", "required": False},
            {"id": "pis_cst", "dbType": "string", "required": False},
            {"id": "cofins_cst", "dbType": "string", "required": False},
            {"id": "ibs_cbs_cst", "dbType": "string", "required": False},
            {"id": "ibs_aliquota_uf", "dbType": "decimal", "required": False},
            {"id": "ibs_aliquota_mun", "dbType": "decimal", "required": False},
            {"id": "cbs_aliquota", "dbType": "decimal", "required": False},
            {"id": "is_cst", "dbType": "string", "required": False},
            {"id": "is_aliquota", "dbType": "decimal", "required": False},
        ],
    },
    "components": [
        {
            "id": "fiscal-rule-form",
            "type": "form",
            "components": [
                {
                    "id": "id_grupo_tributario",
                    "type": "text",
                    "label": "Grupo Tributário (ID)",
                },
                {
                    "id": "id_natureza_operacao",
                    "type": "text",
                    "label": "Natureza Operação (ID)",
                },
                {
                    "id": "uf_origem",
                    "type": "text",
                    "label": "UF Origem",
                },
                {
                    "id": "uf_destino",
                    "type": "text",
                    "label": "UF Destino",
                },
                {
                    "id": "tipo_contribuinte_dest",
                    "type": "select",
                    "label": "Tipo Contribuinte Destino",
                    "options": [
                        {
                            "value": "Contribuinte",
                            "label": "Contribuinte",
                        },
                        {
                            "value": "Não Contribuinte",
                            "label": "Não Contribuinte",
                        },
                        {"value": "Isento", "label": "Isento"},
                    ],
                },
                {"id": "cfop", "type": "text", "label": "CFOP"},
                {"id": "icms_cst", "type": "text", "label": "ICMS CST"},
                {
                    "id": "icms_csosn",
                    "type": "text",
                    "label": "ICMS CSOSN",
                },
                {
                    "id": "icms_aliquota",
                    "type": "number",
                    "label": "ICMS Alíquota (%)",
                },
                {
                    "id": "icms_perc_reducao_bc",
                    "type": "number",
                    "label": "ICMS % Red. BC",
                },
                {"id": "pis_cst", "type": "text", "label": "PIS CST"},
                {
                    "id": "cofins_cst",
                    "type": "text",
                    "label": "COFINS CST",
                },
                {
                    "id": "ibs_cbs_cst",
                    "type": "text",
                    "label": "IBS/CBS CST",
                },
                {
                    "id": "ibs_aliquota_uf",
                    "type": "number",
                    "label": "IBS Alíq. UF (%)",
                },
                {
                    "id": "ibs_aliquota_mun",
                    "type": "number",
                    "label": "IBS Alíq. Mun. (%)",
                },
                {
                    "id": "cbs_aliquota",
                    "type": "number",
                    "label": "CBS Alíquota (%)",
                },
                {"id": "is_cst", "type": "text", "label": "IS CST"},
                {
                    "id": "is_aliquota",
                    "type": "number",
                    "label": "IS Alíquota (%)",
                },
            ],
        },
    ],
    "columns": [
        {"id": "col-cfop", "key": "cfop", "label": "CFOP"},
        {"id": "col-uf-orig", "key": "uf_origem", "label": "UF Orig."},
        {"id": "col-uf-dest", "key": "uf_destino", "label": "UF Dest."},
        {"id": "col-icms-cst", "key": "icms_cst", "label": "ICMS CST"},
        {
            "id": "col-icms-aliq",
            "key": "icms_aliquota",
            "label": "ICMS %",
        },
        {"id": "col-pis", "key": "pis_cst", "label": "PIS CST"},
        {"id": "col-cofins", "key": "cofins_cst", "label": "COFINS CST"},
    ],
    "actions": [
        {
            "id": "action-create",
            "type": "create",
            "label": "Nova Regra",
        },
        {"id": "action-edit", "type": "edit", "label": "Editar"},
        {"id": "action-delete", "type": "delete", "label": "Excluir"},
    ],
}

# ─── Theme Configuration ─────────────────────────────────────────

THEME_CONFIG_SCHEMA: dict[str, Any] = {
    "title": "Theme Settings",
    "components": [
        {
            "id": "primaryColor",
            "type": "color_swatch_picker",
            "label": "Primary Color",
            "options": [
                {"value": "blue", "hex": "#3b82f6"},
                {"value": "teal", "hex": "#14b8a6"},
                {"value": "violet", "hex": "#8b5cf6"},
                {"value": "cyan", "hex": "#06b6d4"},
                {"value": "orange", "hex": "#f97316"},
                {"value": "indigo", "hex": "#6366f1"},
                {"value": "green", "hex": "#22c55e"},
            ],
        },
        {
            "id": "colorScheme",
            "type": "theme_switch",
            "label": "Color Scheme",
            "on_label": "Dark Mode",
            "off_label": "Light Mode",
            "on_value": "dark",
            "off_value": "light",
        },
        {
            "id": "radius",
            "type": "segmented",
            "label": "Border Radius",
            "options": [
                {"value": "xs", "label": "XS"},
                {"value": "sm", "label": "SM"},
                {"value": "md", "label": "MD"},
                {"value": "lg", "label": "LG"},
                {"value": "xl", "label": "XL"},
            ],
        },
        {
            "id": "fontSize",
            "type": "segmented",
            "label": "Font Size",
            "options": [
                {"value": "sm", "label": "Small"},
                {"value": "md", "label": "Medium"},
                {"value": "lg", "label": "Large"},
            ],
        },
        {
            "id": "sidebarCollapsed",
            "type": "theme_switch",
            "label": "Sidebar",
            "on_label": "Collapsed",
            "off_label": "Expanded",
        },
    ],
}
