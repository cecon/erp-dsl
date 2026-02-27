"""Built-in image/blob transform functions for the DSL pipeline.

Handles the conversion between base64 image data and filesystem
blob storage. Saves images to the `uploads/` directory and returns
the relative path for database storage.
"""

from __future__ import annotations

import base64
import logging
import os
import uuid
from pathlib import Path
from typing import Any

from src.application.dsl_functions.registry import function_registry

logger = logging.getLogger(__name__)

# Upload directory — relative to the backend working directory
UPLOAD_DIR = Path("uploads")


def _ensure_upload_dir() -> None:
    """Create uploads directory if it doesn't exist."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def image_to_blob(value: Any) -> Any:
    """Convert a base64-encoded image to a file on disk.

    Accepts:
        "data:image/png;base64,iVBORw0KGgo..."
        or raw base64 string

    Returns:
        Relative file path, e.g. "uploads/abc123.png"
    """
    if not isinstance(value, str) or not value:
        return value

    _ensure_upload_dir()

    # Parse data URI if present
    if value.startswith("data:"):
        # data:image/png;base64,iVBORw0KGgo...
        header, _, b64_data = value.partition(",")
        ext = _extract_extension(header)
    else:
        b64_data = value
        ext = "png"  # default

    try:
        raw_bytes = base64.b64decode(b64_data)
    except Exception:
        logger.warning("Invalid base64 data, storing as-is")
        return value

    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = UPLOAD_DIR / filename

    filepath.write_bytes(raw_bytes)
    logger.info("Saved blob: %s (%d bytes)", filepath, len(raw_bytes))

    return str(filepath)


def blob_to_image(value: Any) -> Any:
    """Read a file path and return base64-encoded data URI.

    Accepts:
        "uploads/abc123.png"

    Returns:
        "data:image/png;base64,iVBORw0KGgo..."
    """
    if not isinstance(value, str) or not value:
        return value

    filepath = Path(value)
    if not filepath.exists():
        logger.warning("Blob file not found: %s", filepath)
        return value

    raw_bytes = filepath.read_bytes()
    b64 = base64.b64encode(raw_bytes).decode("utf-8")
    ext = filepath.suffix.lstrip(".")
    mime = _ext_to_mime(ext)

    return f"data:{mime};base64,{b64}"


def _extract_extension(header: str) -> str:
    """Extract file extension from data URI header."""
    # data:image/png;base64 → png
    try:
        mime_part = header.split(":")[1].split(";")[0]
        return mime_part.split("/")[1]
    except (IndexError, KeyError):
        return "png"


def _ext_to_mime(ext: str) -> str:
    """Map file extension to MIME type."""
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
    }
    return mime_map.get(ext.lower(), "application/octet-stream")


# ── Auto-register ────────────────────────────────────────────────

function_registry.register("image_to_blob", image_to_blob)
function_registry.register("blob_to_image", blob_to_image)
