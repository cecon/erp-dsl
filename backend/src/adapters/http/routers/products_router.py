"""Products CRUD router — thin HTTP adapter."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.adapters.http.dependency_injection import (
    create_product_use_case,
    delete_product_use_case,
    get_current_user,
    get_db,
    list_products_use_case,
    update_product_use_case,
)
from src.application.ports.auth_port import AuthContext
from src.application.use_cases.crud_product import (
    CreateProductUseCase,
    DeleteProductUseCase,
    ListProductsUseCase,
    UpdateProductUseCase,
)

router = APIRouter()


class CreateProductRequest(BaseModel):
    name: str
    price: Decimal
    sku: Optional[str] = None


class UpdateProductRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    sku: Optional[str] = None


@router.get("")
def list_products(
    offset: int = 0,
    limit: int = 50,
    auth: AuthContext = Depends(get_current_user),
    uc: ListProductsUseCase = Depends(list_products_use_case),
) -> dict[str, Any]:
    return uc.execute(auth.tenant_id, offset, limit)


@router.post("")
def create_product(
    body: CreateProductRequest,
    auth: AuthContext = Depends(get_current_user),
    uc: CreateProductUseCase = Depends(create_product_use_case),
    db=Depends(get_db),
) -> dict[str, Any]:
    result = uc.execute(
        tenant_id=auth.tenant_id,
        name=body.name,
        price=body.price,
        sku=body.sku,
    )
    db.commit()
    return result


@router.put("/{product_id}")
def update_product(
    product_id: str,
    body: UpdateProductRequest,
    auth: AuthContext = Depends(get_current_user),
    uc: UpdateProductUseCase = Depends(update_product_use_case),
    db=Depends(get_db),
) -> dict[str, Any]:
    try:
        result = uc.execute(
            product_id=product_id,
            tenant_id=auth.tenant_id,
            name=body.name,
            price=body.price,
            sku=body.sku,
        )
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{product_id}")
def delete_product(
    product_id: str,
    auth: AuthContext = Depends(get_current_user),
    uc: DeleteProductUseCase = Depends(delete_product_use_case),
    db=Depends(get_db),
) -> dict[str, str]:
    deleted = uc.execute(product_id, auth.tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    db.commit()
    return {"detail": "Product deleted"}
