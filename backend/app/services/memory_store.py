from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.db.models import MemoryEntry, User


class MemoryStore:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def add_memory(self, external_user_id: str, key: str, value: str, reason: str | None = None) -> None:
        with self._session_factory() as session:
            user = self._ensure_user(session, external_user_id)
            session.add(
                MemoryEntry(
                    user_id=user.id,
                    memory_key=key,
                    memory_value=value,
                    reason=reason,
                    source="agent",
                )
            )
            session.commit()

    def get_snapshot(self, external_user_id: str) -> dict[str, str]:
        with self._session_factory() as session:
            user = session.scalar(select(User).where(User.external_id == external_user_id))
            if not user:
                return {}

            rows = session.scalars(
                select(MemoryEntry).where(MemoryEntry.user_id == user.id).order_by(MemoryEntry.id.asc())
            ).all()

        latest: dict[str, str] = {}
        for row in rows:
            latest[row.memory_key] = row.memory_value
        return latest

    def recent_memories(self, external_user_id: str, limit: int = 8) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            user = session.scalar(select(User).where(User.external_id == external_user_id))
            if not user:
                return []

            rows = session.scalars(
                select(MemoryEntry).where(MemoryEntry.user_id == user.id).order_by(MemoryEntry.id.desc()).limit(limit)
            ).all()

        return [
            {
                "key": row.memory_key,
                "value": row.memory_value,
                "reason": row.reason,
                "source": row.source,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]

    @staticmethod
    def _ensure_user(session, external_user_id: str) -> User:
        user = session.scalar(select(User).where(User.external_id == external_user_id))
        if user:
            return user

        user = User(external_id=external_user_id)
        session.add(user)
        session.flush()
        return user
