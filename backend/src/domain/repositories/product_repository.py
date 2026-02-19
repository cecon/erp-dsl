"""Abstract repository interface for products (domain Protocol)."""

from __future__ import annotations

from typing import Optional, Protocol

from src.domain.entities.product import Product


class ProductRepository(Protocol):
    """Port for persisting and querying products."""

    def get_by_id(self, product_id: str, tenant_id: str) -> Optional[Product]:
        ...

    def list_by_tenant(
        self,
        tenant_id: str,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Product]: ...

    def count_by_tenant(self, tenant_id: str) -> int: ...

    def save(self, product: Product) -> Product: ...

    def update(self, product: Product) -> Product: ...

    def delete(self, product_id: str, tenant_id: str) -> bool: ...
