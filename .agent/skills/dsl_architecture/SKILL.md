---
description: Architectural rules and conventions for the ERP's Domain Specific Language (DSL) UI Engine
---

# DSL Engine Architecture Skill

This project uses a metadata-driven UI approach (Domain Specific Language - DSL) to render pages dynamically. This skill defines how the DSL Engine operates, where components are located, and how registries function to ensure long-term architectural consistency.

## 1. Core Philosophy: Backend-Driven UI
The fundamental rule of this ERP is that **the Frontend is dumb, and the Backend is smart.** 
The Frontend (`PageRenderer`, `DashboardRenderer`) should have close to ZERO hardcoded business logic regarding what fields to show, what columns exist in a grid, or what endpoints to call. 

All this metadata is provided by the Backend via the JSON DSL Schema (`GET /api/pages/{pageKey}`).

## 2. Directory Structure & Registries

### Frontend Engine (`frontend/src/core/engine`)
This folder contains the core machinery that interprets the JSON Schema and renders the UI.
- `PageRenderer.tsx`: The main skeleton. It fetches the schema by `pageKey` and orchestrates the layout (Header, Grid, Forms, Modals).
- `DashboardRenderer.tsx`: Specialized engine for analytics layouts and widget composition.

### Component Registry (`frontend/src/core/registry`)
When the schema says `{"type": "money_input"}`, the Frontend needs to know which React component to render. **Do not hardcode massive switch/case statements in the renderers.**
- Use a central **Component Registry** (e.g., `ComponentRegistry.ts`).
- This registry maps string identifiers (`"money_input"`) to lazy-loaded or directly imported React Components.
- When creating a new UI component, you **MUST** register it in the Component Registry so the DSL Engine can use it.

### UI Components (`frontend/src/components`)
- `components/grid`: Data Grids and Tables (e.g., `DynamicMrtGrid.tsx`). Must be schema-aware.
- `components/form`: Input fields and dynamic forms.
- `components/layout`: Structural elements (Sidebar, Header).

## 3. How to Create or Edit a CRUD Entity

**NEVER create a new `frontend/src/pages/MyEntity.tsx`.**

To add a new CRUD screen (e.g., "Fornecedores"):
1. **Backend Schema**: Create the JSON metadata outlining the Grid columns, Form fields, and API endpoints inside the Backend's schema seeds (e.g., `seed_schemas.py`).
2. **Backend Sidebar**: Add the new route to the `_sidebar` schema pointing to `/pages/fornecedores`.
3. **Backend API**: Create the standard REST API endpoints (GET, POST, PUT, DELETE) in the backend routers.
4. **Result**: The Frontend's `PageRenderer` will automatically construct the Fornecedores page dynamically.

## 4. Modifying Existing Components
If you need to change how a specific input looks (e.g., changing a date picker):
- Go to the specific component in `frontend/src/components/`.
- Make the change. This change will instantly reflect across **all** DSL-rendered pages that use that component. This is the power of the central Component Registry.

## 5. Summary of Rules
- **No hardcoded routes**: Pages must be driven by `PageRenderer` and backend schemas.
- **Component registration**: All new interactive components requested by the schema must be added to the registry.
- **Generic properties**: Components must accept generic generic props (`value`, `onChange`, `schemaConfig`) so they can be reused purely based on backend definitions.
