from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import User, UserProfile


class UserRepository:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    @staticmethod
    def get_or_create_user_in_session(session: Session, external_id: str, display_name: str | None = None) -> User:
        """Get or create user in the given session; does not commit. Caller must commit if needed."""
        user = session.scalar(select(User).where(User.external_id == external_id))
        if user:
            if display_name and user.display_name != display_name:
                user.display_name = display_name
            return user
        user = User(external_id=external_id, display_name=display_name)
        session.add(user)
        session.flush()
        return user

    def get_or_create_user(self, external_id: str, display_name: str | None = None) -> User:
        with self._session_factory() as session:
            user = self.get_or_create_user_in_session(session, external_id, display_name)
            session.commit()
            session.refresh(user)
            return user

    def get_user(self, external_id: str) -> User | None:
        with self._session_factory() as session:
            return session.scalar(select(User).where(User.external_id == external_id))

    def get_profile(self, external_id: str) -> UserProfile | None:
        with self._session_factory() as session:
            user = session.scalar(select(User).where(User.external_id == external_id))
            if not user:
                return None
            return session.scalar(select(UserProfile).where(UserProfile.user_id == user.id))

    def upsert_profile(
        self,
        external_id: str,
        display_name: str | None = None,
        goals: list[str] | None = None,
        dietary_preferences: list[str] | None = None,
        allergies: list[str] | None = None,
        medications: list[str] | None = None,
        notes: str | None = None,
    ) -> UserProfile:
        with self._session_factory() as session:
            user = self.get_or_create_user_in_session(session, external_id, display_name)

            profile = session.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
            if not profile:
                profile = UserProfile(
                    user_id=user.id,
                    goals=goals or [],
                    dietary_preferences=dietary_preferences or [],
                    allergies=allergies or [],
                    medications=medications or [],
                    notes=notes,
                )
                session.add(profile)
            else:
                if goals is not None:
                    profile.goals = goals
                if dietary_preferences is not None:
                    profile.dietary_preferences = dietary_preferences
                if allergies is not None:
                    profile.allergies = allergies
                if medications is not None:
                    profile.medications = medications
                if notes is not None:
                    profile.notes = notes

            session.commit()
            session.refresh(profile)
            return profile

    def ensure_profile(self, external_id: str, display_name: str | None = None) -> UserProfile:
        with self._session_factory() as session:
            user = self.get_or_create_user_in_session(session, external_id, display_name)

            profile = session.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
            if profile:
                return profile

            profile = UserProfile(
                user_id=user.id,
                goals=[],
                dietary_preferences=[],
                allergies=[],
                medications=[],
                notes=None,
            )
            session.add(profile)
            session.commit()
            session.refresh(profile)
            return profile
