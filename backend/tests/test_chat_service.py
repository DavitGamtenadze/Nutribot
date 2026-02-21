from __future__ import annotations

from app.models.schemas import ChatRequest
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.user_repository import UserRepository
from app.services.chat_service import ChatService


class StubCoachEngine:
    def build_plan(
        self,
        message,
        image_url,
        goals,
        dietary_preferences,
        allergies,
        medications,
        notes,
        generation,
        conversation_history,
        user_id=None,
        max_tool_rounds=4,
    ):
        from app.models.schemas import CoachResponse, PlanPriority

        return CoachResponse(
            summary="Stub summary",
            priorities=[
                PlanPriority(
                    title="Protein anchor",
                    action="Add protein with lunch.",
                    why_it_matters="Supports recovery.",
                    timeframe="today",
                )
            ],
            meal_focus=["Add vegetables at dinner."],
            supplement_options=["Creatine can be considered."],
            safety_watchouts=["Not medical advice."],
            follow_up_questions=["What does your lunch usually look like?"],
            disclaimer="General guidance only.",
        ), []


class StubLLMClient:
    enabled = False


def test_chat_service_persists_messages_and_returns_conversation_id(db_session_factory) -> None:
    user_repo = UserRepository(db_session_factory)
    conv_repo = ConversationRepository(db_session_factory)
    service = ChatService(
        user_repo=user_repo,
        conversation_repo=conv_repo,
        coach_engine=StubCoachEngine(),
        llm_client=StubLLMClient(),
    )

    req = ChatRequest(
        user_id="u1",
        user_name="Davit",
        conversation_id=None,
        message="Is my lunch good for muscle gain?",
        goals=["muscle_gain"],
        dietary_preferences=["high_protein"],
        allergies=["soy"],
        medications=[],
    )

    result = service.handle_chat(req)

    assert result.conversation_id > 0
    assert result.response.summary == "Stub summary"
    assert result.response_message_id > 0

    messages = conv_repo.list_messages("u1", result.conversation_id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
