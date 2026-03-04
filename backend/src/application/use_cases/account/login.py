"""Use case: Authenticate an existing account (login)."""

from __future__ import annotations

from passlib.context import CryptContext

from src.application.ports.account_repository_port import AccountRepositoryPort
from src.application.ports.auth_port import AuthPort

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginUseCase:
    """Verifies credentials and issues a JWT token."""

    def __init__(
        self,
        repo: AccountRepositoryPort,
        auth: AuthPort,
    ) -> None:
        self._repo = repo
        self._auth = auth

    def execute(self, email: str, password: str) -> dict:
        """Authenticate an account.

        Returns
        -------
        dict with access_token, account_id, email, name.

        Raises
        ------
        ValueError if credentials are invalid.
        """
        acct = self._repo.find_account_by_email(email)
        if not acct or not pwd_context.verify(password, acct.password_hash):
            raise ValueError("Invalid credentials")

        token = self._auth.create_token(
            user_id=acct.id,
            tenant_id=acct.id,
            username=acct.email,
            role="owner",
        )

        return {
            "access_token": token,
            "account_id": acct.id,
            "email": acct.email,
            "name": acct.name,
        }
