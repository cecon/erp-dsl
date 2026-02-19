"""Product entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional


@dataclass
class Product:
    """Domain entity representing a product within a tenant."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    name: str = ""
    price: Decimal = Decimal("0.00")
    sku: Optional[str] = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def update(
        self,
        name: Optional[str] = None,
        price: Optional[Decimal] = None,
        sku: Optional[str] = None,
    ) -> None:
        if name is not None:
            self.name = name
        if price is not None:
            self.price = price
        if sku is not None:
            self.sku = sku
        self.updated_at = datetime.now(timezone.utc)
