"""DSL schema definitions for seed data.

Each schema is a page_key that the frontend fetches via GET /api/pages/{key}.
Layout schemas use underscore prefix (_sidebar, _header) to distinguish
them from content pages (products, dashboard).
"""

from __future__ import annotations

from typing import Any

# ─── Products CRUD Page ──────────────────────────────────────────

PRODUCTS_PAGE_SCHEMA: dict[str, Any] = {
    "title": "Products",
    "description": "CRUD page for product management",
    "layout": "grid",
    "dataSource": {
        "endpoint": "/entities/products",
        "tableName": "products",
        "method": "GET",
        "paginationParams": {"offset": "offset", "limit": "limit"},
        "fields": [
            {"id": "name", "dbType": "string", "required": True},
            {"id": "price", "dbType": "decimal", "required": True},
            {
                "id": "sku",
                "dbType": "string",
                "required": False,
                "transforms": [
                    {"fn": "uppercase", "on": "request"},
                ],
            },
        ],
    },
    "components": [
        {
            "id": "product-form",
            "type": "form",
            "components": [
                {"id": "name", "type": "text", "label": "Product Name"},
                {"id": "price", "type": "money", "label": "Price"},
                {"id": "sku", "type": "text", "label": "SKU"},
            ],
        },
    ],
    "columns": [
        {"id": "col-name", "key": "name", "label": "Name"},
        {"id": "col-price", "key": "price", "label": "Price"},
        {"id": "col-sku", "key": "sku", "label": "SKU"},
    ],
    "actions": [
        {"id": "action-agent-enrich", "type": "agent", "label": "Novo com IA", "agent": "product-enrich"},
        {"id": "action-create", "type": "create", "label": "New Product"},
        {"id": "action-edit", "type": "edit", "label": "Edit"},
        {"id": "action-delete", "type": "delete", "label": "Delete"},
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
