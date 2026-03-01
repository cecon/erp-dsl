"""WorkflowExecutor — runs workflow steps sequentially via SSE.

Loads a Workflow domain entity and executes each step through the
SkillRegistry, yielding SSE-compatible dicts for the streaming
response.  Supports confirmation pauses, configurable error handling
per step, and dynamic parameter resolution.

Dynamic parameters:
  - ``{input}``           → replaced with the user text after the /command
  - ``{previous_result}`` → replaced with the JSON of the previous step result
  - Empty string values   → filled with the user input automatically
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator

from src.application.agent import skill_registry
from src.domain.entities.workflow import Workflow

logger = logging.getLogger(__name__)


def _resolve_params(
    params: dict[str, Any],
    user_input: str,
    previous_result: Any | None,
) -> dict[str, Any]:
    """Resolve dynamic placeholders in step parameters.

    Rules:
    1. String values containing ``{input}`` are replaced with *user_input*.
    2. String values containing ``{previous_result}`` are replaced with the
       JSON serialisation of the previous step's result.
    3. Empty string values (``""``) are filled with *user_input*.
    """
    prev_json = json.dumps(previous_result, ensure_ascii=False, default=str) if previous_result is not None else ""
    resolved: dict[str, Any] = {}
    for key, val in params.items():
        if isinstance(val, str):
            if val == "":
                resolved[key] = user_input
            else:
                resolved[key] = val.replace("{input}", user_input).replace(
                    "{previous_result}", prev_json,
                )
        else:
            resolved[key] = val
    return resolved


async def execute_workflow(
    workflow: Workflow,
    context: dict,
    sandbox: bool = False,
) -> AsyncGenerator[dict, None]:
    """Execute all steps in *workflow* sequentially.

    Yields SSE event dicts with ``role: 'workflow'``.

    Args:
        workflow: The domain entity with populated ``steps``.
        context: Dict containing ``db``, ``tenant_id``, and
                 ``user_input`` (text after the /command).
        sandbox: When True, adds ``sandbox=True`` to the context so
                 skills can opt for dry-run behaviour.
    """
    ctx = {**context, "sandbox": sandbox}
    total = len(workflow.steps)
    user_input: str = ctx.get("user_input", "")
    previous_result: Any = None

    yield {
        "role": "workflow",
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "total_steps": total,
        "status": "started",
        "done": False,
    }

    for idx, step in enumerate(workflow.steps):
        step_num = idx + 1

        # ── Confirmation gate ───────────────────────────────
        if step.requires_confirmation:
            yield {
                "role": "workflow",
                "step": step_num,
                "total_steps": total,
                "skill": step.skill,
                "status": "awaiting_confirmation",
                "message": (
                    f"Step {step_num}/{total} ({step.skill}) requer "
                    f"confirmação. Confirme para continuar."
                ),
                "done": False,
            }
            return

        # ── Resolve dynamic parameters ──────────────────────
        resolved_params = _resolve_params(step.params, user_input, previous_result)

        # ── Emit running status ─────────────────────────────
        yield {
            "role": "workflow",
            "step": step_num,
            "total_steps": total,
            "skill": step.skill,
            "params": resolved_params,
            "status": "running",
            "done": False,
        }

        # ── Resolve and invoke skill ────────────────────────
        skill_fn = skill_registry.get(step.skill)
        if skill_fn is None:
            err_msg = f"Skill '{step.skill}' não encontrada."
            logger.warning("Workflow %s step %d: %s", workflow.id, step_num, err_msg)
            yield {
                "role": "workflow",
                "step": step_num,
                "total_steps": total,
                "skill": step.skill,
                "status": "error",
                "message": err_msg,
                "done": step.on_error == "stop",
            }
            if step.on_error == "stop":
                return
            if step.on_error == "ask":
                return
            continue  # on_error == "continue"

        try:
            result = await skill_fn(resolved_params, ctx)
        except Exception as exc:
            logger.error(
                "Workflow %s step %d (%s) failed: %s",
                workflow.id, step_num, step.skill, exc,
            )
            result = {"error": str(exc)}
            yield {
                "role": "workflow",
                "step": step_num,
                "total_steps": total,
                "skill": step.skill,
                "status": "error",
                "message": str(exc),
                "result": result,
                "done": step.on_error == "stop",
            }
            if step.on_error == "stop":
                return
            if step.on_error == "ask":
                return
            continue  # on_error == "continue"

        # ── Track result for {previous_result} ──────────────
        previous_result = result

        # ── Emit step success ───────────────────────────────
        yield {
            "role": "workflow",
            "step": step_num,
            "total_steps": total,
            "skill": step.skill,
            "status": "done",
            "result": result,
            "done": False,
        }

    # ── All steps completed ─────────────────────────────────
    yield {
        "role": "workflow",
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "status": "completed",
        "message": f"Workflow '{workflow.name}' finalizado com sucesso.",
        "done": True,
    }

