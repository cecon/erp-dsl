"""Otto HTTP router — universal chat streaming endpoint.

GET /api/otto/stream → SSE streaming (emits conversational events)
"""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.http.dependency_injection import get_db, auth_adapter
from src.application.agent.llm_provider import GeminiProvider
from src.application.otto.orchestrator import run_otto_stream
from src.infrastructure.persistence.sqlalchemy.agent_models import LLMProviderModel
from src.infrastructure.persistence.sqlalchemy.models import PageVersionModel

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────────


def _get_active_llm(db: Session, tenant_id: str) -> GeminiProvider:
    """Fetch the active LLM provider config for a tenant."""
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
        api_key=row.api_key_encrypted,
        model=row.model,
    )


def _get_page_schema(db: Session, tenant_id: str, page_key: str) -> dict | None:
    """Fetch the page schema for context injection."""
    stmt = (
        select(PageVersionModel)
        .where(
            PageVersionModel.page_key == page_key,
            PageVersionModel.tenant_id == tenant_id,
            PageVersionModel.status == "published",
        )
        .order_by(PageVersionModel.version_number.desc())
        .limit(1)
    )
    row = db.execute(stmt).scalar_one_or_none()
    if row is None:
        return None
    return row.schema_json


# ── Endpoint ─────────────────────────────────────────────────────────


@router.get("/stream")
async def otto_stream(
    input: str = Query(..., description="User message"),
    page_key: Optional[str] = Query(None, description="Current page key for context"),
    token: str = Query(..., description="JWT token (EventSource cannot send headers)"),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Otto universal chat — SSE streaming endpoint.

    Emits Server-Sent Events for each orchestrator step.
    Each event is ``data: {JSON}\\n\\n`` with fields:
    - role: 'assistant' | 'tool' | 'system' | 'form'
    - content: text
    - done: boolean
    - tool_name: string (if role=tool)
    - tool_result: object (if role=tool)
    - schema: array (if role=form)
    - data: object (if role=form)
    """
    auth = auth_adapter.verify_token(token)
    if auth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    tenant_id = auth.tenant_id
    db.info["tenant_id"] = tenant_id

    llm = _get_active_llm(db, tenant_id)

    page_schema = None
    if page_key:
        page_schema = _get_page_schema(db, tenant_id, page_key)

    async def event_generator():
        async for event in run_otto_stream(
            user_input=input,
            tenant_id=tenant_id,
            llm=llm,
            page_key=page_key,
            page_schema=page_schema,
            context={"db": db, "tenant_id": tenant_id},
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
