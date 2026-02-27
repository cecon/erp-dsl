"""Startup script — runs migrations, seeds database, then starts uvicorn."""

import subprocess
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from src.adapters.http.dependency_injection import SessionLocal
from src.infrastructure.persistence.seed import seed_database


def main() -> None:
    # Run Alembic migrations (replaces Base.metadata.create_all)
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    # Seed
    session = SessionLocal()
    try:
        seed_database(session)
    finally:
        session.close()

    # Start uvicorn
    subprocess.run(
        [
            sys.executable, "-m", "uvicorn",
            "src.adapters.http.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()

