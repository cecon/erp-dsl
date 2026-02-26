---
description: Architectural rules and conventions for the ERP Backend (FastAPI, SQLAlchemy, Hexagonal Architecture)
---

# Backend Hexagonal Architecture Skill

This project follows a strict Hexagonal Architecture (Ports and Adapters) combined with Domain-Driven Design (DDD) principles to ensure the backend is highly decoupled, testable, and maintainable.

## 1. Core Principles
- **Separation of Concerns**: Business logic must NEVER be mixed with HTTP routing or database specific mappings.
- **Dependency Inversion**: High-level modules (Use Cases) should not depend on low-level modules (Adapters like DB or External APIs). Both should depend on abstractions (Ports/Interfaces).

## 2. Directory Structure (`backend/src`)

### `domain/`
The absolute core of the application.
- Contains **Entities** and **Aggregates** (pure Python classes, NO SQLAlchemy dependencies).
- Contains **Domain Exceptions**.
- **Rule**: Code in the `domain` folder cannot import anything from `application`, `adapters`, or `infrastructure`.

### `application/`
The orchestrator layer.
- **Use Cases**: Contains the business workflows. A Use Case executes a specific action (e.g., `CreateProductUseCase`, `CalculateTaxesUseCase`).
- **Ports (Interfaces)**: Defines abstract base classes (ABCs) that describe what the application needs from the outside world (e.g., `ProductRepositoryInterface`, `SefazAdapterInterface`).
- **Rule**: Use Cases interact with Ports. They do not know if the database is Postgres or MongoDB.

### `adapters/`
The translation layer to the outside world.
- **HTTP (Primary/Driving Adapters)**: Contains all FastAPI Routers, Dependency Injection setup, and Request/Response Schemas (Pydantic). 
  - **Rule**: A Router's ONLY job is to validate the HTTP request using Pydantic, call the appropriate Use Case, and format the HTTP response. Zero business logic.
- **External (Secondary/Driven Adapters)**: Implementations of Ports that call external APIs (e.g., SEFAZ, BrasilAPI, LLMs).

### `infrastructure/`
The technical implementation layer.
- **Persistence**: SQLAlchemy models (`models.py`), Alembic migrations, Database connection setup, and Repository implementations that implement the domain Ports.
- **Rule**: SQLAlchemy models only exist here. They must be mapped back to Domain Entities before returning to the Application layer.

## 3. Workflow for a New Feature (e.g., CRUD for Fornecedores)
1. **Domain**: Define the `Fornecedor` entity.
2. **Application (Port)**: Create `FornecedorRepositoryInterface`.
3. **Application (Use Case)**: Create `CreateFornecedorUseCase` which receives the repository interface.
4. **Infrastructure (Adapter)**: Create the SQLAlchemy model and `SqlAlchemyFornecedorRepository` that implements the interface.
5. **Adapters (HTTP)**: Create the FastAPI router for `/fornecedores`, inject the repository into the Use Case, and execute it.

## 4. Generic CRUD
For standard DSL-driven CRUDs, we use the `GenericCrudRouter` and `GenericCrudRepository`. Only deviate from the generic implementation if the entity requires significant custom use cases or business rules upon creation/update.
