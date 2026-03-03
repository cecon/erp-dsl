"""Skill: publish_page_version — publish a draft version, archiving the old one.

Used by Otto after the user confirms a schema change.

Contract: async def publish_page_version(params: dict, context: dict) -> dict
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.application.agent import skill_registry
from src.infrastructure.persistence.sqlalchemy.models import PageVersionModel

logger = logging.getLogger(__name__)


async def publish_page_version(params: dict, context: dict) -> dict:
    """Publish a draft page version, archiving the old published one.

    Args:
        params:
            - version_id (str): the draft version to publish
        context: Must contain ``db``.

    Returns:
        dict with success status.
    """
    version_id = params.get("version_id", "").strip()
    if not version_id:
        return {"error": "version_id is required"}

    db = context.get("db")
    if db is None:
        return {"error": "No database session in context"}

    # Find the draft version
    draft = db.query(PageVersionModel).filter_by(id=version_id).first()
    if draft is None:
        return {"error": f"Version '{version_id}' not found"}

    if draft.status != "draft":
        return {"error": f"Version is not a draft (status: {draft.status})"}

    # Archive current published version(s) for this page
    now = datetime.now(timezone.utc)
    published = (
        db.query(PageVersionModel)
        .filter(
            PageVersionModel.page_key == draft.page_key,
            PageVersionModel.status == "published",
        )
        .all()
    )
    for pub in published:
        pub.status = "archived"
        pub.updated_at = now

    # Publish the draft
    draft.status = "published"
    draft.updated_at = now

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("publish_page_version failed: %s", exc)
        return {"error": str(exc)}

    return {
        "success": True,
        "version_id": draft.id,
        "version_number": draft.version_number,
        "page_key": draft.page_key,
        "archived_count": len(published),
        "refresh_page": True,
    }


# ── Auto-register ───────────────────────────────────────────────────
skill_registry.register(
    name="publish_page_version",
    fn=publish_page_version,
    description=(
        "Publish a draft page version, making it the active schema. "
        "The previous published version is automatically archived. "
        "ALWAYS ask the user for confirmation before publishing. "
        "Params: version_id (str — the draft to publish)."
    ),
    params_schema={
        "type": "object",
        "properties": {
            "version_id": {
                "type": "string",
                "description": "ID of the draft version to publish",
            },
        },
        "required": ["version_id"],
    },
)
