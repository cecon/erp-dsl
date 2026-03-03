"""Skill: rollback_page_version — revert to a previous page version.

Used by Otto when the user wants to undo a schema change.

Contract: async def rollback_page_version(params: dict, context: dict) -> dict
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.application.agent import skill_registry
from src.infrastructure.persistence.sqlalchemy.models import PageVersionModel

logger = logging.getLogger(__name__)


async def rollback_page_version(params: dict, context: dict) -> dict:
    """Rollback to a previous version of a page schema.

    Args:
        params:
            - page_key (str): page to rollback
            - target_version (int, optional): version number to rollback to.
              If not specified, rolls back to the most recent archived version.
        context: Must contain ``db``.

    Returns:
        dict with success status and the restored version info.
    """
    page_key = params.get("page_key", "").strip()
    target_version = params.get("target_version")

    if not page_key:
        return {"error": "page_key is required"}

    db = context.get("db")
    if db is None:
        return {"error": "No database session in context"}

    now = datetime.now(timezone.utc)

    # Find the target version to restore
    if target_version is not None:
        target = (
            db.query(PageVersionModel)
            .filter(
                PageVersionModel.page_key == page_key,
                PageVersionModel.version_number == target_version,
            )
            .first()
        )
    else:
        # Find the most recently archived version
        target = (
            db.query(PageVersionModel)
            .filter(
                PageVersionModel.page_key == page_key,
                PageVersionModel.status == "archived",
            )
            .order_by(PageVersionModel.version_number.desc())
            .first()
        )

    if target is None:
        return {"error": f"No version found to rollback to for '{page_key}'"}

    # Archive current published version(s)
    published = (
        db.query(PageVersionModel)
        .filter(
            PageVersionModel.page_key == page_key,
            PageVersionModel.status == "published",
        )
        .all()
    )
    for pub in published:
        pub.status = "archived"
        pub.updated_at = now

    # Re-publish the target version
    target.status = "published"
    target.updated_at = now

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("rollback_page_version failed: %s", exc)
        return {"error": str(exc)}

    return {
        "success": True,
        "page_key": page_key,
        "restored_version": target.version_number,
        "restored_version_id": target.id,
        "refresh_page": True,
    }


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="rollback_page_version",
    fn=rollback_page_version,
    description=(
        "Rollback a page schema to a previous version. "
        "If no target_version is specified, rolls back to the most recent archived version. "
        "Params: page_key (str), target_version (int, optional)."
    ),
    params_schema={
        "type": "object",
        "properties": {
            "page_key": {
                "type": "string",
                "description": "Page key to rollback (e.g. 'products')",
            },
            "target_version": {
                "type": "integer",
                "description": "Version number to restore (optional, defaults to most recent archived)",
            },
        },
        "required": ["page_key"],
    },
)
