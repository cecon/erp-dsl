"""SQLAlchemy implementation of the Workflow repository port."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.application.ports.workflow_repository_port import (
    WorkflowRepositoryInterface,
)
from src.domain.entities.workflow import (
    Workflow,
    WorkflowStatus,
    WorkflowStep,
)
from src.infrastructure.persistence.sqlalchemy.models import WorkflowModel


class SqlAlchemyWorkflowRepository(WorkflowRepositoryInterface):
    """Concrete workflow repository backed by PostgreSQL."""

    def __init__(self, db: Session) -> None:
        self._db = db

    # ── Mapping helpers ─────────────────────────────────────────

    @staticmethod
    def _to_entity(row: WorkflowModel) -> Workflow:
        steps = [
            WorkflowStep(
                skill=s.get("skill", ""),
                params=s.get("params", {}),
                requires_confirmation=s.get("requires_confirmation", False),
                on_error=s.get("on_error", "stop"),
            )
            for s in (row.steps or [])
        ]
        return Workflow(
            id=row.id,
            tenant_id=row.tenant_id,
            name=row.name,
            command=row.command,
            description=row.description or "",
            steps=steps,
            status=WorkflowStatus(row.status),
            version=row.version,
        )

    @staticmethod
    def _steps_to_dicts(steps: list[WorkflowStep]) -> list[dict]:
        return [
            {
                "skill": s.skill,
                "params": s.params,
                "requires_confirmation": s.requires_confirmation,
                "on_error": s.on_error,
            }
            for s in steps
        ]

    # ── Interface implementation ────────────────────────────────

    def list_by_tenant(self, tenant_id: str) -> list[Workflow]:
        stmt = (
            select(WorkflowModel)
            .where(WorkflowModel.tenant_id == tenant_id)
            .order_by(WorkflowModel.name)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [self._to_entity(r) for r in rows]

    def get_by_id(
        self, workflow_id: str, tenant_id: str,
    ) -> Workflow | None:
        stmt = select(WorkflowModel).where(
            WorkflowModel.id == workflow_id,
            WorkflowModel.tenant_id == tenant_id,
        )
        row = self._db.execute(stmt).scalar_one_or_none()
        return self._to_entity(row) if row else None

    def get_by_command(
        self, command: str, tenant_id: str,
    ) -> Workflow | None:
        stmt = select(WorkflowModel).where(
            WorkflowModel.command == command,
            WorkflowModel.tenant_id == tenant_id,
            WorkflowModel.status == "published",
        )
        row = self._db.execute(stmt).scalar_one_or_none()
        return self._to_entity(row) if row else None

    def create(self, workflow: Workflow) -> Workflow:
        model = WorkflowModel(
            id=workflow.id,
            tenant_id=workflow.tenant_id,
            name=workflow.name,
            command=workflow.command,
            description=workflow.description,
            steps=self._steps_to_dicts(workflow.steps),
            status=workflow.status.value,
            version=workflow.version,
        )
        self._db.add(model)
        self._db.flush()
        return workflow

    def update(self, workflow: Workflow) -> Workflow:
        stmt = select(WorkflowModel).where(
            WorkflowModel.id == workflow.id,
            WorkflowModel.tenant_id == workflow.tenant_id,
        )
        model = self._db.execute(stmt).scalar_one_or_none()
        if model is None:
            raise ValueError(f"Workflow {workflow.id} not found.")
        model.name = workflow.name
        model.command = workflow.command
        model.description = workflow.description
        model.steps = self._steps_to_dicts(workflow.steps)
        model.status = workflow.status.value
        model.version = workflow.version
        self._db.flush()
        return workflow
