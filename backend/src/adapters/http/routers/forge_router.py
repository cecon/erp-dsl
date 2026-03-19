"""Forge HTTP router — autonomous coding agent proxy.

POST /forge/stream   → SSE proxy to forge-worker (/task + /status/{id})
GET  /forge/health   → health check passthrough to forge-worker
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.adapters.http.dependency_injection import auth_adapter

router = APIRouter()

FORGE_WORKER_URL = os.environ.get("FORGE_WORKER_URL", "http://forge-worker:8020")


# ── Request / Response models ─────────────────────────────────────────


class ForgeStreamRequest(BaseModel):
    """Request body for the Forge SSE streaming endpoint."""
    task: str = Field(..., description="Natural language task for the agent")
    branch_prefix: str = Field("forge", description="Git branch prefix")


# ── Endpoints ─────────────────────────────────────────────────────────


@router.post("/stream")
async def forge_stream(
    body: ForgeStreamRequest,
    token: str = Query(..., description="JWT token for auth"),
) -> StreamingResponse:
    """Submit a coding task to the Forge agent and stream back the logs via SSE.

    Flow:
    1. Verify auth token
    2. POST task to forge-worker → get task_id
    3. Open SSE stream from forge-worker /status/{task_id}
    4. Proxy SSE events back to the browser
    """
    auth = auth_adapter.verify_token(token)
    if auth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return StreamingResponse(
        _forge_sse_generator(body.task, body.branch_prefix),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/health")
async def forge_health(
    token: str = Query(..., description="JWT token for auth"),
) -> dict:
    """Passthrough health check to forge-worker."""
    auth = auth_adapter.verify_token(token)
    if auth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{FORGE_WORKER_URL}/health")
            return resp.json()
    except Exception:
        return {"status": "unavailable", "worker": FORGE_WORKER_URL}


# ── Internal ──────────────────────────────────────────────────────────


async def _forge_sse_generator(task: str, branch_prefix: str) -> AsyncGenerator[str, None]:
    """Submit task to forge-worker and proxy its SSE stream."""
    try:
        # Step 1: Submit task
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{FORGE_WORKER_URL}/task",
                json={"task": task, "branch_prefix": branch_prefix},
            )
            if resp.status_code != 200:
                error = {"type": "error", "message": f"Forge worker error: {resp.text}"}
                yield f"data: {json.dumps(error)}\n\n"
                return
            task_id = resp.json()["task_id"]

        yield f"data: {json.dumps({'type': 'log', 'message': f'🚀 Tarefa aceita. ID: {task_id}'})}\n\n"

        # Step 2: Stream logs
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", f"{FORGE_WORKER_URL}/status/{task_id}") as stream:
                async for line in stream.aiter_lines():
                    if line.startswith("data: "):
                        payload = line[6:]
                        # Forward as-is to browser
                        yield f"data: {payload}\n\n"
                        # Stop when done or error
                        try:
                            event = json.loads(payload)
                            if event.get("type") in ("done", "error"):
                                break
                        except json.JSONDecodeError:
                            pass

    except httpx.ConnectError:
        error = {
            "type": "error",
            "message": "❌ Forge Worker não está disponível. Verifique se o container está rodando.",
        }
        yield f"data: {json.dumps(error)}\n\n"
    except Exception as exc:
        error = {"type": "error", "message": f"❌ Erro inesperado: {exc}"}
        yield f"data: {json.dumps(error)}\n\n"
