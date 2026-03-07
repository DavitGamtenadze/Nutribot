from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import sessionmaker

from sqlalchemy import or_

from app.db.models import Conversation, MealLog, Message, ToolEvent, User
from app.repositories.user_repository import UserRepository


class ConversationRepository:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def ensure_conversation(
        self,
        external_user_id: str,
        conversation_id: int | None,
        default_title: str | None = None,
    ) -> Conversation:
        with self._session_factory() as session:
            user = self._require_user(session, external_user_id)

            if conversation_id is not None:
                conversation = session.scalar(
                    select(Conversation).where(
                        and_(Conversation.id == conversation_id, Conversation.user_id == user.id)
                    )
                )
                if conversation:
                    return conversation

            conversation = Conversation(user_id=user.id, title=default_title or "New conversation")
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            return conversation

    def list_conversations(self, external_user_id: str, limit: int = 20) -> list[Conversation]:
        with self._session_factory() as session:
            user = self._require_user(session, external_user_id)
            return session.scalars(
                select(Conversation)
                .where(Conversation.user_id == user.id)
                .order_by(Conversation.updated_at.desc())
                .limit(limit)
            ).all()

    def delete_conversation(self, external_user_id: str, conversation_id: int) -> bool:
        with self._session_factory() as session:
            user = self._require_user(session, external_user_id)
            conversation = session.scalar(
                select(Conversation).where(
                    and_(Conversation.id == conversation_id, Conversation.user_id == user.id)
                )
            )
            if not conversation:
                return False
            session.delete(conversation)
            session.commit()
            return True

    def update_title(self, conversation_id: int, title: str) -> None:
        with self._session_factory() as session:
            conversation = session.scalar(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            if conversation:
                conversation.title = title
                session.commit()

    def search_conversations(self, external_user_id: str, query: str, limit: int = 20) -> list[Conversation]:
        with self._session_factory() as session:
            user = self._require_user(session, external_user_id)
            pattern = f"%{query}%"
            # Find conversations matching title or containing messages with the query
            matching_msg_conv_ids = (
                select(Message.conversation_id)
                .where(Message.user_id == user.id, Message.content.ilike(pattern))
                .distinct()
                .scalar_subquery()
            )
            return session.scalars(
                select(Conversation)
                .where(
                    Conversation.user_id == user.id,
                    or_(
                        Conversation.title.ilike(pattern),
                        Conversation.id.in_(matching_msg_conv_ids),
                    ),
                )
                .order_by(Conversation.updated_at.desc())
                .limit(limit)
            ).all()

    def list_meal_logs(self, external_user_id: str, limit: int = 100) -> list[MealLog]:
        with self._session_factory() as session:
            user = self._require_user(session, external_user_id)
            return session.scalars(
                select(MealLog)
                .where(MealLog.user_id == user.id)
                .order_by(MealLog.created_at.desc())
                .limit(limit)
            ).all()

    def get_weekly_summary(self, external_user_id: str) -> dict:
        """Aggregate meal logs for the past 7 days."""
        from datetime import timedelta

        with self._session_factory() as session:
            user = self._require_user(session, external_user_id)
            seven_days_ago = datetime.now(UTC) - timedelta(days=7)

            logs = session.scalars(
                select(MealLog)
                .where(MealLog.user_id == user.id, MealLog.created_at >= seven_days_ago)
                .order_by(MealLog.created_at.desc())
            ).all()

            total_meals = len(logs)
            active_days = len({str(log.created_at.date()) for log in logs})

            # Extract recurring priority titles
            priority_counts: dict[str, int] = {}
            for log in logs:
                analysis = log.analysis_json or {}
                for p in analysis.get("priorities", []):
                    title = p.get("title", "")
                    if title:
                        priority_counts[title] = priority_counts.get(title, 0) + 1

            recurring = [t for t, c in sorted(priority_counts.items(), key=lambda x: -x[1]) if c >= 2][:5]

            return {
                "total_meals": total_meals,
                "active_days": active_days,
                "consistency_pct": round((active_days / 7) * 100),
                "recurring_themes": recurring,
            }

    def add_message(
        self,
        external_user_id: str,
        conversation_id: int,
        role: str,
        content: str,
        image_url: str | None = None,
        metadata_json: dict | None = None,
    ) -> Message:
        with self._session_factory() as session:
            user = self._require_user(session, external_user_id)
            conversation = session.scalar(
                select(Conversation).where(and_(Conversation.id == conversation_id, Conversation.user_id == user.id))
            )
            if not conversation:
                raise ValueError("Conversation not found for user")

            message = Message(
                conversation_id=conversation.id,
                user_id=user.id,
                role=role,
                content=content,
                image_url=image_url,
                metadata_json=metadata_json,
            )
            session.add(message)
            conversation.updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(message)
            return message

    def list_messages(self, external_user_id: str, conversation_id: int, limit: int = 80) -> list[Message]:
        with self._session_factory() as session:
            user = self._require_user(session, external_user_id)
            conversation = session.scalar(
                select(Conversation).where(and_(Conversation.id == conversation_id, Conversation.user_id == user.id))
            )
            if not conversation:
                return []

            return session.scalars(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.id.desc())
                .limit(limit)
            ).all()[::-1]

    def add_tool_event(
        self,
        conversation_id: int,
        tool_name: str,
        arguments_json: dict | None,
        result_preview: str,
    ) -> None:
        with self._session_factory() as session:
            session.add(
                ToolEvent(
                    conversation_id=conversation_id,
                    tool_name=tool_name,
                    arguments_json=arguments_json,
                    result_preview=result_preview,
                )
            )
            session.commit()

    def add_meal_log(
        self,
        external_user_id: str,
        conversation_id: int | None,
        meal_text: str | None,
        image_url: str | None,
        analysis_json: dict | None,
    ) -> None:
        with self._session_factory() as session:
            user = self._require_user(session, external_user_id)
            session.add(
                MealLog(
                    user_id=user.id,
                    conversation_id=conversation_id,
                    meal_text=meal_text,
                    image_url=image_url,
                    analysis_json=analysis_json,
                )
            )
            session.commit()

    @staticmethod
    def _require_user(session, external_user_id: str) -> User:
        return UserRepository.get_or_create_user_in_session(session, external_user_id)
