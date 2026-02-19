"""CRUD use cases for Product entity."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from src.application.ports.product_repository_port import ProductRepositoryPort
from src.domain.entities.product import Product


class CreateProductUseCase:
    def __init__(self, repo: ProductRepositoryPort) -> None:
        self._repo = repo

    def execute(
        self,
        tenant_id: str,
        name: str,
        price: Decimal,
        sku: Optional[str] = None,
    ) -> dict[str, Any]:
        product = Product(
            tenant_id=tenant_id,
            name=name,
            price=price,
            sku=sku,
        )
        saved = self._repo.save(product)
        return _to_dict(saved)


class UpdateProductUseCase:
    def __init__(self, repo: ProductRepositoryPort) -> None:
        self._repo = repo

    def execute(
        self,
        product_id: str,
        tenant_id: str,
        name: Optional[str] = None,
        price: Optional[Decimal] = None,
        sku: Optional[str] = None,
    ) -> dict[str, Any]:
        product = self._repo.get_by_id(product_id, tenant_id)
        if not product:
            raise ValueError(f"Product {product_id} not found.")
        product.update(name=name, price=price, sku=sku)
        updated = self._repo.update(product)
        return _to_dict(updated)


class DeleteProductUseCase:
    def __init__(self, repo: ProductRepositoryPort) -> None:
        self._repo = repo

    def execute(self, product_id: str, tenant_id: str) -> bool:
        return self._repo.delete(product_id, tenant_id)


class ListProductsUseCase:
    def __init__(self, repo: ProductRepositoryPort) -> None:
        self._repo = repo

    def execute(
        self,
        tenant_id: str,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        products = self._repo.list_by_tenant(tenant_id, offset, limit)
        total = self._repo.count_by_tenant(tenant_id)
        return {
            "items": [_to_dict(p) for p in products],
            "total": total,
            "offset": offset,
            "limit": limit,
        }


def _to_dict(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "tenant_id": product.tenant_id,
        "name": product.name,
        "price": str(product.price),
        "sku": product.sku,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
    }
