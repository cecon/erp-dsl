"""Account management router — signup, login, plans, projects, apps.

Each handler delegates to the appropriate Use Case.
Zero business logic — only HTTP translation and dependency injection.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.adapters.http.dependency_injection import (
    get_current_user,
    get_create_app_use_case,
    get_create_project_use_case,
    get_login_use_case,
    get_signup_use_case,
    get_account_repo,
)
from src.adapters.http.schemas.account_schemas import (
    AppCreate,
    AppOut,
    CompanyCreate,
    CompanyOut,
    DatabaseOut,
    LoginRequest,
    PlanOut,
    ProjectCreate,
    ProjectOut,
    SignupRequest,
    TokenResponse,
)
from src.application.ports.auth_port import AuthContext
from src.application.use_cases.account.create_app import CreateAppUseCase
from src.application.use_cases.account.create_project import CreateProjectUseCase
from src.application.use_cases.account.login import LoginUseCase
from src.application.use_cases.account.signup import SignupUseCase
from src.domain.entities.account import Company

router = APIRouter()


# ── Signup & Login (public) ──────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse)
def signup(
    body: SignupRequest,
    use_case: SignupUseCase = Depends(get_signup_use_case),
):
    try:
        result = use_case.execute(
            email=body.email, name=body.name, password=body.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc),
        )
    return TokenResponse(**result)


@router.post("/login", response_model=TokenResponse)
def account_login(
    body: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case),
):
    try:
        result = use_case.execute(email=body.email, password=body.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc),
        )
    return TokenResponse(**result)


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
def list_plans(repo=Depends(get_account_repo)):
    plans = repo.list_plans()
    return [
        PlanOut(
            id=p.id, name=p.name, slug=p.slug,
            price=p.price, enabled=p.enabled, features=p.features,
        )
        for p in plans
    ]


# ── Projects (protected) ────────────────────────────────────────────

@router.post("/projects", response_model=ProjectOut)
def create_project(
    body: ProjectCreate,
    auth: AuthContext = Depends(get_current_user),
    use_case: CreateProjectUseCase = Depends(get_create_project_use_case),
):
    try:
        project = use_case.execute(
            account_id=auth.user_id, name=body.name,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return ProjectOut(
        id=project.id, name=project.name, slug=project.slug,
        status=project.status, created_at=project.created_at,
    )


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(
    auth: AuthContext = Depends(get_current_user),
    repo=Depends(get_account_repo),
):
    projects = repo.list_projects_by_account(auth.user_id)
    return [
        ProjectOut(
            id=p.id, name=p.name, slug=p.slug,
            status=p.status, created_at=p.created_at,
        )
        for p in projects
    ]


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    auth: AuthContext = Depends(get_current_user),
    repo=Depends(get_account_repo),
):
    p = repo.get_project(project_id)
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
    repo=Depends(get_account_repo),
):
    company = Company(
        project_id=project_id,
        **body.model_dump(),
    )
    saved = repo.upsert_company(company)
    return CompanyOut(
        id=saved.id, project_id=saved.project_id, type=saved.type,
        razao_social=saved.razao_social,
        nome_fantasia=saved.nome_fantasia,
        cnpj_cpf=saved.cnpj_cpf,
    )


@router.get(
    "/projects/{project_id}/company",
    response_model=CompanyOut | None,
)
def get_company(
    project_id: str,
    auth: AuthContext = Depends(get_current_user),
    repo=Depends(get_account_repo),
):
    c = repo.get_company(project_id)
    if not c:
        return None
    return CompanyOut(
        id=c.id, project_id=c.project_id, type=c.type,
        razao_social=c.razao_social,
        nome_fantasia=c.nome_fantasia,
        cnpj_cpf=c.cnpj_cpf,
    )


# ── Apps (protected) ────────────────────────────────────────────────

@router.post("/projects/{project_id}/apps", response_model=AppOut)
def create_app(
    project_id: str,
    body: AppCreate,
    auth: AuthContext = Depends(get_current_user),
    use_case: CreateAppUseCase = Depends(get_create_app_use_case),
):
    app = use_case.execute(
        project_id=project_id,
        name=body.name,
        llm_provider=body.llm_provider,
        llm_model=body.llm_model,
        llm_api_key=body.llm_api_key,
    )
    return AppOut(
        id=app.id, project_id=app.project_id,
        name=app.name, slug=app.slug,
        status=app.status,
        llm_provider=app.llm_provider,
        llm_model=app.llm_model,
        created_at=app.created_at,
    )


@router.get("/projects/{project_id}/apps", response_model=list[AppOut])
def list_apps(
    project_id: str,
    auth: AuthContext = Depends(get_current_user),
    repo=Depends(get_account_repo),
):
    apps = repo.list_apps_by_project(project_id)
    return [
        AppOut(
            id=a.id, project_id=a.project_id,
            name=a.name, slug=a.slug,
            status=a.status,
            llm_provider=a.llm_provider,
            llm_model=a.llm_model,
            created_at=a.created_at,
        )
        for a in apps
    ]


# ── Database info (protected) ───────────────────────────────────────

@router.get("/apps/{app_id}/database", response_model=DatabaseOut)
def get_database_info(
    app_id: str,
    auth: AuthContext = Depends(get_current_user),
    repo=Depends(get_account_repo),
):
    info = repo.get_database_info(app_id)
    if not info:
        raise HTTPException(404, "Database not provisioned")
    return DatabaseOut(
        id=info.id, app_id=info.app_id,
        db_name=info.db_name, db_host=info.db_host,
        db_port=info.db_port, db_user=info.db_user,
        db_password=info.db_password, status=info.status,
    )
