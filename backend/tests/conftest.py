"""Test configuration — fixtures for API and unit tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.adapters.http.dependency_injection import get_db, get_tenant_db
from src.adapters.http.main import create_app
from src.infrastructure.config.settings import settings
from src.infrastructure.persistence.sqlalchemy.models import Base
from src.infrastructure.persistence.sqlalchemy.tenant_context import (
    enable_tenant_filter,
)
import src.infrastructure.persistence.sqlalchemy.tax_models  # noqa: F401


TENANT_A = "00000000-0000-0000-0000-000000000001"
TENANT_B = "00000000-0000-0000-0000-000000000099"


@pytest.fixture(scope="session")
def engine():
    """Create an engine connected to the test database."""
    return create_engine(settings.database_url, pool_pre_ping=True)


@pytest.fixture(scope="session")
def tables(engine):
    """Ensure all tables exist."""
    Base.metadata.create_all(bind=engine)
    yield
    # Don't drop — tests run against the dev DB


@pytest.fixture()
def db_session(engine, tables):
    """Provide a transactional session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    enable_tenant_filter(Session)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def app(db_session):
    """Create a FastAPI app with overridden DB dependencies."""
    application = create_app()

    def _override_get_db():
        yield db_session

    def _override_get_tenant_db(tenant_id: str = TENANT_A):
        db_session.info["tenant_id"] = tenant_id
        return db_session

    application.dependency_overrides[get_db] = _override_get_db
    # We only override get_db; get_tenant_db depends on get_db + get_current_user
    # Auth is tested separately via real token
    yield application
    application.dependency_overrides.clear()


@pytest.fixture()
def client(app):
    """Provide an HTTP test client."""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def auth_token(client) -> str:
    """Get a valid JWT token via the login endpoint."""
    resp = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture()
def auth_headers(auth_token) -> dict:
    """Authorization headers dict."""
    return {"Authorization": f"Bearer {auth_token}"}
