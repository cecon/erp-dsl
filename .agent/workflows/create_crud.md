---
description: Step-by-step workflow for creating a new CRUD entity in the ERP
---

# Create CRUD Workflow

Follow this multi-phase workflow strictly when creating a new CRUD entity in the system. This ensures the Hexagonal Architecture, DSL Engine, and UX standards are upheld without missing steps.

## Phase 1: Domain & Infrastructure (Backend)
1. **Domain Model**: Create the core entity class in `backend/src/domain/entities/`.
2. **Port**: Define the Repository Interface in `backend/src/application/ports/`.
3. **Adapter (Persistence)**:
   - Create the SQLAlchemy Model in `backend/src/infrastructure/persistence/sqlalchemy/models.py`.
   - Create the Alembic Migration script to update the database.
   - Implement the Repository Interface using `GenericCrudRepository` or a custom SqlAlchemy class.

## Phase 2: Application Business Logic (Backend)
4. **Use Cases**: Create the specific Use Cases (if any custom logic like calculations or external API calls are needed) in `backend/src/application/use_cases/`.
5. **Schemas**: Define Pydantic models for HTTP requests/responses in the Router folder.

## Phase 3: API & Routing (Backend)
6. **Router**: Create the FastAPI router.
   - For standard entities, mount the `GenericCrudRouter`.
   - Ensure the router is registered in `backend/src/adapters/http/main.py`.

## Phase 4: UI Metadata (The DSL Engine)
7. **Seed Schemas**: Go to `backend/src/infrastructure/persistence/seed_schemas.py` (or the respective seed file).
   - Create the `*_PAGE_SCHEMA` defining the columns for the Grid (`DynamicMrtGrid`).
   - Define the `components` array for the Form fields.
   - **CRITICAL UX RULE**: Configure the "Create" and "Edit" actions to navigate to a dedicated form page, NOT a modal, if this is a Primary Entity.
8. **Sidebar**: Add the new entity to the `SIDEBAR_SCHEMA` so users can navigate to it.

## Phase 5: Verification
9. **Tests**: Ensure backend unit/integration tests cover the router and any custom Use Cases.
10. **Linter**: Run `pyrefly check` on the backend to guarantee code quality.
11. **UI Check**: Open the frontend and verify that the Grid renders the correct columns and the "New" button properly navigates to the dedicated Form page.
