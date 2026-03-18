"""Forge Worker — FastAPI service for the autonomous coding agent.

Endpoints:
  POST /task            — submit a coding task (returns task_id + SSE logs)
  GET  /status/{id}     — SSE stream of task logs
  GET  /health          — health check
"""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent import ForgeAgent

app = FastAPI(title="Forge Worker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task store: {task_id: {"status": str, "logs": list[str], "pr_url": str|None}}
_tasks: dict[str, dict] = {}
_task_queues: dict[str, asyncio.Queue] = {}


# ── Models ────────────────────────────────────────────────────────────

class TaskRequest(BaseModel):
    task: str = Field(..., description="Natural language task description")
    branch_prefix: str = Field("forge", description="Git branch prefix")


class TaskResponse(BaseModel):
    task_id: str
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "forge-worker"}


@app.post("/task", response_model=TaskResponse)
async def submit_task(body: TaskRequest) -> TaskResponse:
    """Submit a new coding task. Returns a task_id to follow via /status/{id}."""
    task_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()

    _tasks[task_id] = {"status": "pending", "logs": [], "pr_url": None}
    _task_queues[task_id] = queue

    # Run agent in background
    asyncio.create_task(_run_agent(task_id, body.task, body.branch_prefix, queue))

    return TaskResponse(task_id=task_id, message="Task accepted. Follow via /status/" + task_id)


@app.get("/status/{task_id}")
async def task_status(task_id: str) -> StreamingResponse:
    """SSE stream of task logs. Closes when task completes or fails."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    return StreamingResponse(
        _sse_generator(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Internal ──────────────────────────────────────────────────────────

async def _sse_generator(task_id: str) -> AsyncGenerator[str, None]:
    """Yield SSE events from the task queue."""
    queue = _task_queues.get(task_id)
    if queue is None:
        # Task already finished — replay logs
        task = _tasks[task_id]
        for log in task["logs"]:
            yield f"data: {json.dumps({'type': 'log', 'message': log})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'status': task['status'], 'pr_url': task['pr_url']})}\n\n"
        return

    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=30.0)
            yield f"data: {json.dumps(event)}\n\n"
            if event.get("type") in ("done", "error"):
                break
        except asyncio.TimeoutError:
            # Heartbeat
            yield "data: {\"type\": \"heartbeat\"}\n\n"


async def _run_agent(task_id: str, task: str, branch_prefix: str, queue: asyncio.Queue) -> None:
    """Run the ForgeAgent and pipe logs to the SSE queue."""
    _tasks[task_id]["status"] = "running"

    async def emit(msg: str) -> None:
        event = {"type": "log", "message": msg}
        _tasks[task_id]["logs"].append(msg)
        await queue.put(event)

    try:
        github_token = os.environ["GITHUB_TOKEN"]
        github_repo = os.environ["GITHUB_REPO"]
        base_branch = os.environ.get("GITHUB_BASE_BRANCH", "main")

        agent = ForgeAgent(
            github_token=github_token,
            github_repo=github_repo,
            base_branch=base_branch,
            workspace_dir="/workspace",
            emit=emit,
        )

        pr_url = await agent.run(task=task, branch_prefix=branch_prefix)
        _tasks[task_id]["status"] = "done"
        _tasks[task_id]["pr_url"] = pr_url
        await queue.put({"type": "done", "status": "done", "pr_url": pr_url})

    except Exception as exc:
        error_msg = f"[ERRO] {exc}"
        _tasks[task_id]["status"] = "error"
        _tasks[task_id]["logs"].append(error_msg)
        await queue.put({"type": "error", "message": error_msg})

    finally:
        # Remove queue so replays use logs store
        _task_queues.pop(task_id, None)
