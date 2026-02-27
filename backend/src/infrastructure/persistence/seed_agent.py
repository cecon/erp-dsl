"""Seed script for agent testing — LLM provider + sample NCM entries.

Run standalone:
    cd backend
    source .venv/bin/activate
    PYTHONPATH=. GEMINI_API_KEY=xxx ERP_DATABASE_URL=postgresql://...
    python src/infrastructure/persistence/seed_agent.py
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.infrastructure.config.settings import settings
from src.infrastructure.persistence.sqlalchemy.models import Base
from src.infrastructure.persistence.sqlalchemy.agent_models import LLMProviderModel
from src.infrastructure.persistence.sqlalchemy.fiscal_catalog_models import NCMModel
import src.infrastructure.persistence.sqlalchemy.tax_models  # noqa: F401

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"

# ── Sample NCM data ─────────────────────────────────────────────────

SAMPLE_NCMS = [
    {
        "codigo": "04029900",
        "descricao": "Outros leites e cremes de leite, concentrados ou adicionados de açúcar - Leite condensado",
        "sujeito_is": False,
        "cclass_trib_is": None,
    },
    {
        "codigo": "22021000",
        "descricao": "Águas, incluindo as águas minerais e as águas gaseificadas, adicionadas de açúcar",
        "sujeito_is": False,
        "cclass_trib_is": None,
    },
    {
        "codigo": "21069090",
        "descricao": "Outras preparações alimentícias não especificadas nem compreendidas noutras posições",
        "sujeito_is": False,
        "cclass_trib_is": None,
    },
]


def seed_agent_data() -> None:
    """Idempotent seed: inserts LLM provider and NCMs if they don't exist."""
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        print("WARNING: GEMINI_API_KEY not set, using empty string")

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # ── LLM Provider ─────────────────────────────────────────
        existing = session.execute(
            select(LLMProviderModel).where(
                LLMProviderModel.tenant_id == DEFAULT_TENANT_ID,
                LLMProviderModel.provider == "google",
            )
        ).scalar_one_or_none()

        if existing:
            # Update the API key if it changed
            if existing.api_key_encrypted != gemini_key and gemini_key:
                existing.api_key_encrypted = gemini_key
                existing.is_active = True
                print(f"Updated LLM provider API key (id={existing.id})")
            else:
                print(f"LLM provider already exists (id={existing.id})")
        else:
            provider = LLMProviderModel(
                id=str(uuid.uuid4()),
                tenant_id=DEFAULT_TENANT_ID,
                provider="google",
                model="gemini-2.0-flash",
                api_key_encrypted=gemini_key,
                base_url=None,
                params=None,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                version=1,
            )
            session.add(provider)
            print(f"Created LLM provider: google/gemini-2.0-flash")

        # ── NCM entries ──────────────────────────────────────────
        for ncm_data in SAMPLE_NCMS:
            existing_ncm = session.get(NCMModel, ncm_data["codigo"])
            if existing_ncm:
                print(f"NCM {ncm_data['codigo']} already exists")
            else:
                ncm = NCMModel(
                    codigo=ncm_data["codigo"],
                    descricao=ncm_data["descricao"],
                    sujeito_is=ncm_data["sujeito_is"],
                    cclass_trib_is=ncm_data["cclass_trib_is"],
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(ncm)
                print(f"Created NCM: {ncm_data['codigo']} — {ncm_data['descricao'][:50]}")

        session.commit()
        print("\nSeed completed successfully!")

    except Exception as exc:
        session.rollback()
        print(f"Seed failed: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_agent_data()
