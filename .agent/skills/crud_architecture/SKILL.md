---
description: Architectural rules for creating new CRUDs and defining the UX flow (Grid vs Form Pages)
---

# CRUD Architecture Skill

This skill defines the standard rules, components, and user experience flow for all CRUD (Create, Read, Update, Delete) entities in the ERP.

## 1. Visual Hierarchy: Pages vs Modals
The largest architectural distinction in our ERP's UX is the decision between a dedicated Page and a Modal. 

### Primary Entities (Pages)
- **Definition**: Core business entities like Products, Customers, Orders, Invoices.
- **Rule**: Primary entities **MUST NOT** use Modals for their main creation or editing flow. 
- **Flow**: High-volume grids (DynamicMrtGrid). Clicking `+ New` or `Edit` must navigate the user to a dedicated, exclusive form page (e.g., `/pages/products/new` or `/pages/products/edit/123`). This gives the user maximum screen real estate for complex forms.

### Secondary/Nested Entities (Modals)
- **Definition**: Auxiliary data created during the flow of a Primary Entity, such as a Tax Group, Unit of Measure, or Product Category.
- **Rule**: If the user is on the Product Creation Page and needs to select a "Category" that doesn't exist yet, clicking `+ New Category` **MUST** open a Modal over the current form.
- **Goal**: Do not break the user's flow or force them to abandon the primary form they were filling out.

## 2. API & Schema Binding (The DSL)
Since the UI is DSL-driven:
- A new CRUD requires **Backend Changes Only** for the layout.
- The `seed_schemas.py` must define both the Grid view (with its columns) and the Form view (with its fields).
- Action buttons in the Grid schema should use `{"type": "navigate", "to": "/pages/my_entity/new"}` instead of opening a modal.

## 3. Workflow
When tasked with creating a new CRUD for the system, you must strictly follow the `/agent/workflows/create_crud.md` step-by-step guide to ensure no architectural layers or tests are missed.
