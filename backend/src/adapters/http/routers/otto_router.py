"""Otto HTTP router — universal chat streaming endpoint.

POST /otto/stream → SSE streaming (emits conversational events)
POST /otto/respond/{session_id} → receive interactive response and resume stream
GET  /otto/components → list of available UI components and skills
"""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.http.dependency_injection import get_db, auth_adapter
from src.application.agent.llm_provider import GeminiProvider
from src.application.otto.orchestrator import run_otto_stream
from src.application.otto.sessions import (
    create_session,
    get_session,
    remove_session,
)
from src.infrastructure.persistence.sqlalchemy.agent_models import LLMProviderModel
from src.infrastructure.persistence.sqlalchemy.models import PageVersionModel

router = APIRouter()


# ── Request Model ────────────────────────────────────────────────────


class HistoryMessage(BaseModel):
    """A single message in the conversation history."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class OttoStreamRequest(BaseModel):
    """Request body for the Otto SSE streaming endpoint."""
    input: str = Field(..., description="Current user message")
    page_key: Optional[str] = Field(None, description="Current page key for context")
    history: list[HistoryMessage] = Field(
        default_factory=list,
        description="Previous conversation messages for context continuity",
    )


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


@router.post("/stream")
async def otto_stream(
    body: OttoStreamRequest,
    token: str = Query(..., description="JWT token for auth"),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Otto universal chat — SSE streaming endpoint.

    Accepts POST with JSON body containing:
    - input: current user message
    - page_key: optional page context
    - history: list of previous {role, content} messages

    Emits Server-Sent Events for each orchestrator step.
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
    if body.page_key:
        page_schema = _get_page_schema(db, tenant_id, body.page_key)

    # Convert history to list of dicts for the orchestrator
    history = [{"role": m.role, "content": m.content} for m in body.history]

    # Create a session for interactive message support
    session = create_session()

    async def event_generator():
        try:
            async for event in run_otto_stream(
                user_input=body.input,
                tenant_id=tenant_id,
                llm=llm,
                page_key=body.page_key,
                page_schema=page_schema,
                context={"db": db, "tenant_id": tenant_id},
                history=history,
                session=session,
            ):
                payload = json.dumps(event, ensure_ascii=False, default=str)
                yield f"data: {payload}\n\n"
        finally:
            remove_session(session.id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Interactive response endpoint ────────────────────────────────────


class InteractiveResponse(BaseModel):
    """Body for the interactive response endpoint."""
    value: str = Field(..., description="User's selected value")


@router.post("/respond/{session_id}")
async def respond_interactive(
    session_id: str,
    body: InteractiveResponse,
) -> dict:
    """Receive the user's interactive response and resume the paused stream."""
    session = get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired",
        )
    session.response = body.value
    session.event.set()
    return {"ok": True}


# ── Components list endpoint ─────────────────────────────────────────


# Frontend ComponentRegistry keys — kept in sync manually.
# These are the DSL component types registered in ComponentRegistry.ts.
FRONTEND_COMPONENTS = [
    "text", "number", "money", "date", "datetime",
    "select", "checkbox", "textarea",
    "color_swatch_picker", "theme_switch", "segmented",
    "hidden", "agent:product-enrich",
]


@router.get("/components")
async def list_components(
    token: str = Query(..., description="JWT token for auth"),
    db: Session = Depends(get_db),
) -> dict:
    """Return available UI components and skills.

    The LLM uses this list to decide when it can render a component
    inline in the chat vs. responding with plain text.
    """
    auth = auth_adapter.verify_token(token)
    if auth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    from src.application.agent import skill_registry
    skills = skill_registry.list_skills()

    return {
        "components": FRONTEND_COMPONENTS,
        "skills": [{"name": s["name"], "description": s.get("description", "")} for s in skills],
    }
