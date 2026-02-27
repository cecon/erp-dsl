"""SQLAlchemy ORM models for fiscal catalog data.

These are shared reference tables (no tenant_id) — NCM, CEST, and
Classificação Tributária. They are populated via migrations/seeds and
are NOT managed by the GenericCrudRepository.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Numeric, String, Text

from src.infrastructure.persistence.sqlalchemy.models import Base


class NCMModel(Base):
    """Nomenclatura Comum do Mercosul."""

    __tablename__ = "ncm"

    codigo = Column(String(8), primary_key=True)
    descricao = Column(Text, nullable=False)
    sujeito_is = Column(Boolean, nullable=False, default=False)
    cclass_trib_is = Column(String(16), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CESTModel(Base):
    """Código Especificador da Substituição Tributária."""

    __tablename__ = "cest"

    codigo = Column(String(7), primary_key=True)
    descricao = Column(Text, nullable=False)
    ncm_codigo = Column(String(8), nullable=False, index=True)


class ClassificacaoTributariaModel(Base):
    """Classificação Tributária (IBS/CBS — Reforma Tributária)."""

    __tablename__ = "classificacoes_tributarias"

    codigo = Column(String(16), primary_key=True)
    descricao = Column(Text, nullable=False)
    cst_ibs_cbs = Column(String(4), nullable=False)
    regime = Column(String(32), nullable=False)
    permite_reducao = Column(Boolean, nullable=False, default=False)
    percentual_reducao = Column(Numeric(6, 2), nullable=True)
    exige_diferimento = Column(Boolean, nullable=False, default=False)
    exige_is = Column(Boolean, nullable=False, default=False)
