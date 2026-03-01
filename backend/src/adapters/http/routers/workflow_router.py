"""Workflow HTTP router — CRUD + SSE execution endpoints.

POST /workflows           → create
GET  /workflows           → list (tenant-scoped)
GET  /workflows/{id}      → get single
PUT  /workflows/{id}      → update
POST /workflows/{id}/execute  → SSE streaming execution
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.adapters.http.dependency_injection import (
    get_db,
    get_tenant_db,
    auth_adapter,
)
from src.application.ports.auth_port import AuthContext
from src.application.workflows.executor import execute_workflow
from src.application.workflows.workflow_use_cases import (
    CreateWorkflowUseCase,
    GetWorkflowUseCase,
    ListWorkflowsUseCase,
    UpdateWorkflowUseCase,
)
from src.domain.entities.workflow import Workflow
from src.infrastructure.persistence.sqlalchemy.workflow_repository_impl import (
    SqlAlchemyWorkflowRepository,
)

router = APIRouter()


# ── Request / Response models ────────────────────────────────────


class WorkflowStepIn(BaseModel):
    skill: str
    params: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False
    on_error: str = "stop"


class WorkflowCreateIn(BaseModel):
    name: str
    command: str
    description: str = ""
    steps: list[WorkflowStepIn] = Field(default_factory=list)
    status: str = "draft"


class WorkflowUpdateIn(BaseModel):
    name: str | None = None
    command: str | None = None
    description: str | None = None
    steps: list[WorkflowStepIn] | None = None
    status: str | None = None


def _serialize(w: Workflow) -> dict:
    return {
        "id": w.id,
        "tenant_id": w.tenant_id,
        "name": w.name,
        "command": w.command,
        "description": w.description,
        "steps": [
            {
                "skill": s.skill,
                "params": s.params,
                "requires_confirmation": s.requires_confirmation,
                "on_error": s.on_error,
            }
            for s in w.steps
        ],
        "status": w.status.value,
        "version": w.version,
    }


# ── CRUD endpoints ──────────────────────────────────────────────


@router.get("")
def list_workflows(
    db: Session = Depends(get_tenant_db),
) -> dict:
    """List all workflows for the current tenant."""
    tenant_id = db.info["tenant_id"]
    repo = SqlAlchemyWorkflowRepository(db)
    uc = ListWorkflowsUseCase(repo)
    items = uc.execute(tenant_id)
    return {
        "items": [_serialize(w) for w in items],
        "total": len(items),
    }


@router.get("/{workflow_id}")
def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_tenant_db),
) -> dict:
    """Get a single workflow by ID."""
    tenant_id = db.info["tenant_id"]
    repo = SqlAlchemyWorkflowRepository(db)
    uc = GetWorkflowUseCase(repo)
    w = uc.execute(workflow_id, tenant_id)
    if w is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )
    return _serialize(w)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_workflow(
    body: WorkflowCreateIn,
    db: Session = Depends(get_tenant_db),
) -> dict:
    """Create a new workflow."""
    tenant_id = db.info["tenant_id"]
    repo = SqlAlchemyWorkflowRepository(db)
    uc = CreateWorkflowUseCase(repo)
    try:
        w = uc.execute(body.model_dump(), tenant_id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A workflow with command '{body.command}' "
                f"already exists for this tenant."
            ),
        )
    return _serialize(w)


@router.put("/{workflow_id}")
def update_workflow(
    workflow_id: str,
    body: WorkflowUpdateIn,
    db: Session = Depends(get_tenant_db),
) -> dict:
    """Update an existing workflow."""
    tenant_id = db.info["tenant_id"]
    repo = SqlAlchemyWorkflowRepository(db)
    uc = UpdateWorkflowUseCase(repo)
    data = body.model_dump(exclude_none=True)
    if "steps" in data:
        data["steps"] = [s.model_dump() for s in body.steps]  # type: ignore
    try:
        w = uc.execute(workflow_id, data, tenant_id)
        db.commit()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate command for this tenant.",
        )
    return _serialize(w)


# ── Execution endpoint (SSE) ────────────────────────────────────


@router.post("/{workflow_id}/execute")
async def execute_workflow_endpoint(
    workflow_id: str,
    sandbox: bool = Query(False),
    token: str = Query(..., description="JWT token for auth"),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Execute a workflow via SSE streaming.

    Uses query-param auth (same pattern as Otto) because SSE
    via fetch doesn't support Authorization headers consistently.
    """
    auth = auth_adapter.verify_token(token)
    if auth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    tenant_id = auth.tenant_id
    db.info["tenant_id"] = tenant_id

    repo = SqlAlchemyWorkflowRepository(db)
    w = repo.get_by_id(workflow_id, tenant_id)
    if w is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found.",
        )

    context = {"db": db, "tenant_id": tenant_id}

    async def event_generator():
        async for event in execute_workflow(w, context, sandbox=sandbox):
            payload = json.dumps(event, ensure_ascii=False, default=str)
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
