"""SQLAlchemy implementation of ProductRepository port."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from src.domain.entities.product import Product
from src.infrastructure.persistence.sqlalchemy.models import ProductModel


class ProductRepositoryImpl:
    """Concrete implementation of the ProductRepository port."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Mappers ──────────────────────────────────────────────────────

    @staticmethod
    def _to_entity(model: ProductModel) -> Product:
        return Product(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            price=Decimal(str(model.price)),
            sku=model.sku,
            created_at=model.created_at or datetime.now(timezone.utc),
            updated_at=model.updated_at or datetime.now(timezone.utc),
        )

    @staticmethod
    def _to_model(entity: Product) -> ProductModel:
        return ProductModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            name=entity.name,
            price=entity.price,
            sku=entity.sku,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    # ── Port implementation ──────────────────────────────────────────

    def get_by_id(
        self, product_id: str, tenant_id: str
    ) -> Optional[Product]:
        stmt = select(ProductModel).where(
            and_(
                ProductModel.id == product_id,
                ProductModel.tenant_id == tenant_id,
            )
        )
        model = self._session.execute(stmt).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def list_by_tenant(
        self, tenant_id: str, offset: int = 0, limit: int = 50
    ) -> list[Product]:
        stmt = (
            select(ProductModel)
            .where(ProductModel.tenant_id == tenant_id)
            .order_by(ProductModel.name)
            .offset(offset)
            .limit(limit)
        )
        models = self._session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def count_by_tenant(self, tenant_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(ProductModel)
            .where(ProductModel.tenant_id == tenant_id)
        )
        return self._session.execute(stmt).scalar_one()

    def save(self, product: Product) -> Product:
        model = self._to_model(product)
        self._session.add(model)
        self._session.flush()
        return product

    def update(self, product: Product) -> Product:
        model = self._session.get(ProductModel, product.id)
        if model:
            model.name = product.name
            model.price = product.price
            model.sku = product.sku
            model.updated_at = datetime.now(timezone.utc)
            self._session.flush()
        return product

    def delete(self, product_id: str, tenant_id: str) -> bool:
        stmt = select(ProductModel).where(
            and_(
                ProductModel.id == product_id,
                ProductModel.tenant_id == tenant_id,
            )
        )
        model = self._session.execute(stmt).scalar_one_or_none()
        if model:
            self._session.delete(model)
            self._session.flush()
            return True
        return False
