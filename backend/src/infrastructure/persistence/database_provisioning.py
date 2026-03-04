"""Service for provisioning isolated tenant databases.

Connects to the master PostgreSQL instance and creates a dedicated
database + user for each project app.
"""

from __future__ import annotations

import secrets
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.infrastructure.config.settings import settings
from src.infrastructure.persistence.sqlalchemy.account_models import (
    ProjectDatabaseModel,
)


def _admin_engine():
    """Engine connected to the default ``postgres`` database for DDL."""
    base = settings.database_url.rsplit("/", 1)[0]
    url = f"{base}/postgres"
    return create_engine(url, isolation_level="AUTOCOMMIT")


def _short_id(app_id: str) -> str:
    return app_id.replace("-", "")[:12]


def provision_database(
    session: Session,
    app_id: str,
) -> ProjectDatabaseModel:
    """Create an isolated database and user for the given app.

    Returns
    -------
    ProjectDatabaseModel
        The persisted record with connection credentials.
    """
    short = _short_id(app_id)
    db_name = f"erpdsl_app_{short}"
    db_user = f"app_{short}"
    db_password = secrets.token_urlsafe(24)

    engine = _admin_engine()

    with engine.connect() as conn:
        # Create dedicated user
        conn.execute(
            text(
                f"DO $$ BEGIN "
                f"  IF NOT EXISTS ("
                f"    SELECT FROM pg_catalog.pg_roles "
                f"    WHERE rolname = '{db_user}'"
                f"  ) THEN "
                f"    CREATE ROLE {db_user} LOGIN "
                f"    PASSWORD '{db_password}';"
                f"  END IF; "
                f"END $$;"
            )
        )

        # Create database
        exists = conn.execute(
            text(
                "SELECT 1 FROM pg_database "
                f"WHERE datname = '{db_name}'"
            )
        ).scalar()

        if not exists:
            conn.execute(text(f"CREATE DATABASE {db_name} OWNER {db_user}"))

    # Parse host/port from the main database_url
    # Format: postgresql://user:pass@host:port/dbname
    url_parts = settings.database_url.split("@")[1]
    host_port = url_parts.split("/")[0]
    if ":" in host_port:
        db_host, db_port_str = host_port.split(":")
        db_port = int(db_port_str)
    else:
        db_host = host_port
        db_port = 5432

    record = ProjectDatabaseModel(
        id=str(uuid.uuid4()),
        app_id=app_id,
        db_name=db_name,
        db_host=db_host,
        db_port=db_port,
        db_user=db_user,
        db_password=db_password,
        status="ready",
    )
    session.add(record)
    session.flush()

    engine.dispose()
    return record
