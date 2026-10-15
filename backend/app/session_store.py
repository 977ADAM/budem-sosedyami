"""Anonymous browser-session ownership backed by PostgreSQL."""

from __future__ import annotations

import hashlib
import secrets
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

SESSION_TTL_DAYS = 30


class SessionStore:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def resolve(self, token: str | None) -> tuple[UUID, str, bool]:
        """Refresh a valid token or create a new opaque browser session."""
        if token:
            session_id = await self.lookup(token)
            if session_id:
                return session_id, token, False

        new_token = secrets.token_urlsafe(32)
        session_id = uuid4()
        async with self._engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    INSERT INTO anonymous_chat_sessions (id, token_hash, expires_at)
                    VALUES (
                        :session_id,
                        :token_hash,
                        now() + make_interval(days => :ttl_days)
                    )
                    """
                ),
                {
                    "session_id": session_id,
                    "token_hash": _hash_token(new_token),
                    "ttl_days": SESSION_TTL_DAYS,
                },
            )
        return session_id, new_token, True

    async def resolve_existing(self, token: str | None) -> UUID | None:
        """Refresh a valid session without creating one when the cookie is absent."""
        if not token:
            return None
        return await self.lookup(token)

    async def lookup(self, token: str) -> UUID | None:
        token_hash = _hash_token(token)
        async with self._engine.begin() as connection:
            result = await connection.execute(
                text(
                    """
                    UPDATE anonymous_chat_sessions
                    SET last_seen_at = now(),
                        expires_at = now() + make_interval(days => :ttl_days)
                    WHERE token_hash = :token_hash
                      AND expires_at > now()
                      AND cleanup_pending = false
                    RETURNING id
                    """
                ),
                {"ttl_days": SESSION_TTL_DAYS, "token_hash": token_hash},
            )
            row = result.mappings().first()
        return row["id"] if row else None

    async def revoke(self, session_id: UUID) -> None:
        async with self._engine.begin() as connection:
            await connection.execute(
                text("DELETE FROM anonymous_chat_sessions WHERE id = :session_id"),
                {"session_id": session_id},
            )

    async def mark_for_cleanup(self, session_id: UUID) -> None:
        async with self._engine.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE anonymous_chat_sessions "
                    "SET cleanup_pending = true WHERE id = :session_id"
                ),
                {"session_id": session_id},
            )

    async def claim_expired(self) -> list[UUID]:
        async with self._engine.begin() as connection:
            result = await connection.execute(
                text(
                    """
                    UPDATE anonymous_chat_sessions
                    SET cleanup_pending = true
                    WHERE expires_at <= now() OR cleanup_pending = true
                    RETURNING id
                    """
                )
            )
            rows = result.mappings().all()
        return [row["id"] for row in rows]

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
