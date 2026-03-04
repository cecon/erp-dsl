# AutoSystem

Multi-tenant configurable ERP platform with a DSL-driven page engine and AI assistant (Otto).

## Architecture Overview

AutoSystem is composed of **three layers** that work together:

```
┌──────────────────────────────────────────────────────────────┐
│  frontend-platform  (React 19 · Mantine · Port 5175)        │
│  Marketplace / Painel de Gestão da Plataforma                │
│  • Signup, Login, Planos                                     │
│  • Gestão de Projetos, Apps, Empresa                         │
│  • Provisionamento de banco isolado por app                  │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│  backend  (FastAPI · SQLAlchemy · Port 8013)                 │
│  Hexagonal Architecture (Ports & Adapters)                   │
│  • Domain entities, Use Cases, Repository Ports              │
│  • DSL engine, Otto AI, Generic CRUD                         │
│  • Multi-tenant isolation via tenant_id filters              │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│  frontend  (React 18 · Mantine · Port 5174)                  │
│  Aplicativo do Tenant / ERP DSL-Driven                       │
│  • PageRenderer, DashboardRenderer, EnterpriseGrid           │
│  • Otto AI Assistant (chat, forms, skills)                   │
│  • Tema dinâmico configurável por tenant                     │
└──────────────────────────────────────────────────────────────┘
```

### Why two frontends?

| Layer               | Purpose                                                                                             | Analogy                                |
| ------------------- | --------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `frontend-platform` | Admin da plataforma SaaS — onde o usuário cria conta, escolhe plano, cria projetos e configura apps | Vercel Dashboard, Supabase Dashboard   |
| `frontend`          | Aplicativo do tenant — o ERP real, renderizado via DSL, com AI assistant                            | O app deployado, o projeto em produção |

## Quick Start (Docker)

```bash
docker-compose up --build
```

- **Platform (Admin)**: http://localhost:5175
- **App (Tenant ERP)**: http://localhost:5174
- **Backend API**: http://localhost:8013
- **API Docs**: http://localhost:8013/docs

Default tenant credentials: `admin` / `admin`

## Backend Architecture (Hexagonal)

```
backend/src/
  domain/             # Pure Python — entities, value objects, repository protocols
    entities/         # Account, Project, App, PageVersion, Tenant, Workflow
    repositories/     # Abstract Protocol interfaces
    services/         # Domain services (page versioning rules)
  application/        # Use cases & ports (no framework dependencies)
    use_cases/        # SignupUseCase, LoginUseCase, CreateProjectUseCase, ...
    ports/            # Re-exports of domain repository protocols
    otto/             # AI orchestrator (ReAct loop)
    agent/            # Skills system for AI autonomy
  infrastructure/     # Technical implementations
    persistence/      # SQLAlchemy models, repositories, migrations
    security/         # JWT authentication
    config/           # Application settings
  adapters/           # Inbound HTTP adapters (FastAPI routers)
    http/routers/     # Zero business logic — only HTTP translation
    http/schemas/     # Pydantic request/response schemas
```

## Frontend Architecture

```
frontend/src/              # Tenant ERP App
  core/
    layout/                # CoreLayout, Header, Sidebar
    engine/                # PageRenderer, DynamicForm, EnterpriseGrid
  features/otto/           # Otto AI chat widget
  pages/                   # Login
  services/                # Axios API client
  state/                   # Zustand stores (auth, theme)

frontend-platform/src/     # Platform Admin
  pages/
    Login, SignUp           # Authentication
    PlanSelection           # Subscription plans
    dashboard/
      Dashboard             # Project list + sidebar
      ProjectSettings       # Tabs: General, Company, Apps, Database
      tabs/                 # Decomposed tab components
      CreateAppModal        # App creation with LLM config
  services/                 # Axios API client
  state/                    # Zustand stores (auth, dashboard)
```

## Development (without Docker)

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Ensure Postgres is running on localhost:5432
python start.py
```

### Frontend (Tenant ERP)

```bash
cd frontend
pnpm install
pnpm dev
```

### Frontend Platform (Admin)

```bash
cd frontend-platform
pnpm install
pnpm dev
```
