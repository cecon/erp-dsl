"""Startup script — runs migrations, seeds database, then starts uvicorn."""

import subprocess
import sys

from sqlalchemy.orm import Session

from src.adapters.http.dependency_injection import SessionLocal, engine
from src.infrastructure.persistence.sqlalchemy.models import Base
from src.infrastructure.persistence.seed import seed_database


def main() -> None:
    # Create tables
    Base.metadata.create_all(bind=engine)

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
