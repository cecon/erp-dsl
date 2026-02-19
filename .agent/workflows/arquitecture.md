---
description: Architectural rules and constraints for the multi-tenant ERP/Admin metadata platform
---

# Architecture Workflow

Follow these steps whenever creating, modifying, or reviewing code in this project.

---

## 1. Identify the affected layer

Before writing any code, determine which architectural layer is involved:

- **Domain** — Entities, Value Objects, Domain Services, business invariants
- **Application** — Use Cases that orchestrate domain logic via Ports
- **Infrastructure** — SQLAlchemy models, repository implementations, JWT adapter, external service adapters, DB config
- **Adapters (API)** — FastAPI routers (thin handlers only)
- **Frontend** — React components driven by metadata

---

## 2. Respect dependency direction

Ensure imports flow **inward only**:

```
Adapters → Application → Domain
Infrastructure → Application / Domain
```

**Never** import from outer layers into inner layers. Specifically, the Domain layer must **not** import FastAPI, SQLAlchemy, HTTP, JWT, or any framework.

---

## 3. Keep the Domain layer pure

- No ORM models in domain.
- No framework imports in domain.
- No I/O operations in domain.
- All business rules must live in domain entities, value objects, domain services, or use cases.

---

## 4. Write Use Cases correctly

- Use cases orchestrate domain logic only.
- Use cases depend on **Ports** (interfaces), never on concrete repositories.
- Use cases must not contain HTTP logic.
- Use cases must be testable without infrastructure (mock the ports).

---

## 5. Define Ports as interfaces

- Ports belong to the application or domain layer.
- Infrastructure must implement ports.
- Domain must never reference concrete adapters.

---

## 6. Keep routers thin

- Routers must **never** contain business rules.
- Routers call use cases and return responses — nothing more.

---

## 7. Follow versioning rules

- Published schemas are **immutable** — never update in-place.
- Every modification creates a new version.
- Rollback switches the active version pointer (does not delete history).
- Only one published version per `(page_key + tenant)`.

---

## 8. Follow merge rules

- Merge must be deep merge by key, never by array position.
- Structural arrays must use stable object keys.
- Merge conflicts must not silently overwrite.
- Merge always produces a new version.

---

## 9. Follow multi-tenant rules

- A global version exists for each page.
- Tenant overrides reference `base_version_id`.
- Fallback to global if tenant override does not exist.
- Tenant merge must not auto-upgrade without explicit action.
- Tenant rollback must not delete history.

---

## 10. Follow frontend rules

**Fixed structural elements** (metadata must never alter these):
- Login page, CoreLayout, Header, Sidebar container, Navigation system

**Metadata may control only**:
- Page content, fields, columns, filters, allowed actions (whitelisted)

Rules:
- No dynamic layout injection via schema.
- Component registry must be controlled and finite.

---

## 11. Enforce security constraints

- No `eval` or dynamic function execution.
- All actions must be whitelisted. Only allowed action types: `call_api`, `navigate`, `show_toast`, `run_job`.
- Backend must validate all actions.
- Schema must be validated via strict schema validation.
- Never trust frontend validation alone.

---

## 12. Write tests following layer boundaries

- Domain logic → unit tests without database.
- Use cases → tests with mocked ports.
- Infrastructure → tests may use database.
- No test should require HTTP layer unless explicitly testing an adapter.

---

## 13. Enforce the 300-line file limit

- No file may exceed **300 lines**.
- If a file approaches the limit, split it into smaller, focused modules.
- Each module should have a single clear responsibility.

---

## 14. Apply SOLID principles

- **S – Single Responsibility**: Each class/module has one reason to change.
- **O – Open/Closed**: Extend behavior via new classes or ports, not by modifying existing ones.
- **L – Liskov Substitution**: Subtypes must be substitutable for their base types without breaking behavior.
- **I – Interface Segregation**: Prefer small, focused ports over large, multipurpose interfaces.
- **D – Dependency Inversion**: Depend on abstractions (ports), not on concrete implementations.

---

## 15. Follow DRY and KISS

- **DRY (Don't Repeat Yourself)**: Extract shared logic into helpers, utils, or domain services. Never copy-paste code across modules.
- **KISS (Keep It Simple, Stupid)**: Prefer the simplest solution that meets requirements. Avoid premature abstraction, over-engineering, and unnecessary complexity.

---

## 16. Final checklist before committing

- [ ] No business rules inside routers.
- [ ] No direct SQLAlchemy usage inside use cases.
- [ ] No published schema updated in-place.
- [ ] No dynamic code execution from JSON.
- [ ] No implicit auto-merge without audit.
- [ ] No hardcoded tenant-specific logic inside domain.
- [ ] Dependency direction is correct (inward only).
- [ ] Domain layer has no framework imports.
- [ ] Use cases are testable with mocked ports.
- [ ] Prefer explicit code over magic abstractions.
- [ ] No file exceeds 300 lines.
- [ ] SOLID principles are respected.
- [ ] No duplicated logic across modules (DRY).
- [ ] Solution is as simple as possible (KISS).
