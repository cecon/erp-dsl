"""Application port re-exporting the domain PageRepository Protocol."""

from src.domain.repositories.page_repository import PageRepository

# Re-export for use-case imports
PageRepositoryPort = PageRepository

__all__ = ["PageRepositoryPort"]
