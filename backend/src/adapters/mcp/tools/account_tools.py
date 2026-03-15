"""MCP tools — Project/account information.

Provides read-only tools for the Claude model to inspect the
current ERP project context (projects, apps, tenant info).
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.mcp.mcp_auth import get_admin_context
from src.infrastructure.persistence.sqlalchemy.account_models import (
    ProjectModel,
    ProjectAppModel,
)
from src.infrastructure.persistence.sqlalchemy.models import UserModel


def register_account_tools(mcp: FastMCP, get_db: Any) -> None:
    """Register account/project info tools into the FastMCP instance."""

    @mcp.tool()
    def get_project_info() -> dict[str, Any]:
        """Retorna informações do projeto ERP atual (tenant, apps, usuários admin).

        Use este tool para entender o contexto do projeto antes de fazer
        alterações em entidades ou schemas.
        """
        db: Session = next(get_db())
        try:
            ctx = get_admin_context(db)

            # Busca o projeto pelo tenant_id do admin
            project = db.execute(
                select(ProjectModel).where(
                    ProjectModel.id == ctx.tenant_id
                )
            ).scalar_one_or_none()

            # Busca apps vinculados ao projeto
            apps = db.execute(
                select(ProjectAppModel).where(
                    ProjectAppModel.project_id == ctx.tenant_id
                )
            ).scalars().all()

            # Busca usuários admin
            admins = db.execute(
                select(UserModel).where(
                    UserModel.tenant_id == ctx.tenant_id,
                    UserModel.role == "admin",
                )
            ).scalars().all()

            return {
                "tenant_id": ctx.tenant_id,
                "project": {
                    "id": str(project.id) if project else ctx.tenant_id,
                    "name": project.name if project else "N/A",
                } if project else {"id": ctx.tenant_id, "name": "N/A"},
                "apps": [
                    {"id": str(a.id), "name": a.name, "slug": a.slug}
                    for a in apps
                ],
                "admins": [
                    {"id": str(u.id), "username": u.username}
                    for u in admins
                ],
            }
        finally:
            db.close()

    @mcp.tool()
    def list_entity_types() -> list[str]:
        """Lista todos os tipos de entidade disponíveis no ERP (com schema publicado).

        Use este tool antes de chamar list_entities/get_entity para saber
        quais entity_names são válidos.
        """
        from src.infrastructure.persistence.sqlalchemy.models import PageVersionModel

        db: Session = next(get_db())
        try:
            pages = (
                db.query(PageVersionModel.page_key)
                .filter(
                    PageVersionModel.scope == "global",
                    PageVersionModel.status == "published",
                )
                .distinct()
                .all()
            )
            return [p.page_key for p in pages]
        finally:
            db.close()
