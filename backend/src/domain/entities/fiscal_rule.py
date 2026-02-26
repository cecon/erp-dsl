"""Fiscal Rule entity — represents the tax calculation matrix."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class FiscalRule:
    """Core domain entity for Fiscal Rules."""

    id: str
    tenant_id: str

    # Filter fields
    id_grupo_tributario: str
    id_natureza_operacao: str
    uf_origem: str
    uf_destino: str
    tipo_contribuinte_dest: str

    # Current model taxes (ICMS/PIS/COFINS)
    cfop: str
    icms_cst: str
    icms_csosn: str
    icms_aliquota: Decimal
    icms_perc_reducao_bc: Decimal
    pis_cst: str
    cofins_cst: str

    # Tax reform axes (IBS/CBS/IS - NT 2025.002)
    ibs_cbs_cst: str
    ibs_aliquota_uf: Decimal
    ibs_aliquota_mun: Decimal
    cbs_aliquota: Decimal
    is_cst: str
    is_aliquota: Decimal

    created_at: datetime
    updated_at: datetime
