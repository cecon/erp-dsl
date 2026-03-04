"""Use case: Create a new project under an account."""

from __future__ import annotations

import re

from src.application.ports.account_repository_port import AccountRepositoryPort
from src.domain.entities.account import Project


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")[:64]


class CreateProjectUseCase:
    """Creates a project after verifying the account has an active subscription."""

    def __init__(self, repo: AccountRepositoryPort) -> None:
        self._repo = repo

    def execute(self, account_id: str, name: str) -> Project:
        """Create a project.

        Raises
        ------
        ValueError if no active subscription.
        """
        sub = self._repo.find_active_subscription(account_id)
        if not sub:
            raise ValueError("No active subscription")

        project = Project(
            account_id=account_id,
            subscription_id=sub.id,
            name=name,
            slug=_slugify(name),
        )
        return self._repo.save_project(project)
