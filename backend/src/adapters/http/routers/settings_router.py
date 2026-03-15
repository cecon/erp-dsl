"""Settings router — Personal API Token management.

Allows authenticated users to create, list and revoke their own
API tokens. These tokens can be used instead of a JWT to authenticate
API calls (ChatGPT Actions, MCP, external tools).

Token flow:
  1. User POSTs /settings/tokens with a name.
  2. Server generates a secure random token, stores its SHA-256 hash,
     and returns the raw token ONCE (it cannot be retrieved again).
  3. User configures their tool (ChatGPT, Claude, etc.) with this token
     as an API key via the X-API-Key header or Authorization: Bearer.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.http.dependency_injection import get_current_user, get_db
from src.application.ports.auth_port import AuthContext
from src.infrastructure.persistence.sqlalchemy.api_token_model import ApiTokenModel

router = APIRouter()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class CreateTokenRequest(BaseModel):
    name: str


class TokenResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None


class CreatedTokenResponse(TokenResponse):
    token: str  # raw token — shown only once


@router.get("/tokens", response_model=List[TokenResponse])
def list_tokens(
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[TokenResponse]:
    """Lista todos os tokens de API do usuário autenticado."""
    tokens = db.execute(
        select(ApiTokenModel).where(
            ApiTokenModel.user_id == auth.user_id,
            ApiTokenModel.is_active == True,  # noqa: E712
        ).order_by(ApiTokenModel.created_at.desc())
    ).scalars().all()
    return [
        TokenResponse(
            id=t.id,
            name=t.name,
            is_active=t.is_active,
            created_at=t.created_at,
            last_used_at=t.last_used_at,
        )
        for t in tokens
    ]


@router.post("/tokens", response_model=CreatedTokenResponse, status_code=201)
def create_token(
    body: CreateTokenRequest,
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CreatedTokenResponse:
    """Cria um novo token de API para o usuário autenticado.

    O token raw é retornado apenas uma vez — armazene-o em lugar seguro.
    """
    if not body.name or len(body.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Token name is required (min 2 chars)")

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)

    record = ApiTokenModel(
        id=str(uuid.uuid4()),
        user_id=auth.user_id,
        tenant_id=auth.tenant_id,
        name=body.name.strip(),
        token_hash=token_hash,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return CreatedTokenResponse(
        id=record.id,
        name=record.name,
        is_active=record.is_active,
        created_at=record.created_at,
        last_used_at=None,
        token=raw_token,
    )


@router.delete("/tokens/{token_id}")
def revoke_token(
    token_id: str,
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Revoga (desativa) um token de API do usuário autenticado."""
    token = db.execute(
        select(ApiTokenModel).where(
            ApiTokenModel.id == token_id,
            ApiTokenModel.user_id == auth.user_id,
        )
    ).scalar_one_or_none()

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    token.is_active = False
    db.commit()
    return Response(status_code=204)
