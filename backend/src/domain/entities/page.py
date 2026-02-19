"""Page entity — represents a logical page identified by its key."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects.page_key import PageKey


@dataclass
class Page:
    """Thin entity representing a logical page.

    A Page is just a namespace: all real data lives in PageVersion.
    """

    page_key: PageKey

    @staticmethod
    def create(key: str) -> Page:
        return Page(page_key=PageKey(key))
