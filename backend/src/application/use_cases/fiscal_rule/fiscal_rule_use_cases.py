"""Fiscal Rule use cases."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from src.application.ports.fiscal_rule_repository_port import (
    FiscalRuleRepositoryPort,
)
from src.domain.entities.fiscal_rule import FiscalRule


class ListFiscalRulesUseCase:
    """Use case to list fiscal rules for a tenant."""

    def __init__(self, repository: FiscalRuleRepositoryPort) -> None:
        self.repository = repository

    def execute(
        self, tenant_id: str, limit: int = 50, offset: int = 0
    ) -> list[FiscalRule]:
        return self.repository.list_all(tenant_id, limit, offset)


class GetFiscalRuleUseCase:
    """Use case to get a single fiscal rule by ID."""

    def __init__(self, repository: FiscalRuleRepositoryPort) -> None:
        self.repository = repository

    def execute(self, rule_id: str, tenant_id: str) -> FiscalRule | None:
        return self.repository.get_by_id(rule_id, tenant_id)


class CreateFiscalRuleUseCase:
    """Use case to create a new fiscal rule."""

    def __init__(self, repository: FiscalRuleRepositoryPort) -> None:
        self.repository = repository

    def execute(
        self,
        tenant_id: str,
        id_grupo_tributario: str,
        id_natureza_operacao: str,
        uf_origem: str = "",
        uf_destino: str = "",
        tipo_contribuinte_dest: str = "",
        cfop: str = "",
        icms_cst: str = "",
        icms_csosn: str = "",
        icms_aliquota: Decimal | None = None,
        icms_perc_reducao_bc: Decimal | None = None,
        pis_cst: str = "",
        cofins_cst: str = "",
        ibs_cbs_cst: str = "",
        ibs_aliquota_uf: Decimal | None = None,
        ibs_aliquota_mun: Decimal | None = None,
        cbs_aliquota: Decimal | None = None,
        is_cst: str = "",
        is_aliquota: Decimal | None = None,
    ) -> FiscalRule:
        now = datetime.now(timezone.utc)
        
        rule = FiscalRule(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            id_grupo_tributario=id_grupo_tributario,
            id_natureza_operacao=id_natureza_operacao,
            uf_origem=uf_origem,
            uf_destino=uf_destino,
            tipo_contribuinte_dest=tipo_contribuinte_dest,
            cfop=cfop,
            icms_cst=icms_cst,
            icms_csosn=icms_csosn,
            icms_aliquota=icms_aliquota or Decimal("0"),
            icms_perc_reducao_bc=icms_perc_reducao_bc or Decimal("0"),
            pis_cst=pis_cst,
            cofins_cst=cofins_cst,
            ibs_cbs_cst=ibs_cbs_cst,
            ibs_aliquota_uf=ibs_aliquota_uf or Decimal("0"),
            ibs_aliquota_mun=ibs_aliquota_mun or Decimal("0"),
            cbs_aliquota=cbs_aliquota or Decimal("0"),
            is_cst=is_cst,
            is_aliquota=is_aliquota or Decimal("0"),
            created_at=now,
            updated_at=now,
        )

        return self.repository.save(rule)


class UpdateFiscalRuleUseCase:
    """Use case to update an existing fiscal rule."""

    def __init__(self, repository: FiscalRuleRepositoryPort) -> None:
        self.repository = repository

    def execute(
        self,
        rule_id: str,
        tenant_id: str,
        id_grupo_tributario: str | None = None,
        id_natureza_operacao: str | None = None,
        uf_origem: str | None = None,
        uf_destino: str | None = None,
        tipo_contribuinte_dest: str | None = None,
        cfop: str | None = None,
        icms_cst: str | None = None,
        icms_csosn: str | None = None,
        icms_aliquota: Decimal | None = None,
        icms_perc_reducao_bc: Decimal | None = None,
        pis_cst: str | None = None,
        cofins_cst: str | None = None,
        ibs_cbs_cst: str | None = None,
        ibs_aliquota_uf: Decimal | None = None,
        ibs_aliquota_mun: Decimal | None = None,
        cbs_aliquota: Decimal | None = None,
        is_cst: str | None = None,
        is_aliquota: Decimal | None = None,
    ) -> FiscalRule:
        rule = self.repository.get_by_id(rule_id, tenant_id)
        if not rule:
            raise ValueError(f"Fiscal Rule {rule_id} not found")

        if id_grupo_tributario is not None:
            rule.id_grupo_tributario = id_grupo_tributario
        if id_natureza_operacao is not None:
            rule.id_natureza_operacao = id_natureza_operacao
        if uf_origem is not None:
            rule.uf_origem = uf_origem
        if uf_destino is not None:
            rule.uf_destino = uf_destino
        if tipo_contribuinte_dest is not None:
            rule.tipo_contribuinte_dest = tipo_contribuinte_dest
        if cfop is not None:
            rule.cfop = cfop
        if icms_cst is not None:
            rule.icms_cst = icms_cst
        if icms_csosn is not None:
            rule.icms_csosn = icms_csosn
        if icms_aliquota is not None:
            rule.icms_aliquota = icms_aliquota
        if icms_perc_reducao_bc is not None:
            rule.icms_perc_reducao_bc = icms_perc_reducao_bc
        if pis_cst is not None:
            rule.pis_cst = pis_cst
        if cofins_cst is not None:
            rule.cofins_cst = cofins_cst
        if ibs_cbs_cst is not None:
            rule.ibs_cbs_cst = ibs_cbs_cst
        if ibs_aliquota_uf is not None:
            rule.ibs_aliquota_uf = ibs_aliquota_uf
        if ibs_aliquota_mun is not None:
            rule.ibs_aliquota_mun = ibs_aliquota_mun
        if cbs_aliquota is not None:
            rule.cbs_aliquota = cbs_aliquota
        if is_cst is not None:
            rule.is_cst = is_cst
        if is_aliquota is not None:
            rule.is_aliquota = is_aliquota
            
        rule.updated_at = datetime.now(timezone.utc)

        return self.repository.update(rule)


class DeleteFiscalRuleUseCase:
    """Use case to delete a fiscal rule."""

    def __init__(self, repository: FiscalRuleRepositoryPort) -> None:
        self.repository = repository

    def execute(self, rule_id: str, tenant_id: str) -> bool:
        return self.repository.delete(rule_id, tenant_id)
