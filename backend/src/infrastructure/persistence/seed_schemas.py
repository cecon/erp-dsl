"""DSL schema definitions for seed data.

Each schema is a page_key that the frontend fetches via GET /api/pages/{key}.
Layout schemas use underscore prefix (_sidebar, _header) to distinguish
them from content pages (products, dashboard).
"""

from __future__ import annotations

from typing import Any

# ─── Products CRUD Page ──────────────────────────────────────────

# ─── Shared field definitions for products ───────────────────────

_PRODUCT_DS_FIELDS: list[dict[str, Any]] = [
    {"id": "name", "dbType": "string", "required": True},
    {"id": "price", "dbType": "decimal", "required": True},
    {
        "id": "sku",
        "dbType": "string",
        "required": False,
        "transforms": [{"fn": "uppercase", "on": "request"}],
    },
    {"id": "ean", "dbType": "string", "required": False},
    {"id": "tipo_produto", "dbType": "string", "required": False},
    {"id": "description", "dbType": "string", "required": False},
    {"id": "descricao_tecnica", "dbType": "string", "required": False},
    {"id": "unidade", "dbType": "string", "required": False},
    {"id": "foto_url", "dbType": "string", "required": False},
    {"id": "custo", "dbType": "decimal", "required": False},
    {"id": "markup", "dbType": "decimal", "required": False},
    {"id": "margem", "dbType": "decimal", "required": False},
    {"id": "grupo", "dbType": "string", "required": False},
    {"id": "subgrupo", "dbType": "string", "required": False},
    {"id": "marca", "dbType": "string", "required": False},
    {"id": "tax_group_id", "dbType": "string", "required": False},
    {"id": "ncm_codigo", "dbType": "string", "required": False},
    {"id": "cest_codigo", "dbType": "string", "required": False},
    {"id": "cclass_codigo", "dbType": "string", "required": False},
    {"id": "ind_comb", "dbType": "string", "required": False},
    {"id": "cod_anp", "dbType": "string", "required": False},
    {"id": "desc_anp", "dbType": "string", "required": False},
    {"id": "uf_cons", "dbType": "string", "required": False},
    {"id": "codif", "dbType": "string", "required": False},
    {"id": "p_bio", "dbType": "decimal", "required": False},
    {"id": "q_temp", "dbType": "decimal", "required": False},
    {"id": "cst_is", "dbType": "string", "required": False},
    {"id": "cclass_trib_is", "dbType": "string", "required": False},
    {"id": "ad_rem_ibs", "dbType": "decimal", "required": False},
    {"id": "ad_rem_cbs", "dbType": "decimal", "required": False},
]

# ─── UF options (reused in ANP section) ──────────────────────────

_UF_OPTIONS: list[dict[str, str]] = [
    {"value": "", "label": "Selecione..."},
    {"value": "AC", "label": "AC"}, {"value": "AL", "label": "AL"},
    {"value": "AM", "label": "AM"}, {"value": "AP", "label": "AP"},
    {"value": "BA", "label": "BA"}, {"value": "CE", "label": "CE"},
    {"value": "DF", "label": "DF"}, {"value": "ES", "label": "ES"},
    {"value": "GO", "label": "GO"}, {"value": "MA", "label": "MA"},
    {"value": "MG", "label": "MG"}, {"value": "MS", "label": "MS"},
    {"value": "MT", "label": "MT"}, {"value": "PA", "label": "PA"},
    {"value": "PB", "label": "PB"}, {"value": "PE", "label": "PE"},
    {"value": "PI", "label": "PI"}, {"value": "PR", "label": "PR"},
    {"value": "RJ", "label": "RJ"}, {"value": "RN", "label": "RN"},
    {"value": "RO", "label": "RO"}, {"value": "RR", "label": "RR"},
    {"value": "RS", "label": "RS"}, {"value": "SC", "label": "SC"},
    {"value": "SE", "label": "SE"}, {"value": "SP", "label": "SP"},
    {"value": "TO", "label": "TO"},
]

