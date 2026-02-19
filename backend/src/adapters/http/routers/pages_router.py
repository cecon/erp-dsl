"""Pages router — thin HTTP adapter delegating to use cases."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.adapters.http.dependency_injection import (
    create_draft_use_case,
    get_current_user,
    get_db,
    get_page_use_case,
    merge_page_use_case,
    publish_page_use_case,
    rollback_page_use_case,
)
from src.application.ports.auth_port import AuthContext
from src.application.use_cases.create_draft import CreateDraftUseCase
from src.application.use_cases.get_page import GetPageUseCase
from src.application.use_cases.merge_page import MergePageUseCase
from src.application.use_cases.publish_page import PublishPageUseCase
from src.application.use_cases.rollback_page import RollbackPageUseCase

router = APIRouter()


class DraftRequest(BaseModel):
    schema_json: dict[str, Any]
    tenant_id: Optional[str] = None


class PublishRequest(BaseModel):
    version_id: str


@router.get("/{page_key}")
def get_page(
    page_key: str,
    auth: AuthContext = Depends(get_current_user),
    uc: GetPageUseCase = Depends(get_page_use_case),
    db=Depends(get_db),
) -> dict[str, Any]:
    result = uc.execute(page_key, auth.tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Page not found")
    db.commit()
    return result


@router.post("/{page_key}/draft")
def create_draft(
    page_key: str,
    body: DraftRequest,
    auth: AuthContext = Depends(get_current_user),
    uc: CreateDraftUseCase = Depends(create_draft_use_case),
    db=Depends(get_db),
) -> dict[str, Any]:
    try:
        result = uc.execute(
            page_key=page_key,
            schema_json=body.schema_json,
            tenant_id=body.tenant_id or auth.tenant_id,
        )
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{page_key}/publish")
def publish_page(
    page_key: str,
    body: PublishRequest,
    auth: AuthContext = Depends(get_current_user),
    uc: PublishPageUseCase = Depends(publish_page_use_case),
    db=Depends(get_db),
) -> dict[str, Any]:
    try:
        result = uc.execute(page_key, body.version_id)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{page_key}/rollback/{version_id}")
def rollback_page(
    page_key: str,
    version_id: str,
    auth: AuthContext = Depends(get_current_user),
    uc: RollbackPageUseCase = Depends(rollback_page_use_case),
    db=Depends(get_db),
) -> dict[str, Any]:
    try:
        result = uc.execute(
            page_key=page_key,
            version_id=version_id,
            tenant_id=auth.tenant_id,
        )
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{page_key}/merge")
def merge_page(
    page_key: str,
    auth: AuthContext = Depends(get_current_user),
    uc: MergePageUseCase = Depends(merge_page_use_case),
    db=Depends(get_db),
) -> dict[str, Any]:
    try:
        result = uc.execute(page_key, auth.tenant_id)
        if not result:
            raise HTTPException(status_code=404, detail="Merge failed")
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
