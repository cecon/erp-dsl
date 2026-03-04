"""SQLAlchemy implementation of AccountRepository."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.entities.account import (
    Account,
    App,
    Company,
    DatabaseInfo,
    Plan,
    Project,
    Subscription,
)
from src.infrastructure.persistence.sqlalchemy.account_models import (
    AccountModel,
    PlanModel,
    ProjectAppModel,
    ProjectCompanyModel,
    ProjectDatabaseModel,
    ProjectModel,
    SubscriptionModel,
)


class AccountRepositoryImpl:
    """SQLAlchemy-backed repository for platform management entities."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Accounts ────────────────────────────────────────────────────

    def find_account_by_email(self, email: str) -> Optional[Account]:
        row = self._session.execute(
            select(AccountModel).where(AccountModel.email == email)
        ).scalar_one_or_none()
        return self._to_account(row) if row else None

    def save_account(self, account: Account) -> Account:
        model = AccountModel(
            id=account.id,
            email=account.email,
            name=account.name,
            password_hash=account.password_hash,
        )
        self._session.add(model)
        self._session.flush()
        return account

    # ── Plans & Subscriptions ───────────────────────────────────────

    def find_free_plan(self) -> Optional[Plan]:
        row = self._session.execute(
            select(PlanModel).where(PlanModel.slug == "free")
        ).scalar_one_or_none()
        return self._to_plan(row) if row else None

    def list_plans(self) -> list[Plan]:
        rows = self._session.execute(select(PlanModel)).scalars().all()
        return [self._to_plan(r) for r in rows]

    def save_subscription(self, sub: Subscription) -> Subscription:
        model = SubscriptionModel(
            id=sub.id,
            account_id=sub.account_id,
            plan_id=sub.plan_id,
            status=sub.status,
        )
        self._session.add(model)
        self._session.flush()
        return sub

    def find_active_subscription(
        self, account_id: str,
    ) -> Optional[Subscription]:
        row = self._session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.account_id == account_id,
                SubscriptionModel.status == "active",
            )
        ).scalar_one_or_none()
        return self._to_subscription(row) if row else None

    # ── Projects ────────────────────────────────────────────────────

    def save_project(self, project: Project) -> Project:
        model = ProjectModel(
            id=project.id,
            account_id=project.account_id,
            subscription_id=project.subscription_id,
            name=project.name,
            slug=project.slug,
        )
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        project.created_at = model.created_at
        project.status = model.status
        return project

    def list_projects_by_account(self, account_id: str) -> list[Project]:
        rows = self._session.execute(
            select(ProjectModel).where(
                ProjectModel.account_id == account_id,
            )
        ).scalars().all()
        return [self._to_project(r) for r in rows]

    def get_project(self, project_id: str) -> Optional[Project]:
        row = self._session.get(ProjectModel, project_id)
        return self._to_project(row) if row else None

    # ── Company ─────────────────────────────────────────────────────

    def get_company(self, project_id: str) -> Optional[Company]:
        row = self._session.execute(
            select(ProjectCompanyModel).where(
                ProjectCompanyModel.project_id == project_id,
            )
        ).scalar_one_or_none()
        return self._to_company(row) if row else None

    def upsert_company(self, company: Company) -> Company:
        existing = self._session.execute(
            select(ProjectCompanyModel).where(
                ProjectCompanyModel.project_id == company.project_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.type = company.type
            existing.razao_social = company.razao_social
            existing.nome_fantasia = company.nome_fantasia
            existing.cnpj_cpf = company.cnpj_cpf
            existing.ie = company.ie
            existing.im = company.im
            existing.endereco = company.endereco
            self._session.flush()
            self._session.refresh(existing)
            return self._to_company(existing)

        model = ProjectCompanyModel(
            id=company.id,
            project_id=company.project_id,
            type=company.type,
            razao_social=company.razao_social,
            nome_fantasia=company.nome_fantasia,
            cnpj_cpf=company.cnpj_cpf,
            ie=company.ie,
            im=company.im,
            endereco=company.endereco,
        )
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        return self._to_company(model)

    # ── Apps ─────────────────────────────────────────────────────────

    def save_app(self, app: App) -> App:
        model = ProjectAppModel(
            id=app.id,
            project_id=app.project_id,
            name=app.name,
            slug=app.slug,
            llm_provider=app.llm_provider,
            llm_model=app.llm_model,
            llm_api_key=app.llm_api_key,
        )
        self._session.add(model)
        self._session.flush()
        self._session.refresh(model)
        app.created_at = model.created_at
        app.status = model.status
        return app

    def list_apps_by_project(self, project_id: str) -> list[App]:
        rows = self._session.execute(
            select(ProjectAppModel).where(
                ProjectAppModel.project_id == project_id,
            )
        ).scalars().all()
        return [self._to_app(r) for r in rows]

    # ── Database info ───────────────────────────────────────────────

    def get_database_info(self, app_id: str) -> Optional[DatabaseInfo]:
        row = self._session.execute(
            select(ProjectDatabaseModel).where(
                ProjectDatabaseModel.app_id == app_id,
            )
        ).scalar_one_or_none()
        return self._to_database_info(row) if row else None

    # ── Mappers (Model → Domain Entity) ─────────────────────────────

    @staticmethod
    def _to_account(m: AccountModel) -> Account:
        return Account(
            id=m.id, email=m.email, name=m.name,
            password_hash=m.password_hash,
            is_active=m.is_active, created_at=m.created_at,
        )

    @staticmethod
    def _to_plan(m: PlanModel) -> Plan:
        return Plan(
            id=m.id, name=m.name, slug=m.slug,
            price=float(m.price), enabled=m.enabled,
            features=m.features or {},
        )

    @staticmethod
    def _to_subscription(m: SubscriptionModel) -> Subscription:
        return Subscription(
            id=m.id, account_id=m.account_id,
            plan_id=m.plan_id, status=m.status,
            created_at=m.created_at,
        )

    @staticmethod
    def _to_project(m: ProjectModel) -> Project:
        return Project(
            id=m.id, account_id=m.account_id,
            subscription_id=m.subscription_id,
            name=m.name, slug=m.slug,
            status=m.status, created_at=m.created_at,
        )

    @staticmethod
    def _to_company(m: ProjectCompanyModel) -> Company:
        return Company(
            id=m.id, project_id=m.project_id,
            type=m.type, razao_social=m.razao_social,
            nome_fantasia=m.nome_fantasia,
            cnpj_cpf=m.cnpj_cpf,
            ie=m.ie, im=m.im,
            endereco=m.endereco,
            created_at=m.created_at,
        )

    @staticmethod
    def _to_app(m: ProjectAppModel) -> App:
        return App(
            id=m.id, project_id=m.project_id,
            name=m.name, slug=m.slug,
            status=m.status,
            llm_provider=m.llm_provider,
            llm_model=m.llm_model,
            llm_api_key=m.llm_api_key,
            created_at=m.created_at,
        )

    @staticmethod
    def _to_database_info(m: ProjectDatabaseModel) -> DatabaseInfo:
        return DatabaseInfo(
            id=m.id, app_id=m.app_id,
            db_name=m.db_name, db_host=m.db_host,
            db_port=m.db_port, db_user=m.db_user,
            db_password=m.db_password, status=m.status,
            created_at=m.created_at,
        )
