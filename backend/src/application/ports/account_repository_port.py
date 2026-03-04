"""Application port re-exporting the domain AccountRepository Protocol."""

from src.domain.repositories.account_repository import AccountRepository

# Re-export for use-case imports
AccountRepositoryPort = AccountRepository

__all__ = ["AccountRepositoryPort"]
