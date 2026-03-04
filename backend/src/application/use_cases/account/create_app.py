"""Use case: Create a new app and provision its isolated database."""

from __future__ import annotations

import re
from typing import Protocol

from src.application.ports.account_repository_port import AccountRepositoryPort
from src.domain.entities.account import App


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")[:64]


class DatabaseProvisioner(Protocol):
    """Port for provisioning an isolated database for an app."""

    def provision(self, app_id: str) -> None: ...


class CreateAppUseCase:
    """Creates an app within a project and provisions its database."""

    def __init__(
        self,
        repo: AccountRepositoryPort,
        provisioner: DatabaseProvisioner,
    ) -> None:
        self._repo = repo
        self._provisioner = provisioner

    def execute(
        self,
        project_id: str,
        name: str,
        llm_provider: str | None = None,
        llm_model: str | None = None,
        llm_api_key: str | None = None,
    ) -> App:
        """Create an app and provision its database."""
        app = App(
            project_id=project_id,
            name=name,
            slug=_slugify(name),
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_api_key=llm_api_key,
        )
        saved = self._repo.save_app(app)
        self._provisioner.provision(saved.id)
        return saved
