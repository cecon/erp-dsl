"""Agent Orchestrator — proprietary ReAct loop.

Receives a user request, discovers available skills, and iterates
with the LLM until a final product draft is produced or the maximum
number of iterations is reached.

Supports two modes:
- ``run_agent()``: batch mode, returns final AgentResult.
- ``run_agent_stream()``: async generator, yields SSE-ready dicts per step.

No external agent frameworks — pure Python.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

from src.application.agent import skill_registry
from src.application.agent.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 8


@dataclass
class AgentResult:
    """Result of an orchestrator run."""

    draft: dict | None = None
    steps: list[dict] = field(default_factory=list)
    finished: bool = False
    iterations: int = 0
    error: str | None = None


def _build_default_system_prompt(tenant_schema: dict) -> str:
    """Build a generic system prompt (fallback when no custom prompt is given)."""
    skills = skill_registry.list_skills()

    skills_block = "\n".join(
        f"  - **{s['name']}**: {s['description']}\n"
        f"    params: {json.dumps(s['params_schema'], ensure_ascii=False)}"
        for s in skills
    )

    schema_block = json.dumps(tenant_schema, indent=2, ensure_ascii=False)

    return f"""You are an ERP product registration assistant.

Your goal is to help the user fill in product data by using the available skills
to fetch and classify information automatically.

## Available Skills
{skills_block}

## Tenant Product Schema (fields to fill)
```json
{schema_block}
```

## Response Format
You MUST respond with valid JSON only. No markdown, no extra text.

To call a skill:
{{"action": "<skill_name>", "params": {{...}}}}

When you have gathered enough information and are ready to return the final draft:
{{"done": true, "draft": {{...}}}}

Rules:
- Call ONE skill at a time.
- After receiving a skill result, decide if you need more data or can produce the draft.
- Fill as many fields as possible from the gathered data.
- For fields you cannot determine, use null.
- Always respond with valid JSON.
"""


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


async def _execute_iteration(
    iteration: int,
    messages: list[dict],
    llm: LLMProvider,
    context: dict,
) -> dict:
    """Execute a single iteration of the ReAct loop.

    Returns a step dict describing what happened.
    """
    # ── Call LLM ─────────────────────────────────────────────────
    try:
        raw_response = await llm.complete(messages)
    except Exception as exc:
        logger.error("LLM call failed at iteration %d: %s", iteration, exc)
        return {"iteration": iteration, "type": "llm_error", "error": str(exc)}

    # ── Parse JSON ───────────────────────────────────────────────
    parsed = _parse_llm_response(raw_response)
    if parsed is None:
        logger.warning(
            "Invalid JSON from LLM at iteration %d: %s",
            iteration, raw_response[:200],
        )
        messages.append({"role": "model", "content": raw_response})
        messages.append({
            "role": "user",
            "content": "Your response was not valid JSON. Please respond with ONLY valid JSON.",
        })
        return {
            "iteration": iteration,
            "type": "parse_error",
            "raw": raw_response[:500],
        }

    # ── Handle "done" ────────────────────────────────────────────
    if parsed.get("done"):
        draft = parsed.get("draft", {})
        return {"iteration": iteration, "type": "done", "draft": draft}

    # ── Handle skill action ──────────────────────────────────────
    action = parsed.get("action")
    params = parsed.get("params", {})

    if not action:
        messages.append({"role": "model", "content": raw_response})
        messages.append({
            "role": "user",
            "content": (
                'Your JSON must have either {"action": "...", "params": {...}} '
                'or {"done": true, "draft": {...}}.'
            ),
        })
        return {"iteration": iteration, "type": "invalid_action", "parsed": parsed}

    skill_fn = skill_registry.get(action)
    if skill_fn is None:
        available = [s["name"] for s in skill_registry.list_skills()]
        messages.append({"role": "model", "content": raw_response})
        messages.append({
            "role": "user",
            "content": f"Skill '{action}' not found. Available skills: {available}",
        })
        return {"iteration": iteration, "type": "skill_not_found", "action": action}

    # ── Execute skill ────────────────────────────────────────────
    try:
        skill_result = await skill_fn(params, context)
    except Exception as exc:
        logger.error("Skill '%s' failed: %s", action, exc)
        skill_result = {"error": str(exc)}

    # Feed result back to LLM
    messages.append({"role": "model", "content": raw_response})
    messages.append({
        "role": "user",
        "content": (
            f"Skill '{action}' returned:\n"
            f"```json\n{json.dumps(skill_result, ensure_ascii=False, default=str)}\n```\n"
            "Based on this result, decide your next action or produce the final draft."
        ),
    })

    return {
        "iteration": iteration,
        "type": "skill_call",
        "action": action,
        "params": params,
        "result": skill_result,
    }


# ── Batch mode ───────────────────────────────────────────────────────


async def run_agent(
    user_input: str,
    tenant_id: str,
    tenant_schema: dict,
    llm: LLMProvider,
    context: dict | None = None,
    system_prompt: str | None = None,
) -> AgentResult:
    """Run the ReAct loop (batch mode).

    Args:
        user_input: The user's natural-language request.
        tenant_id: Current tenant ID.
        tenant_schema: Dict describing the product fields for this tenant.
        llm: An LLMProvider instance to call.
        context: Shared context dict passed to skills (e.g. {"db": session}).
        system_prompt: Custom system prompt. Falls back to default if None.

    Returns:
        AgentResult with the final draft and execution history.
    """
    context = context or {}
    result = AgentResult()

    prompt = system_prompt or _build_default_system_prompt(tenant_schema)
    messages: list[dict] = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_input},
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):
        result.iterations = iteration

        step = await _execute_iteration(iteration, messages, llm, context)
        result.steps.append(step)

        if step["type"] == "llm_error":
            result.error = step["error"]
            break

        if step["type"] == "done":
            result.draft = step["draft"]
            result.finished = True
            break

    if not result.finished and result.error is None:
        result.error = f"Max iterations ({MAX_ITERATIONS}) reached without completion"

    return result


# ── Streaming mode (SSE) ─────────────────────────────────────────────


async def run_agent_stream(
    user_input: str,
    tenant_id: str,
    tenant_schema: dict,
    llm: LLMProvider,
    context: dict | None = None,
    system_prompt: str | None = None,
) -> AsyncGenerator[dict, None]:
    """Run the ReAct loop as an async generator for SSE streaming.

    Yields one dict per iteration, suitable for SSE ``data:`` events.

    Final event has ``done: true`` with the product draft.
    """
    context = context or {}

    prompt = system_prompt or _build_default_system_prompt(tenant_schema)
    messages: list[dict] = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_input},
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):
        step = await _execute_iteration(iteration, messages, llm, context)

        if step["type"] == "llm_error":
            yield {"done": True, "error": step["error"], "iteration": iteration}
            return

        if step["type"] == "done":
            yield {"done": True, "draft": step["draft"], "iteration": iteration}
            return

        # Emit in-progress event
        yield {
            "done": False,
            "step": step["type"],
            "iteration": iteration,
            "skill": step.get("action"),
            "result": step.get("result"),
        }

    # Exhausted iterations
    yield {
        "done": True,
        "error": f"Max iterations ({MAX_ITERATIONS}) reached",
        "iteration": MAX_ITERATIONS,
    }
