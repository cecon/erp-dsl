"""SQLAlchemy ORM models for the fiscal module."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, Numeric, String

from src.infrastructure.persistence.sqlalchemy.models import Base


class TaxGroupModel(Base):
    """Grupo Tributário."""

    __tablename__ = "tax_groups"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    descricao = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    version = Column(Integer, nullable=False, default=1)


class OperationNatureModel(Base):
    """Natureza de Operação."""

    __tablename__ = "operation_natures"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    descricao = Column(String(255), nullable=False)
    tipo_movimento = Column(String(16), nullable=False)  # Entrada/Saída
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    version = Column(Integer, nullable=False, default=1)


class FiscalRuleModel(Base):
    """Regra Fiscal — Matriz de cruzamento tributário."""

    __tablename__ = "fiscal_rules"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)

    # ── Filter fields ────────────────────────────────────────────
    id_grupo_tributario = Column(String(36), nullable=False, index=True)
    id_natureza_operacao = Column(String(36), nullable=False, index=True)
    uf_origem = Column(String(2), nullable=False, default="")
    uf_destino = Column(String(2), nullable=False, default="")
    tipo_contribuinte_dest = Column(String(32), nullable=False, default="")

    # ── Output: current model (ICMS/PIS/COFINS) ─────────────────
    cfop = Column(String(8), nullable=False, default="")
    icms_cst = Column(String(4), nullable=False, default="")
    icms_csosn = Column(String(4), nullable=False, default="")
    icms_aliquota = Column(Numeric(6, 2), nullable=False, default=0)
    icms_perc_reducao_bc = Column(Numeric(6, 2), nullable=False, default=0)
    pis_cst = Column(String(4), nullable=False, default="")
    cofins_cst = Column(String(4), nullable=False, default="")

    # ── Output: tax reform (IBS/CBS/IS — NT 2025.002) ────────────
    ibs_cbs_cst = Column(String(4), nullable=False, default="")
    ibs_aliquota_uf = Column(Numeric(6, 2), nullable=False, default=0)
    ibs_aliquota_mun = Column(Numeric(6, 2), nullable=False, default=0)
    cbs_aliquota = Column(Numeric(6, 2), nullable=False, default=0)
    is_cst = Column(String(4), nullable=False, default="")
    is_aliquota = Column(Numeric(6, 2), nullable=False, default=0)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    version = Column(Integer, nullable=False, default=1)