PRODUCTS_PAGE_SCHEMA: dict[str, Any] = {
    "title": "Products",
    "description": "CRUD page for product management",
    "layout": "grid",
    "dataSource": {
        "endpoint": "/entities/products",
        "tableName": "products",
        "method": "GET",
        "paginationParams": {"offset": "offset", "limit": "limit"},
        "fields": _PRODUCT_DS_FIELDS,
    },
    "components": [],
    "columns": [
        {"id": "col-name", "key": "name", "label": "Nome"},
        {"id": "col-sku", "key": "sku", "label": "SKU"},
        {"id": "col-price", "key": "price", "label": "Preço"},
        {"id": "col-grupo", "key": "grupo", "label": "Grupo"},
        {"id": "col-marca", "key": "marca", "label": "Marca"},
        {"id": "col-tipo", "key": "tipo_produto", "label": "Tipo"},
    ],
    "actions": [
        {
            "id": "action-create",
            "type": "create",
            "label": "Novo Produto",
            "navigateTo": "/pages/products_form",
        },
        {
            "id": "action-edit",
            "type": "edit",
            "label": "Editar",
            "navigateTo": "/pages/products_form",
        },
        {"id": "action-delete", "type": "delete", "label": "Excluir"},
    ],
}

# ─── Products Form Page ──────────────────────────────────────────

