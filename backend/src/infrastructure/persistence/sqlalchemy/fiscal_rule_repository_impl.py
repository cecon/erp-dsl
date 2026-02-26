"""SQLAlchemy implementation of the Fiscal Rule repository port."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from src.application.ports.fiscal_rule_repository_port import (
    FiscalRuleRepositoryPort,
)
from src.domain.entities.fiscal_rule import FiscalRule
from src.infrastructure.persistence.sqlalchemy.tax_models import FiscalRuleModel


class FiscalRuleRepositoryImpl(FiscalRuleRepositoryPort):
    """SQLAlchemy persistent repository for Fiscal Rules."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_entity(self, model: FiscalRuleModel) -> FiscalRule:
        return FiscalRule(
            id=model.id,
            tenant_id=model.tenant_id,
            id_grupo_tributario=model.id_grupo_tributario,
            id_natureza_operacao=model.id_natureza_operacao,
            uf_origem=model.uf_origem,
            uf_destino=model.uf_destino,
            tipo_contribuinte_dest=model.tipo_contribuinte_dest,
            cfop=model.cfop,
            icms_cst=model.icms_cst,
            icms_csosn=model.icms_csosn,
            icms_aliquota=model.icms_aliquota,
            icms_perc_reducao_bc=model.icms_perc_reducao_bc,
            pis_cst=model.pis_cst,
            cofins_cst=model.cofins_cst,
            ibs_cbs_cst=model.ibs_cbs_cst,
            ibs_aliquota_uf=model.ibs_aliquota_uf,
            ibs_aliquota_mun=model.ibs_aliquota_mun,
            cbs_aliquota=model.cbs_aliquota,
            is_cst=model.is_cst,
            is_aliquota=model.is_aliquota,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: FiscalRule) -> FiscalRuleModel:
        return FiscalRuleModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            id_grupo_tributario=entity.id_grupo_tributario,
            id_natureza_operacao=entity.id_natureza_operacao,
            uf_origem=entity.uf_origem,
            uf_destino=entity.uf_destino,
            tipo_contribuinte_dest=entity.tipo_contribuinte_dest,
            cfop=entity.cfop,
            icms_cst=entity.icms_cst,
            icms_csosn=entity.icms_csosn,
            icms_aliquota=entity.icms_aliquota,
            icms_perc_reducao_bc=entity.icms_perc_reducao_bc,
            pis_cst=entity.pis_cst,
            cofins_cst=entity.cofins_cst,
            ibs_cbs_cst=entity.ibs_cbs_cst,
            ibs_aliquota_uf=entity.ibs_aliquota_uf,
            ibs_aliquota_mun=entity.ibs_aliquota_mun,
            cbs_aliquota=entity.cbs_aliquota,
            is_cst=entity.is_cst,
            is_aliquota=entity.is_aliquota,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def get_by_id(self, rule_id: str, tenant_id: str) -> Optional[FiscalRule]:
        model = (
            self.session.query(FiscalRuleModel)
            .filter_by(id=rule_id, tenant_id=tenant_id)
            .first()
        )
        return self._to_entity(model) if model else None

    def list_all(
        self, tenant_id: str, limit: int = 50, offset: int = 0
    ) -> list[FiscalRule]:
        models = (
            self.session.query(FiscalRuleModel)
            .filter_by(tenant_id=tenant_id)
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def save(self, rule: FiscalRule) -> FiscalRule:
        model = self._to_model(rule)
        self.session.add(model)
        self.session.flush()
        return self._to_entity(model)

    def update(self, rule: FiscalRule) -> FiscalRule:
        model = self.session.query(FiscalRuleModel).filter_by(id=rule.id).first()
        if not model:
            raise ValueError(f"Fiscal Rule {rule.id} not found")
        
        # Update fields
        model.id_grupo_tributario = rule.id_grupo_tributario
        model.id_natureza_operacao = rule.id_natureza_operacao
        model.uf_origem = rule.uf_origem
        model.uf_destino = rule.uf_destino
        model.tipo_contribuinte_dest = rule.tipo_contribuinte_dest
        model.cfop = rule.cfop
        model.icms_cst = rule.icms_cst
        model.icms_csosn = rule.icms_csosn
        model.icms_aliquota = rule.icms_aliquota
        model.icms_perc_reducao_bc = rule.icms_perc_reducao_bc
        model.pis_cst = rule.pis_cst
        model.cofins_cst = rule.cofins_cst
        model.ibs_cbs_cst = rule.ibs_cbs_cst
        model.ibs_aliquota_uf = rule.ibs_aliquota_uf
        model.ibs_aliquota_mun = rule.ibs_aliquota_mun
        model.cbs_aliquota = rule.cbs_aliquota
        model.is_cst = rule.is_cst
        model.is_aliquota = rule.is_aliquota
        model.updated_at = rule.updated_at
        
        self.session.flush()
        return self._to_entity(model)

    def delete(self, rule_id: str, tenant_id: str) -> bool:
        model = (
            self.session.query(FiscalRuleModel)
            .filter_by(id=rule_id, tenant_id=tenant_id)
            .first()
        )
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False
