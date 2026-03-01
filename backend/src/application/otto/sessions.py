"""Otto Session Manager — in-memory session store for interactive messages.

Each SSE stream gets a unique session_id.  When the orchestrator emits an
interactive message, it *pauses* the stream by clearing an asyncio.Event.
The frontend sends the user's choice via POST /otto/respond/{session_id},
which sets the event and lets the orchestrator resume.

# TODO: migrar para Redis em produção — sessões em memória não sobrevivem
# a restart nem escalam horizontalmente
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)

# TTL for stale sessions (seconds)
SESSION_TTL = 300  # 5 minutes

# How often the cleanup task runs (seconds)
_CLEANUP_INTERVAL = 60


@dataclass
class OttoSession:
    """Represents a single Otto streaming session."""

    id: str
    event: asyncio.Event = field(default_factory=asyncio.Event)
    response: str | None = None
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def touch(self) -> None:
        """Update last_active timestamp."""
        self.last_active = time.time()

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.last_active) > SESSION_TTL


# ── In-memory store ──────────────────────────────────────────────────

_sessions: dict[str, OttoSession] = {}
_lock = Lock()
_cleanup_task: asyncio.Task | None = None


def create_session() -> OttoSession:
    """Create a new session and register it."""
    session = OttoSession(id=str(uuid.uuid4()))
    with _lock:
        _sessions[session.id] = session
    _ensure_cleanup_running()
    logger.debug("Otto session created: %s", session.id)
    return session


def get_session(session_id: str) -> OttoSession | None:
    """Retrieve a session by ID, or None if not found / expired."""
    with _lock:
        session = _sessions.get(session_id)
    if session is None:
        return None
    if session.is_expired:
        remove_session(session_id)
        return None
    session.touch()
    return session


def remove_session(session_id: str) -> None:
    """Remove a session (e.g. when the stream ends)."""
    with _lock:
        removed = _sessions.pop(session_id, None)
    if removed:
        logger.debug("Otto session removed: %s", session_id)


# ── Automatic cleanup ───────────────────────────────────────────────


async def _cleanup_loop() -> None:
    """Periodically purge expired sessions to avoid memory leak."""
    while True:
        await asyncio.sleep(_CLEANUP_INTERVAL)
        now = time.time()
        expired_ids: list[str] = []
        with _lock:
            for sid, session in _sessions.items():
                if (now - session.last_active) > SESSION_TTL:
                    expired_ids.append(sid)
            for sid in expired_ids:
                _sessions.pop(sid, None)
        if expired_ids:
            logger.info(
                "Otto session cleanup: removed %d expired session(s)", len(expired_ids)
            )


def _ensure_cleanup_running() -> None:
    """Start the cleanup background task if not already running."""
    global _cleanup_task
    if _cleanup_task is not None and not _cleanup_task.done():
        return
    try:
        loop = asyncio.get_running_loop()
        _cleanup_task = loop.create_task(_cleanup_loop())
    except RuntimeError:
        # No running loop — will be started on next call inside an async context
        pass
