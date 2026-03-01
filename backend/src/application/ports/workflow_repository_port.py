"""Port (interface) for the Workflow repository.

Application layer depends on this abstraction; infrastructure provides
the concrete implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.workflow import Workflow


class WorkflowRepositoryInterface(ABC):
    """Abstract contract for workflow persistence."""

    @abstractmethod
    def list_by_tenant(self, tenant_id: str) -> list[Workflow]:
        """Return all workflows belonging to *tenant_id*."""

    @abstractmethod
    def get_by_id(self, workflow_id: str, tenant_id: str) -> Workflow | None:
        """Return a single workflow or ``None``."""

    @abstractmethod
    def get_by_command(
        self, command: str, tenant_id: str,
    ) -> Workflow | None:
        """Find the published workflow matching a ``/command``."""

    @abstractmethod
    def create(self, workflow: Workflow) -> Workflow:
        """Persist a new workflow and return it."""

    @abstractmethod
    def update(self, workflow: Workflow) -> Workflow:
        """Update an existing workflow and return it."""