PRODUCTS_FORM_SCHEMA: dict[str, Any] = {
    "title": "Cadastro de Produto",
    "description": "Crie ou edite os dados do produto",
    "layout": "form",
    "dataSource": {
        "endpoint": "/entities/products",
        "tableName": "products",
        "method": "POST",
        "fields": _PRODUCT_DS_FIELDS,
    },
    "components": [
        {
            "id": "product-form-main",
            "type": "form",
            "components": [
                # ── Seção: Identificação ─────────────────────
                {
                    "id": "section-identificacao",
                    "type": "section",
                    "label": "Identificação",
                    "components": [
                        {"id": "name", "type": "text", "label": "Nome do Produto"},
                        {"id": "sku", "type": "text", "label": "SKU"},
                        {"id": "ean", "type": "text", "label": "EAN / Código de Barras"},
                        {
                            "id": "tipo_produto",
                            "type": "select",
                            "label": "Tipo de Produto",
                            "options": [
                                {"value": "padrao", "label": "Padrão"},
                                {"value": "combustivel", "label": "Combustível"},
                                {"value": "medicamento", "label": "Medicamento"},
                                {"value": "servico", "label": "Serviço"},
                            ],
                        },
                    ],
                },
                # ── Seção: Classificação ─────────────────────
                {
                    "id": "section-classificacao",
                    "type": "section",
                    "label": "Classificação",
                    "components": [
                        {"id": "grupo", "type": "text", "label": "Grupo"},
                        {"id": "subgrupo", "type": "text", "label": "Subgrupo"},
                        {"id": "marca", "type": "text", "label": "Marca"},
                        {
                            "id": "tax_group_id",
                            "type": "select",
                            "label": "Grupo Tributário",
                            "dataSource": "/entities/tax_groups",
                            "options": [],
                        },
                    ],
                },
                # ── Seção: Descrição ─────────────────────────
                {
                    "id": "section-descricao",
                    "type": "section",
                    "label": "Descrição",
                    "components": [
                        {"id": "description", "type": "textarea", "label": "Descrição Comercial"},
                        {"id": "descricao_tecnica", "type": "textarea", "label": "Descrição Técnica"},
                        {
                            "id": "unidade",
                            "type": "select",
                            "label": "Unidade de Medida",
                            "options": [
                                {"value": "UN", "label": "UN — Unidade"},
                                {"value": "KG", "label": "KG — Quilograma"},
                                {"value": "LT", "label": "LT — Litro"},
                                {"value": "MT", "label": "MT — Metro"},
                                {"value": "CX", "label": "CX — Caixa"},
                                {"value": "PC", "label": "PC — Peça"},
                            ],
                        },
                        {"id": "foto_url", "type": "text", "label": "URL da Foto"},
                    ],
                },
                # ── Seção: Preço ─────────────────────────────
                {
                    "id": "section-preco",
                    "type": "section",
                    "label": "Preço",
                    "components": [
                        {"id": "price", "type": "money", "label": "Preço de Venda"},
                        {"id": "custo", "type": "money", "label": "Preço de Custo"},
                        {
                            "id": "markup",
                            "type": "number",
                            "label": "Markup %",
                            "readonly": True,
                            "computed": {
                                "formula": "markup",
                                "deps": ["price", "custo"],
                            },
                        },
                        {
                            "id": "margem",
                            "type": "number",
                            "label": "Margem %",
                            "readonly": True,
                            "computed": {
                                "formula": "margem",
                                "deps": ["price", "custo"],
                            },
                        },
                    ],
                },
                # ── Seção: Fiscal ────────────────────────────
                {
                    "id": "section-fiscal",
                    "type": "section",
                    "label": "Fiscal",
                    "components": [
                        {"id": "ncm_codigo", "type": "text", "label": "NCM"},
                        {"id": "cest_codigo", "type": "text", "label": "CEST"},
                        {"id": "cclass_codigo", "type": "text", "label": "Classificação Tributária"},
                    ],
                },
                # ── Seção: Dados ANP (condicional) ───────────
                {
                    "id": "section-anp",
                    "type": "section",
                    "label": "Dados ANP",
                    "condition": {"field": "tipo_produto", "value": "combustivel"},
                    "components": [
                        {"id": "cod_anp", "type": "text", "label": "Código ANP"},
                        {"id": "desc_anp", "type": "text", "label": "Descrição ANP"},
                        {
                            "id": "uf_cons",
                            "type": "select",
                            "label": "UF Consumo",
                            "options": _UF_OPTIONS,
                        },
                        {"id": "codif", "type": "text", "label": "CODIF"},
                        {"id": "p_bio", "type": "number", "label": "% Biodiesel (pBio)"},
                        {"id": "ad_rem_ibs", "type": "number", "label": "Alíquota Ad Rem IBS"},
                        {"id": "ad_rem_cbs", "type": "number", "label": "Alíquota Ad Rem CBS"},
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
                    "navigateTo": "/pages/products",
                },
            ],
        },
    ],
}

# ─── Sidebar Navigation ─────────────────────────────────────────

SIDEBAR_SCHEMA: dict[str, Any] = {
    "title": "_sidebar",
    "brand": {
        "icon": "A",
        "text": "AutoSystem",
    },
    "sections": [
        {
            "id": "main",
            "label": "Main",
            "items": [
                {
                    "id": "nav-dashboard",
                    "label": "Dashboard",
                    "icon": "dashboard",
                    "path": "/",
                },
            ],
        },
        {
            "id": "cadastros",
            "label": "Cadastros",
            "items": [
                {
                    "id": "nav-products",
                    "label": "Produtos",
                    "icon": "package",
                    "path": "/pages/products",
                },
                {
                    "id": "nav-tax-groups",
                    "label": "Grupo Tributário",
                    "icon": "receipt",
                    "path": "/pages/tax_groups",
                },
                {
                    "id": "nav-operation-natures",
                    "label": "Nat. Operação",
                    "icon": "clipboard",
                    "path": "/pages/operation_natures",
                },
                {
                    "id": "nav-fiscal-rules",
                    "label": "Regras Fiscais",
                    "icon": "settings",
                    "path": "/pages/fiscal_rules",
                },
            ],
        },
        {
            "id": "management",
            "label": "Management",
            "items": [
                {
                    "id": "nav-customers",
                    "label": "Customers",
                    "icon": "users",
                    "path": "/pages/customers",
                },
                {
                    "id": "nav-orders",
                    "label": "Orders",
                    "icon": "clipboard",
                    "path": "/pages/orders",
                },
                {
                    "id": "nav-invoices",
                    "label": "Invoices",
                    "icon": "receipt",
                    "path": "/pages/invoices",
                },
            ],
        },
        {
            "id": "automacao",
            "label": "Automação",
            "items": [
                {
                    "id": "nav-workflows",
                    "label": "Workflows",
                    "icon": "workflow",
                    "path": "/pages/workflows",
                },
            ],
        },
        {
            "id": "settings",
            "label": "Settings",
            "items": [
                {
                    "id": "nav-versions",
                    "label": "Page Versions",
                    "icon": "history",
                    "path": "/pages/versions",
                },
                {
                    "id": "nav-tenants",
                    "label": "Tenants",
                    "icon": "building",
                    "path": "/pages/tenants",
                },
            ],
        },
    ],
    "footer": {
        "text": "AutoSystem v0.1.0",
    },
}

# ─── Header Configuration ───────────────────────────────────────

HEADER_SCHEMA: dict[str, Any] = {
    "title": "_header",
    "search": {
        "enabled": True,
        "placeholder": "Search… (Ctrl+K)",
    },
    "notifications": {
        "enabled": True,
    },
    "user_menu": [
        {"id": "profile", "label": "Profile", "icon": "user"},
        {"id": "settings", "label": "Settings", "icon": "settings"},
        {"id": "divider", "type": "divider"},
        {"id": "logout", "label": "Logout", "icon": "logout", "action": "logout"},
    ],
}

# ─── Dashboard ───────────────────────────────────────────────────

DASHBOARD_SCHEMA: dict[str, Any] = {
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
                    "value": "R$ 45.231,89",
                    "change": "+20.1%",
                    "trend": "up",
                    "icon": "trending_up",
                },
                {
                    "id": "stat-orders",
                    "type": "stat_card",
                    "label": "Orders",
                    "value": "2.350",
                    "change": "+12.5%",
                    "trend": "up",
                    "icon": "shopping_cart",
                },
                {
                    "id": "stat-customers",
                    "type": "stat_card",
                    "label": "Active Customers",
                    "value": "1.247",
                    "change": "+4.3%",
                    "trend": "up",
                    "icon": "people",
                },
                {
                    "id": "stat-products",
                    "type": "stat_card",
                    "label": "Products",
                    "value": "573",
                    "change": "-2.1%",
                    "trend": "down",
                    "icon": "inventory",
                },
            ],
        },
        {
            "id": "activity-feed",
            "type": "activity_feed",
            "label": "Recent Activity",
            "max_items": 8,
            "items": [
                {
                    "id": "act-1",
                    "text": "New order #2350 received",
                    "time": "2 min ago",
                    "type": "order",
                },
                {
                    "id": "act-2",
                    "text": "Product 'Widget Pro' updated",
                    "time": "15 min ago",
                    "type": "product",
                },
                {
                    "id": "act-3",
                    "text": "Customer 'Acme Corp' registered",
                    "time": "1 hour ago",
                    "type": "customer",
                },
                {
                    "id": "act-4",
                    "text": "Invoice #1892 issued",
                    "time": "2 hours ago",
                    "type": "invoice",
                },
                {
                    "id": "act-5",
                    "text": "Schema 'products' v3 published",
                    "time": "3 hours ago",
                    "type": "schema",
                },
            ],
        },
        {
            "id": "quick-actions",
            "type": "quick_actions",
            "label": "Quick Actions",
            "items": [
                {
                    "id": "qa-product",
                    "label": "New Product",
                    "icon": "add_box",
                    "action": {"type": "navigate", "to": "/pages/products"},
                },
                {
                    "id": "qa-order",
                    "label": "New Order",
                    "icon": "receipt_long",
                    "action": {"type": "navigate", "to": "/pages/orders"},
                },
                {
                    "id": "qa-customer",
                    "label": "Add Customer",
                    "icon": "person_add",
                    "action": {"type": "navigate", "to": "/pages/customers"},
                },
                {
                    "id": "qa-report",
                    "label": "View Reports",
                    "icon": "analytics",
                    "action": {"type": "navigate", "to": "/pages/reports"},
                },
            ],
        },
    ],
}
