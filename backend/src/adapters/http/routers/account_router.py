"""Account management router — signup, login, plans, projects, apps."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.http.dependency_injection import (
    auth_adapter,
    get_current_user,
    get_db,
)
from src.application.ports.auth_port import AuthContext
from src.infrastructure.persistence.sqlalchemy.account_models import (
    AccountModel,
    PlanModel,
    ProjectAppModel,
    ProjectCompanyModel,
    ProjectDatabaseModel,
    ProjectModel,
    SubscriptionModel,
)

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Schemas ──────────────────────────────────────────────────────────

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


class PlanOut(BaseModel):
    id: str
    name: str
    slug: str
    price: float
    enabled: bool
    features: dict


class ProjectCreate(BaseModel):
    name: str


class ProjectOut(BaseModel):
    id: str
    name: str
    slug: str
    status: str
    created_at: datetime


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


class DatabaseOut(BaseModel):
    id: str
    app_id: str
    db_name: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    status: str


# ── Helpers ──────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")[:64]


# ── Signup & Login (public) ──────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    existing = db.execute(
        select(AccountModel).where(AccountModel.email == body.email)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    account_id = str(uuid.uuid4())
    account = AccountModel(
        id=account_id,
        email=body.email,
        name=body.name,
        password_hash=pwd_context.hash(body.password),
    )
    db.add(account)

    # Auto-subscribe to free plan
    free_plan = db.execute(
        select(PlanModel).where(PlanModel.slug == "free")
    ).scalar_one_or_none()
    if free_plan:
        sub = SubscriptionModel(
            id=str(uuid.uuid4()),
            account_id=account_id,
            plan_id=free_plan.id,
            status="active",
        )
        db.add(sub)

    db.commit()

    token = auth_adapter.create_token(
        user_id=account_id,
        tenant_id=account_id,
        username=body.email,
        role="owner",
    )
    return TokenResponse(
        access_token=token,
        account_id=account_id,
        email=body.email,
        name=body.name,
    )


@router.post("/login", response_model=TokenResponse)
def account_login(body: LoginRequest, db: Session = Depends(get_db)):
    acct = db.execute(
        select(AccountModel).where(AccountModel.email == body.email)
    ).scalar_one_or_none()

    if not acct or not pwd_context.verify(
        body.password, acct.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = auth_adapter.create_token(
        user_id=acct.id,
        tenant_id=acct.id,
        username=acct.email,
        role="owner",
    )
    return TokenResponse(
        access_token=token,
        account_id=acct.id,
        email=acct.email,
        name=acct.name,
    )


# ── Me ───────────────────────────────────────────────────────────────

@router.get("/me")
def get_me(auth: AuthContext = Depends(get_current_user)):
    return {
        "account_id": auth.user_id,
        "email": auth.username,
        "role": auth.role,
    }


# ── Plans (public) ──────────────────────────────────────────────────

@router.get("/plans", response_model=list[PlanOut])
def list_plans(db: Session = Depends(get_db)):
    rows = db.execute(select(PlanModel)).scalars().all()
    return [
        PlanOut(
            id=p.id, name=p.name, slug=p.slug,
            price=float(p.price), enabled=p.enabled,
            features=p.features or {},
        )
        for p in rows
    ]


# ── Projects (protected) ────────────────────────────────────────────

@router.post("/projects", response_model=ProjectOut)
def create_project(
    body: ProjectCreate,
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account_id = auth.user_id

    sub = db.execute(
        select(SubscriptionModel).where(
            SubscriptionModel.account_id == account_id,
            SubscriptionModel.status == "active",
        )
    ).scalar_one_or_none()

    if not sub:
        raise HTTPException(400, "No active subscription")

    project_id = str(uuid.uuid4())
    project = ProjectModel(
        id=project_id,
        account_id=account_id,
        subscription_id=sub.id,
        name=body.name,
        slug=_slugify(body.name),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut(
        id=project.id, name=project.name,
        slug=project.slug, status=project.status,
        created_at=project.created_at,
    )


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(ProjectModel).where(
            ProjectModel.account_id == auth.user_id,
        )
    ).scalars().all()
    return [
        ProjectOut(
            id=p.id, name=p.name, slug=p.slug,
            status=p.status, created_at=p.created_at,
        )
        for p in rows
    ]


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = db.get(ProjectModel, project_id)
    if not p or p.account_id != auth.user_id:
        raise HTTPException(404, "Project not found")
    return ProjectOut(
        id=p.id, name=p.name, slug=p.slug,
        status=p.status, created_at=p.created_at,
    )


# ── Company (protected) ─────────────────────────────────────────────

@router.post(
    "/projects/{project_id}/company",
    response_model=CompanyOut,
)
def upsert_company(
    project_id: str,
    body: CompanyCreate,
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.execute(
        select(ProjectCompanyModel).where(
            ProjectCompanyModel.project_id == project_id,
        )
    ).scalar_one_or_none()

    if existing:
        for k, v in body.model_dump(exclude_unset=True).items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        c = existing
    else:
        c = ProjectCompanyModel(
            id=str(uuid.uuid4()),
            project_id=project_id,
            **body.model_dump(),
        )
        db.add(c)
        db.commit()
        db.refresh(c)

    return CompanyOut(
        id=c.id, project_id=c.project_id, type=c.type,
        razao_social=c.razao_social,
        nome_fantasia=c.nome_fantasia,
        cnpj_cpf=c.cnpj_cpf,
    )


@router.get(
    "/projects/{project_id}/company",
    response_model=CompanyOut | None,
)
def get_company(
    project_id: str,
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.execute(
        select(ProjectCompanyModel).where(
            ProjectCompanyModel.project_id == project_id,
        )
    ).scalar_one_or_none()
    if not c:
        return None
    return CompanyOut(
        id=c.id, project_id=c.project_id, type=c.type,
        razao_social=c.razao_social,
        nome_fantasia=c.nome_fantasia,
        cnpj_cpf=c.cnpj_cpf,
    )


# ── Apps (protected) ────────────────────────────────────────────────

@router.post(
    "/projects/{project_id}/apps",
    response_model=AppOut,
)
def create_app(
    project_id: str,
    body: AppCreate,
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app_id = str(uuid.uuid4())
    app = ProjectAppModel(
        id=app_id,
        project_id=project_id,
        name=body.name,
        slug=_slugify(body.name),
        llm_provider=body.llm_provider,
        llm_model=body.llm_model,
        llm_api_key=body.llm_api_key,
    )
    db.add(app)
    db.flush()

    # Provision isolated database
    from src.infrastructure.persistence.database_provisioning import (
        provision_database,
    )
    provision_database(session=db, app_id=app_id)

    db.commit()
    db.refresh(app)
    return AppOut(
        id=app.id, project_id=app.project_id,
        name=app.name, slug=app.slug,
        status=app.status,
        llm_provider=app.llm_provider,
        llm_model=app.llm_model,
        created_at=app.created_at,
    )


@router.get(
    "/projects/{project_id}/apps",
    response_model=list[AppOut],
)
def list_apps(
    project_id: str,
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(ProjectAppModel).where(
            ProjectAppModel.project_id == project_id,
        )
    ).scalars().all()
    return [
        AppOut(
            id=a.id, project_id=a.project_id,
            name=a.name, slug=a.slug,
            status=a.status,
            llm_provider=a.llm_provider,
            llm_model=a.llm_model,
            created_at=a.created_at,
        )
        for a in rows
    ]


# ── Database info (protected) ───────────────────────────────────────

@router.get("/apps/{app_id}/database", response_model=DatabaseOut)
def get_database_info(
    app_id: str,
    auth: AuthContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = db.execute(
        select(ProjectDatabaseModel).where(
            ProjectDatabaseModel.app_id == app_id,
        )
    ).scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "Database not provisioned")
    return DatabaseOut(
        id=rec.id, app_id=rec.app_id,
        db_name=rec.db_name, db_host=rec.db_host,
        db_port=rec.db_port, db_user=rec.db_user,
        db_password=rec.db_password, status=rec.status,
    )
