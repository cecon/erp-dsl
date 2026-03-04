"""Pydantic schemas for the Account/Platform HTTP adapter."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


# ── Auth ─────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    account_id: str
    email: str
    name: str


# ── Plans ────────────────────────────────────────────────────────────

class PlanOut(BaseModel):
    id: str
    name: str
    slug: str
    price: float
    enabled: bool
    features: dict


# ── Projects ─────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str


class ProjectOut(BaseModel):
    id: str
    name: str
    slug: str
    status: str
    created_at: datetime


# ── Company ──────────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    type: str = "pj"
    razao_social: str | None = None
    nome_fantasia: str | None = None
    cnpj_cpf: str | None = None
    ie: str | None = None
    im: str | None = None
    endereco: dict | None = None


class CompanyOut(BaseModel):
    id: str
    project_id: str
    type: str
    razao_social: str | None
    nome_fantasia: str | None
    cnpj_cpf: str | None


# ── Apps ─────────────────────────────────────────────────────────────

class AppCreate(BaseModel):
    name: str
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None


class AppOut(BaseModel):
    id: str
    project_id: str
    name: str
    slug: str
    status: str
    llm_provider: str | None
    llm_model: str | None
    created_at: datetime


# ── Database ─────────────────────────────────────────────────────────

class DatabaseOut(BaseModel):
    id: str
    app_id: str
    db_name: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    status: str
