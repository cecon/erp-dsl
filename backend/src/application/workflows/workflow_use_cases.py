"""Workflow use cases — thin orchestrators above the repository port."""

from __future__ import annotations

import uuid

from src.application.ports.workflow_repository_port import (
    WorkflowRepositoryInterface,
)
from src.domain.entities.workflow import (
    Workflow,
    WorkflowStatus,
    WorkflowStep,
)


class ListWorkflowsUseCase:
    """List all workflows for a tenant."""

    def __init__(self, repo: WorkflowRepositoryInterface) -> None:
        self._repo = repo

    def execute(self, tenant_id: str) -> list[Workflow]:
        return self._repo.list_by_tenant(tenant_id)


class GetWorkflowUseCase:
    """Retrieve a single workflow by ID."""

    def __init__(self, repo: WorkflowRepositoryInterface) -> None:
        self._repo = repo

    def execute(
        self, workflow_id: str, tenant_id: str,
    ) -> Workflow | None:
        return self._repo.get_by_id(workflow_id, tenant_id)


class CreateWorkflowUseCase:
    """Create a new workflow from raw input data."""

    def __init__(self, repo: WorkflowRepositoryInterface) -> None:
        self._repo = repo

    def execute(self, data: dict, tenant_id: str) -> Workflow:
        steps = [
            WorkflowStep(
                skill=s.get("skill", ""),
                params=s.get("params", {}),
                requires_confirmation=s.get("requires_confirmation", False),
                on_error=s.get("on_error", "stop"),
            )
            for s in data.get("steps", [])
        ]
        workflow = Workflow(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=data["name"],
            command=data["command"],
            description=data.get("description", ""),
            steps=steps,
            status=WorkflowStatus(data.get("status", "draft")),
        )
        return self._repo.create(workflow)


class UpdateWorkflowUseCase:
    """Update an existing workflow, incrementing version."""

    def __init__(self, repo: WorkflowRepositoryInterface) -> None:
        self._repo = repo

    def execute(
        self, workflow_id: str, data: dict, tenant_id: str,
    ) -> Workflow:
        existing = self._repo.get_by_id(workflow_id, tenant_id)
        if existing is None:
            raise ValueError(f"Workflow {workflow_id} not found.")

        if "name" in data:
            existing.name = data["name"]
        if "command" in data:
            existing.command = data["command"]
        if "description" in data:
            existing.description = data["description"]
        if "status" in data:
            existing.status = WorkflowStatus(data["status"])
        if "steps" in data:
            existing.steps = [
                WorkflowStep(
                    skill=s.get("skill", ""),
                    params=s.get("params", {}),
                    requires_confirmation=s.get(
                        "requires_confirmation", False,
                    ),
                    on_error=s.get("on_error", "stop"),
                )
                for s in data["steps"]
            ]

        existing.version += 1
        return self._repo.update(existing)
