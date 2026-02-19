"""Auth router — login endpoint returning JWT."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.http.dependency_injection import auth_adapter, get_db
from src.infrastructure.persistence.sqlalchemy.models import UserModel

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    username: str
    role: str


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    stmt = select(UserModel).where(UserModel.username == body.username)
    user = db.execute(stmt).scalar_one_or_none()

    if not user or not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = auth_adapter.create_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        username=user.username,
        role=user.role,
    )

    return LoginResponse(
        access_token=token,
        tenant_id=user.tenant_id,
        username=user.username,
        role=user.role,
    )
