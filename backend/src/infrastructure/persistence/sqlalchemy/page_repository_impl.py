"""SQLAlchemy implementation of PageRepository port."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from src.domain.entities.page_version import PageVersion, Scope, VersionStatus
from src.infrastructure.persistence.sqlalchemy.models import PageVersionModel


class PageRepositoryImpl:
    """Concrete implementation of the PageRepository port using SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Mappers ──────────────────────────────────────────────────────

    @staticmethod
    def _to_entity(model: PageVersionModel) -> PageVersion:
        return PageVersion(
            id=model.id,
            page_key=model.page_key,
            scope=Scope(model.scope),
            tenant_id=model.tenant_id,
            base_version_id=model.base_version_id,
            version_number=model.version_number,
            schema_json=model.schema_json or {},
            status=VersionStatus(model.status),
            created_at=model.created_at or datetime.now(timezone.utc),
            updated_at=model.updated_at or datetime.now(timezone.utc),
        )

    @staticmethod
    def _to_model(entity: PageVersion) -> PageVersionModel:
        return PageVersionModel(
            id=entity.id,
            page_key=entity.page_key,
            scope=entity.scope.value,
            tenant_id=entity.tenant_id,
            base_version_id=entity.base_version_id,
            version_number=entity.version_number,
            schema_json=entity.schema_json,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    # ── Port implementation ──────────────────────────────────────────

    def get_by_id(self, version_id: str) -> Optional[PageVersion]:
        model = self._session.get(PageVersionModel, version_id)
        return self._to_entity(model) if model else None

    def get_published(
        self,
        page_key: str,
        scope: Scope,
        tenant_id: Optional[str] = None,
    ) -> Optional[PageVersion]:
        conditions = [
            PageVersionModel.page_key == page_key,
            PageVersionModel.scope == scope.value,
            PageVersionModel.status == VersionStatus.PUBLISHED.value,
        ]
        if tenant_id:
            conditions.append(PageVersionModel.tenant_id == tenant_id)
        else:
            conditions.append(PageVersionModel.tenant_id.is_(None))

        stmt = select(PageVersionModel).where(and_(*conditions)).limit(1)
        model = self._session.execute(stmt).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def get_versions(
        self,
        page_key: str,
        scope: Scope,
        tenant_id: Optional[str] = None,
        status: Optional[VersionStatus] = None,
    ) -> list[PageVersion]:
        conditions = [
            PageVersionModel.page_key == page_key,
            PageVersionModel.scope == scope.value,
        ]
        if tenant_id:
            conditions.append(PageVersionModel.tenant_id == tenant_id)
        if status:
            conditions.append(PageVersionModel.status == status.value)

        stmt = (
            select(PageVersionModel)
            .where(and_(*conditions))
            .order_by(PageVersionModel.version_number.desc())
        )
        models = self._session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def get_latest_version_number(
        self,
        page_key: str,
        scope: Scope,
        tenant_id: Optional[str] = None,
    ) -> int:
        conditions = [
            PageVersionModel.page_key == page_key,
            PageVersionModel.scope == scope.value,
        ]
        if tenant_id:
            conditions.append(PageVersionModel.tenant_id == tenant_id)

        stmt = (
            select(PageVersionModel.version_number)
            .where(and_(*conditions))
            .order_by(PageVersionModel.version_number.desc())
            .limit(1)
        )
        result = self._session.execute(stmt).scalar_one_or_none()
        return result or 0

    def save(self, version: PageVersion) -> PageVersion:
        model = self._to_model(version)
        self._session.add(model)
        self._session.flush()
        return version

    def update(self, version: PageVersion) -> PageVersion:
        model = self._session.get(PageVersionModel, version.id)
        if model:
            model.page_key = version.page_key
            model.scope = version.scope.value
            model.tenant_id = version.tenant_id
            model.base_version_id = version.base_version_id
            model.version_number = version.version_number
            model.schema_json = version.schema_json
            model.status = version.status.value
            model.updated_at = datetime.now(timezone.utc)
            self._session.flush()
        return version
