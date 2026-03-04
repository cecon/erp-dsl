"""Abstract repository interface for account management (domain Protocol)."""

from __future__ import annotations

from typing import Optional, Protocol

from src.domain.entities.account import (
    Account,
    App,
    Company,
    DatabaseInfo,
    Plan,
    Project,
    Subscription,
)


class AccountRepository(Protocol):
    """Port for persisting and querying platform entities."""

    # ── Accounts ────────────────────────────────────────────────────
    def find_account_by_email(self, email: str) -> Optional[Account]: ...
    def save_account(self, account: Account) -> Account: ...

    # ── Plans & Subscriptions ───────────────────────────────────────
    def find_free_plan(self) -> Optional[Plan]: ...
    def list_plans(self) -> list[Plan]: ...
    def save_subscription(self, sub: Subscription) -> Subscription: ...
    def find_active_subscription(
        self, account_id: str,
    ) -> Optional[Subscription]: ...

    # ── Projects ────────────────────────────────────────────────────
    def save_project(self, project: Project) -> Project: ...
    def list_projects_by_account(self, account_id: str) -> list[Project]: ...
    def get_project(self, project_id: str) -> Optional[Project]: ...

    # ── Company ─────────────────────────────────────────────────────
    def get_company(self, project_id: str) -> Optional[Company]: ...
    def upsert_company(self, company: Company) -> Company: ...

    # ── Apps ─────────────────────────────────────────────────────────
    def save_app(self, app: App) -> App: ...
    def list_apps_by_project(self, project_id: str) -> list[App]: ...

    # ── Database info ───────────────────────────────────────────────
    def get_database_info(self, app_id: str) -> Optional[DatabaseInfo]: ...
