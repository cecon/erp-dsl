"""Use case: Create a new account (signup)."""

from __future__ import annotations

import re
import uuid

from passlib.context import CryptContext

from src.application.ports.account_repository_port import AccountRepositoryPort
from src.application.ports.auth_port import AuthPort
from src.domain.entities.account import Account, Subscription

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SignupUseCase:
    """Creates a new platform account and auto-subscribes to free plan."""

    def __init__(
        self,
        repo: AccountRepositoryPort,
        auth: AuthPort,
    ) -> None:
        self._repo = repo
        self._auth = auth

    def execute(
        self, email: str, name: str, password: str,
    ) -> dict:
        """Register a new account.

        Returns
        -------
        dict with access_token, account_id, email, name.

        Raises
        ------
        ValueError if email is already registered.
        """
        existing = self._repo.find_account_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        account = Account(
            email=email,
            name=name,
            password_hash=pwd_context.hash(password),
        )
        self._repo.save_account(account)

        # Auto-subscribe to free plan
        free_plan = self._repo.find_free_plan()
        if free_plan:
            sub = Subscription(
                account_id=account.id,
                plan_id=free_plan.id,
                status="active",
            )
            self._repo.save_subscription(sub)

        token = self._auth.create_token(
            user_id=account.id,
            tenant_id=account.id,
            username=email,
            role="owner",
        )

        return {
            "access_token": token,
            "account_id": account.id,
            "email": email,
            "name": name,
        }
