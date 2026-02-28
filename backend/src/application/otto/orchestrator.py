"""Otto Orchestrator — generic ReAct loop for the universal chat.

Reuses the same pattern as the product-enrich agent but with:
- Generic system prompt (context-aware per page)
- Message-style output for conversational UX
- Streaming via async generator for SSE
- Form request support for structured user input

No external agent frameworks — pure Python.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from src.application.agent import skill_registry
from src.application.agent.llm_provider import LLMProvider
from src.application.otto.prompts.otto_system import build_otto_system_prompt

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 10


def _parse_llm_response(raw_response: str) -> dict | None:
    """Parse LLM response, stripping markdown fences if present."""
    clean = raw_response.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[-1]
    if clean.endswith("```"):
        clean = clean.rsplit("```", 1)[0]
    clean = clean.strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


async def run_otto_stream(
    user_input: str,
    tenant_id: str,
    llm: LLMProvider,
    page_key: str | None = None,
    page_schema: dict | None = None,
    context: dict | None = None,
) -> AsyncGenerator[dict, None]:
    """Run the Otto ReAct loop as an async generator for SSE streaming.

    Yields dicts suitable for SSE ``data:`` events.
    Each event has ``role``, ``content``, and ``done`` fields.
    """
    context = context or {}

    skills = skill_registry.list_skills()
    system_prompt = build_otto_system_prompt(
        skills=skills,
        page_key=page_key,
        page_schema=page_schema,
    )

    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

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

        # ── Parse JSON ──────────────────────────────────────────
        parsed = _parse_llm_response(raw_response)
        if parsed is None:
            logger.warning(
                "Otto: Invalid JSON at iteration %d: %s",
                iteration, raw_response[:200],
            )
            messages.append({"role": "model", "content": raw_response})
            messages.append({
                "role": "user",
                "content": "Your response was not valid JSON. Please respond with ONLY valid JSON.",
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
            # Pause — wait for user form submission
            return

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
                "done": False,
            }
            messages.append({"role": "model", "content": raw_response})
            yield {"role": "assistant", "content": "", "done": True}
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
