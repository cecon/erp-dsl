# AutoSystem

Multi-tenant configurable platform with page versioning engine.

## Quick Start (Docker)

```bash
docker-compose up --build
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

Default credentials: `admin` / `admin`

## Architecture

```
backend/
  src/
    domain/        # Pure Python — entities, value objects, services
    application/   # Use cases & ports (no framework dependencies)
    infrastructure/# SQLAlchemy, JWT, settings
    adapters/      # FastAPI (HTTP adapter only)

frontend/
  src/
    core/
      layout/      # CoreLayout, Header, Sidebar
      engine/      # PageRenderer, DynamicForm, EnterpriseGrid
    pages/         # Login
    services/      # Axios API client
    state/         # Zustand auth store
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

### Frontend
```bash
cd frontend
pnpm install
pnpm dev
```
