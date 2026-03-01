"""Otto Orchestrator — generic ReAct loop for the universal chat.

Reuses the same pattern as the product-enrich agent but with:
- Generic system prompt (context-aware per page)
- Message-style output for conversational UX
- Streaming via async generator for SSE
- Form request support for structured user input
- Conversation history for multi-turn context

No external agent frameworks — pure Python.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import AsyncGenerator

from src.application.agent import skill_registry
from src.application.agent.llm_provider import LLMProvider
from src.application.otto.prompts.otto_system import build_otto_system_prompt
from src.application.otto.sessions import OttoSession, get_session
from src.application.workflows.executor import execute_workflow
from src.infrastructure.persistence.sqlalchemy.workflow_repository_impl import (
    SqlAlchemyWorkflowRepository,
)

# Timeout (seconds) waiting for user interactive response
INTERACTIVE_TIMEOUT = 60.0

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 10


def _extract_json(text: str) -> dict:
    """Robustly extract a JSON object from an LLM response.

    Strategy:
      1. Try ``json.loads`` on the raw text (after stripping markdown fences).
      2. If that fails, use a regex to find the first ``{...}`` block and parse it.
      3. If still no valid JSON, wrap the raw text as a plain message fallback.

    This ensures the orchestrator *never* breaks due to the LLM mixing
    explanatory prose with its JSON payload.
    """
    # Step 0 — strip markdown code fences
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[-1]
    if clean.endswith("```"):
        clean = clean.rsplit("```", 1)[0]
    clean = clean.strip()

    # Step 1 — direct parse
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Step 2 — regex: extract first top-level {...} block
    match = re.search(r"\{.*\}", clean, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            logger.warning(
                "Otto: regex-extracted block is not valid JSON: %s",
                match.group()[:200],
            )

    # Step 3 — fallback: treat entire text as a plain assistant message
    logger.warning(
        "Otto: could not extract JSON, falling back to text message: %s",
        text[:200],
    )
    return {"message": text.strip()}


async def _try_workflow_command(
    user_input: str,
    context: dict,
) -> AsyncGenerator[dict, None] | None:
    """If *user_input* starts with ``/``, try to find a matching workflow.

    Returns an async generator of SSE events if a workflow is found,
    or ``None`` to fall through to the normal LLM path.

    Text after the command (e.g. ``/cmd arg1 arg2``) is extracted and
    injected into the context as ``user_input`` so the executor can
    resolve ``{input}`` placeholders in step parameters.
    """
    if not user_input.startswith("/"):
        return None

    db = context.get("db")
    tenant_id = context.get("tenant_id")
    if db is None or not tenant_id:
        return None

    parts = user_input.split(maxsplit=1)
    command = parts[0]  # e.g. "/cadastrar-produto"
    args_text = parts[1] if len(parts) > 1 else ""

    repo = SqlAlchemyWorkflowRepository(db)
    workflow = repo.get_by_command(command, tenant_id)

    if workflow is None:
        return None

    # Inject the text after the command into context
    ctx_with_input = {**context, "user_input": args_text}
    return execute_workflow(workflow, ctx_with_input)


async def run_otto_stream(
    user_input: str,
    tenant_id: str,
    llm: LLMProvider,
    page_key: str | None = None,
    page_schema: dict | None = None,
    context: dict | None = None,
    history: list[dict] | None = None,
    session: OttoSession | None = None,
) -> AsyncGenerator[dict, None]:
    """Run the Otto ReAct loop as an async generator for SSE streaming.

    Yields dicts suitable for SSE ``data:`` events.
    Each event has ``role``, ``content``, and ``done`` fields.

    Args:
        history: Previous conversation messages [{role, content}] for
                 multi-turn context. Roles should be 'user' or 'assistant'
                 (mapped to 'model' for Gemini).
    """
    context = context or {}
    history = history or []

    # ── Workflow command interception ────────────────────────
    wf_gen = await _try_workflow_command(user_input, context)
    if wf_gen is not None:
        async for event in wf_gen:
            yield event
        return

    # ── Normal LLM path ─────────────────────────────────────
    skills = skill_registry.list_skills()
    system_prompt = build_otto_system_prompt(
        skills=skills,
        page_key=page_key,
        page_schema=page_schema,
    )

    # Build messages: system + history + current user input
    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
    ]

    # Append conversation history (map 'assistant' → 'model' for Gemini)
    for msg in history:
        role = msg.get("role", "user")
        if role == "assistant":
            role = "model"
        messages.append({"role": role, "content": msg.get("content", "")})

    # Append current user message
    messages.append({"role": "user", "content": user_input})

    for iteration in range(1, MAX_ITERATIONS + 1):
        # ── Call LLM ────────────────────────────────────────────
        try:
            raw_response = await llm.complete(messages)
        except Exception as exc:
            logger.error("Otto LLM call failed at iteration %d: %s", iteration, exc)
            yield {
                "role": "system",
                "content": f"Erro na chamada ao LLM: {exc}",
                "done": True,
            }
            return

        # ── Parse JSON (robust — never fails) ────────────────────
        parsed = _extract_json(raw_response)

        # ── Handle interactive request ────────────────────────────
        if parsed.get("interactive") and session is not None:
            idata = parsed["interactive"]
            itype = idata.get("type", "confirm")

            event_payload: dict = {
                "role": "interactive",
                "type": itype,
                "session_id": session.id,
                "question": idata.get("question", ""),
                "done": False,
            }
            # Copy type-specific fields
            if itype == "confirm":
                event_payload["confirm_label"] = idata.get("confirm_label", "Confirmar")
                event_payload["cancel_label"] = idata.get("cancel_label", "Cancelar")
            elif itype == "choice":
                event_payload["options"] = idata.get("options", [])
            elif itype == "image-picker":
                event_payload["images"] = idata.get("images", [])
            elif itype == "carousel":
                event_payload["items"] = idata.get("items", [])

            yield event_payload

            # Pause — wait for the frontend to POST /otto/respond/{session_id}
            session.event.clear()
            try:
                await asyncio.wait_for(
                    session.event.wait(), timeout=INTERACTIVE_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "Otto interactive timeout for session %s", session.id
                )
                yield {
                    "role": "system",
                    "content": "Tempo esgotado. Reinicie a conversa.",
                    "done": True,
                }
                return

            user_choice = session.response or ""
            session.response = None  # reset for potential next interactive

            # Feed user choice back into LLM conversation
            messages.append({"role": "model", "content": raw_response})
            messages.append({
                "role": "user",
                "content": f"[USER_CHOICE] {user_choice}",
            })
            continue

        # ── Handle form request ──────────────────────────────────
        if parsed.get("form"):
            yield {
                "role": "form",
                "content": parsed.get("message", "Preencha os campos:"),
                "schema": parsed.get("schema", []),
                "data": parsed.get("data", {}),
                "done": False,
            }
            return

        # ── Handle component render ─────────────────────────────
        if parsed.get("component"):
            yield {
                "role": "component",
                "component": parsed["component"],
                "props": parsed.get("props", {}),
                "content": parsed.get("message", ""),
                "done": parsed.get("done", False),
            }
            if parsed.get("done"):
                return
            messages.append({"role": "model", "content": raw_response})
            continue

        # ── Handle "done" ───────────────────────────────────────
        if parsed.get("done"):
            yield {
                "role": "assistant",
                "content": parsed.get("message", ""),
                "draft": parsed.get("draft"),
                "done": True,
            }
            return

        # ── Handle message (no action) ──────────────────────────
        if "message" in parsed and "action" not in parsed:
            yield {
                "role": "assistant",
                "content": parsed["message"],
                "done": True,
            }
            return

        # ── Handle skill action ─────────────────────────────────
        action = parsed.get("action")
        params = parsed.get("params", {})

        if not action:
            messages.append({"role": "model", "content": raw_response})
            messages.append({
                "role": "user",
                "content": (
                    'Your JSON must have either {"message": "..."}, '
                    '{"action": "...", "params": {...}}, '
                    '{"form": true, "schema": [...], "data": {...}}, '
                    'or {"done": true, "message": "...", "draft": {...}}.'
                ),
            })
            continue

        # Emit "thinking" event
        yield {
            "role": "assistant",
            "content": parsed.get("message", f"Executando {action}…"),
            "done": False,
        }

        skill_fn = skill_registry.get(action)
        if skill_fn is None:
            available = [s["name"] for s in skills]
            messages.append({"role": "model", "content": raw_response})
            messages.append({
                "role": "user",
                "content": f"Skill '{action}' not found. Available: {available}",
            })
            yield {
                "role": "tool",
                "tool_name": action,
                "content": f"Skill '{action}' não encontrada.",
                "done": False,
            }
            continue

        # Execute skill
        try:
            skill_result = await skill_fn(params, context)
        except Exception as exc:
            logger.error("Otto skill '%s' failed: %s", action, exc)
            skill_result = {"error": str(exc)}

        # Emit tool result event
        yield {
            "role": "tool",
            "tool_name": action,
            "tool_result": skill_result,
            "content": json.dumps(skill_result, ensure_ascii=False, default=str)[:500],
            "done": False,
        }

        # Feed result back to LLM
        messages.append({"role": "model", "content": raw_response})
        messages.append({
            "role": "user",
            "content": (
                f"Skill '{action}' returned:\n"
                f"```json\n{json.dumps(skill_result, ensure_ascii=False, default=str)}\n```\n"
                "Based on this result, decide your next action or answer the user."
            ),
        })

    # Exhausted iterations
    yield {
        "role": "system",
        "content": f"Limite de iterações ({MAX_ITERATIONS}) atingido.",
        "done": True,
    }
