"""Agent HTTP router — product enrichment endpoints.

POST /api/agent/product-enrich    → batch mode (returns full AgentResult)
GET  /api/agent/product-enrich/stream → SSE streaming (emits events per step)
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.http.dependency_injection import get_current_user, get_tenant_db
from src.application.agent.llm_provider import GeminiProvider
from src.application.agent.orchestrator import run_agent, run_agent_stream
from src.application.agent.prompts.product_enrich import build_system_prompt
from src.application.agent import skill_registry
from src.application.ports.auth_port import AuthContext
from src.infrastructure.persistence.sqlalchemy.agent_models import LLMProviderModel
from src.infrastructure.persistence.sqlalchemy.models import PageVersionModel

router = APIRouter()


# ── Request / Response schemas ───────────────────────────────────────


class ProductEnrichRequest(BaseModel):
    user_input: str


class StepResponse(BaseModel):
    iteration: int
    type: str
    action: str | None = None
    params: dict | None = None
    result: dict | None = None


class ProductEnrichResponse(BaseModel):
    draft: dict | None = None
    steps: list[dict] = []
    finished: bool = False
    iterations: int = 0
    error: str | None = None


# ── Helpers ──────────────────────────────────────────────────────────


def _get_active_llm(db: Session, tenant_id: str) -> GeminiProvider:
    """Fetch the active LLM provider config for a tenant and build a GeminiProvider."""
    stmt = (
        select(LLMProviderModel)
        .where(
            LLMProviderModel.tenant_id == tenant_id,
            LLMProviderModel.is_active == True,  # noqa: E712
        )
        .limit(1)
    )
    row = db.execute(stmt).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No active LLM provider configured for this tenant. "
                "Please add a record to the 'llm_providers' table."
            ),
        )
    return GeminiProvider(
        api_key=row.api_key_encrypted,  # TODO: decrypt in the future
        model=row.model,
    )


def _get_tenant_schema(db: Session, tenant_id: str) -> dict:
    """Fetch tenant-specific product field extensions from page_versions.

    Looks for a published PageVersion with page_key='product_field_extensions'
    and scope='tenant'. Falls back to an empty dict.
    """
    stmt = (
        select(PageVersionModel)
        .where(
            PageVersionModel.page_key == "product_field_extensions",
            PageVersionModel.scope == "tenant",
            PageVersionModel.tenant_id == tenant_id,
            PageVersionModel.status == "published",
        )
        .order_by(PageVersionModel.version_number.desc())
        .limit(1)
    )
    row = db.execute(stmt).scalar_one_or_none()
    if row is None:
        return {}
    return row.schema_json or {}


# ── Endpoints ────────────────────────────────────────────────────────


@router.post("/product-enrich", response_model=ProductEnrichResponse)
async def product_enrich(
    body: ProductEnrichRequest,
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> ProductEnrichResponse:
    """Enrich product data using the AI agent (batch mode).

    Resolves the active LLM provider for the tenant, fetches tenant-specific
    product schema extensions, and runs the ReAct orchestrator.
    """
    tenant_id = auth.tenant_id

    llm = _get_active_llm(db, tenant_id)
    tenant_schema = _get_tenant_schema(db, tenant_id)

    # Build the specialized product enrichment prompt
    skills = skill_registry.list_skills()
    system_prompt = build_system_prompt(skills, tenant_schema)

    result = await run_agent(
        user_input=body.user_input,
        tenant_id=tenant_id,
        tenant_schema=tenant_schema,
        llm=llm,
        context={"db": db, "tenant_id": tenant_id},
        system_prompt=system_prompt,
    )

    return ProductEnrichResponse(
        draft=result.draft,
        steps=result.steps,
        finished=result.finished,
        iterations=result.iterations,
        error=result.error,
    )


@router.get("/product-enrich/stream")
async def product_enrich_stream(
    user_input: str = Query(..., description="Natural-language product description or EAN"),
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
) -> StreamingResponse:
    """Enrich product data using the AI agent (SSE streaming mode).

    Emits Server-Sent Events for each orchestrator step.
    Each event is ``data: {JSON}\\n\\n``.
    Final event contains ``done: true`` with the product draft.
    """
    tenant_id = auth.tenant_id

    llm = _get_active_llm(db, tenant_id)
    tenant_schema = _get_tenant_schema(db, tenant_id)

    skills = skill_registry.list_skills()
    system_prompt = build_system_prompt(skills, tenant_schema)

    async def event_generator():
        async for event in run_agent_stream(
            user_input=user_input,
            tenant_id=tenant_id,
            tenant_schema=tenant_schema,
            llm=llm,
            context={"db": db, "tenant_id": tenant_id},
            system_prompt=system_prompt,
        ):
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
