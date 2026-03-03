"""Router for LLM utility endpoints (model listing, etc.)."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.adapters.http.dependency_injection import get_tenant_db
from src.infrastructure.persistence.sqlalchemy.agent_models import LLMProviderModel

router = APIRouter()

GOOGLE_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"


@router.get("/models")
async def list_available_models(
    api_key: str = Query(..., description="API key to authenticate with the provider"),
) -> list[dict[str, str]]:
    """Fetch available models from Google's API and return as select options."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                GOOGLE_MODELS_URL,
                params={"key": api_key},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Google API error: {exc.response.text[:200]}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach Google API: {exc}",
        )

    models = data.get("models", [])

    # Filter to models that support generateContent and return as select options
    options: list[dict[str, str]] = []
    for m in models:
        name = m.get("name", "")  # e.g. "models/gemini-2.5-flash"
        display_name = m.get("displayName", name)
        supported = m.get("supportedGenerationMethods", [])

        if "generateContent" in supported:
            # Strip "models/" prefix for the value
            model_id = name.replace("models/", "")
            options.append({
                "value": model_id,
                "label": display_name,
            })

    return options
