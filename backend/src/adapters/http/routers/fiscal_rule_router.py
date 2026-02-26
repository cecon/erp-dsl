"""FastAPI router for Fiscal Rules (Regra Tributária)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.adapters.http.dependency_injection import get_current_user, get_db
from src.application.ports.auth_port import AuthContext
from src.application.use_cases.fiscal_rule import (
    CreateFiscalRuleUseCase,
    DeleteFiscalRuleUseCase,
    GetFiscalRuleUseCase,
    ListFiscalRulesUseCase,
    UpdateFiscalRuleUseCase,
)
from src.infrastructure.persistence.sqlalchemy.fiscal_rule_repository_impl import (
    FiscalRuleRepositoryImpl,
)

router = APIRouter()

# ── Schemas ────────────────────────────────────────────────────────


class FiscalRuleResponse(BaseModel):
    id: str
    tenant_id: str
    id_grupo_tributario: str
    id_natureza_operacao: str
    uf_origem: str
    uf_destino: str
    tipo_contribuinte_dest: str
    cfop: str
    icms_cst: str
    icms_csosn: str
    icms_aliquota: float
    icms_perc_reducao_bc: float
    pis_cst: str
    cofins_cst: str
    ibs_cbs_cst: str
    ibs_aliquota_uf: float
    ibs_aliquota_mun: float
    cbs_aliquota: float
    is_cst: str
    is_aliquota: float
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ListFiscalRulesResponse(BaseModel):
    items: list[FiscalRuleResponse]
    total: int


class CreateFiscalRuleRequest(BaseModel):
    id_grupo_tributario: str
    id_natureza_operacao: str
    uf_origem: str = ""
    uf_destino: str = ""
    tipo_contribuinte_dest: str = ""
    cfop: str = ""
    icms_cst: str = ""
    icms_csosn: str = ""
    icms_aliquota: Decimal | None = None
    icms_perc_reducao_bc: Decimal | None = None
    pis_cst: str = ""
    cofins_cst: str = ""
    ibs_cbs_cst: str = ""
    ibs_aliquota_uf: Decimal | None = None
    ibs_aliquota_mun: Decimal | None = None
    cbs_aliquota: Decimal | None = None
    is_cst: str = ""
    is_aliquota: Decimal | None = None


class UpdateFiscalRuleRequest(BaseModel):
    id_grupo_tributario: str | None = None
    id_natureza_operacao: str | None = None
    uf_origem: str | None = None
    uf_destino: str | None = None
    tipo_contribuinte_dest: str | None = None
    cfop: str | None = None
    icms_cst: str | None = None
    icms_csosn: str | None = None
    icms_aliquota: Decimal | None = None
    icms_perc_reducao_bc: Decimal | None = None
    pis_cst: str | None = None
    cofins_cst: str | None = None
    ibs_cbs_cst: str | None = None
    ibs_aliquota_uf: Decimal | None = None
    ibs_aliquota_mun: Decimal | None = None
    cbs_aliquota: Decimal | None = None
    is_cst: str | None = None
    is_aliquota: Decimal | None = None


# ── Dependencies ───────────────────────────────────────────────────


def get_repository(db: Session = Depends(get_db)) -> FiscalRuleRepositoryImpl:
    return FiscalRuleRepositoryImpl(db)


# ── Endpoints ──────────────────────────────────────────────────────


@router.get("", response_model=ListFiscalRulesResponse)
def list_fiscal_rules(
    offset: int = 0,
    limit: int = 50,
    auth: AuthContext = Depends(get_current_user),
    repo: FiscalRuleRepositoryImpl = Depends(get_repository),
) -> dict:
    use_case = ListFiscalRulesUseCase(repo)
    rules = use_case.execute(tenant_id=auth.tenant_id, limit=limit, offset=offset)
    
    # Minimal total count for generic frontend compatibility
    return {"items": rules, "total": len(rules)}


@router.get("/{rule_id}", response_model=FiscalRuleResponse)
def get_fiscal_rule(
    rule_id: str,
    auth: AuthContext = Depends(get_current_user),
    repo: FiscalRuleRepositoryImpl = Depends(get_repository),
) -> FiscalRuleResponse:
    use_case = GetFiscalRuleUseCase(repo)
    rule = use_case.execute(rule_id, auth.tenant_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fiscal rule not found",
        )
    return rule


@router.post("", response_model=FiscalRuleResponse, status_code=status.HTTP_201_CREATED)
def create_fiscal_rule(
    request: CreateFiscalRuleRequest,
    auth: AuthContext = Depends(get_current_user),
    repo: FiscalRuleRepositoryImpl = Depends(get_repository),
    db: Session = Depends(get_db),
) -> FiscalRuleResponse:
    use_case = CreateFiscalRuleUseCase(repo)
    rule = use_case.execute(
        tenant_id=auth.tenant_id,
        **request.dict(exclude_unset=True),
    )
    db.commit()
    return rule


@router.put("/{rule_id}", response_model=FiscalRuleResponse)
def update_fiscal_rule(
    rule_id: str,
    request: UpdateFiscalRuleRequest,
    auth: AuthContext = Depends(get_current_user),
    repo: FiscalRuleRepositoryImpl = Depends(get_repository),
    db: Session = Depends(get_db),
) -> FiscalRuleResponse:
    use_case = UpdateFiscalRuleUseCase(repo)
    try:
        rule = use_case.execute(
            rule_id=rule_id,
            tenant_id=auth.tenant_id,
            **request.dict(exclude_unset=True),
        )
        db.commit()
        return rule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.delete("/{rule_id}")
def delete_fiscal_rule(
    rule_id: str,
    auth: AuthContext = Depends(get_current_user),
    repo: FiscalRuleRepositoryImpl = Depends(get_repository),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    use_case = DeleteFiscalRuleUseCase(repo)
    deleted = use_case.execute(rule_id=rule_id, tenant_id=auth.tenant_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fiscal rule not found",
        )
    db.commit()
    return {"detail": "Fiscal rule deleted"}
