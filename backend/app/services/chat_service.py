from __future__ import annotations

from app.models.schemas import ChatRequest, ChatResponse, GenerationConfig
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.user_repository import UserRepository
from app.services.coach_engine import CoachEngine
from app.services.llm_client import LLMClient


class ChatService:
    def __init__(
        self,
        user_repo: UserRepository,
        conversation_repo: ConversationRepository,
        coach_engine: CoachEngine,
        llm_client: LLMClient,
    ) -> None:
        self._user_repo = user_repo
        self._conversation_repo = conversation_repo
        self._coach_engine = coach_engine
        self._llm_client = llm_client

    def handle_chat(self, req: ChatRequest) -> ChatResponse:
        self._user_repo.get_or_create_user(req.user_id, display_name=req.user_name)

        profile = self._user_repo.get_profile(req.user_id)
        if profile is None:
            profile = self._user_repo.ensure_profile(req.user_id, req.user_name)

        requested_goals = req.goals if req.goals else None
        requested_diet = req.dietary_preferences if req.dietary_preferences else None
        requested_allergies = req.allergies if req.allergies else None
        requested_medications = req.medications if req.medications else None
        requested_notes = req.notes if req.notes else None
        if any(
            (
                requested_goals is not None,
                requested_diet is not None,
                requested_allergies is not None,
                requested_medications is not None,
                requested_notes is not None,
                req.user_name,
            )
        ):
            profile = self._user_repo.upsert_profile(
                external_id=req.user_id,
                display_name=req.user_name,
                goals=requested_goals if requested_goals is not None else profile.goals,
                dietary_preferences=requested_diet if requested_diet is not None else profile.dietary_preferences,
                allergies=requested_allergies if requested_allergies is not None else profile.allergies,
                medications=requested_medications if requested_medications is not None else profile.medications,
                notes=requested_notes if requested_notes is not None else profile.notes,
            )

        conversation = self._conversation_repo.ensure_conversation(
            external_user_id=req.user_id,
            conversation_id=req.conversation_id,
            default_title=(req.message or "Meal analysis")[:80],
        )

        prior_messages = self._conversation_repo.list_messages(
            external_user_id=req.user_id,
            conversation_id=conversation.id,
            limit=16,
        )
        history_payload = [{"role": m.role, "content": m.content} for m in prior_messages]

        image_url = req.image_url or None
        if image_url and self._llm_client.enabled:
            classification = self._llm_client.classify_image(image_url)
            if classification == "rejected":
                raise ValueError(
                    "The uploaded image doesn't appear to be food-related. "
                    "Please share a photo of a meal or food item so NutriBot can help."
                )

        self._conversation_repo.add_message(
            external_user_id=req.user_id,
            conversation_id=conversation.id,
            role="user",
            content=req.message or "[image only message]",
            image_url=image_url,
            metadata_json={
                "goals": profile.goals,
                "dietary_preferences": profile.dietary_preferences,
                "allergies": profile.allergies,
                "medications": profile.medications,
            },
        )

        response, tool_events = self._coach_engine.build_plan(
            message=req.message,
            image_url=image_url,
            goals=profile.goals,
            dietary_preferences=profile.dietary_preferences,
            allergies=profile.allergies,
            medications=profile.medications,
            notes=profile.notes,
            generation=GenerationConfig(),
            conversation_history=history_payload,
            user_id=req.user_id,
            max_tool_rounds=4,
        )

        # Log tool events to the database
        for event in tool_events:
            self._conversation_repo.add_tool_event(
                conversation_id=conversation.id,
                tool_name=event["tool_name"],
                arguments_json=event.get("arguments"),
                result_preview=event.get("result_preview", "")[:500],
            )

        # Store the full response as assistant content so history is useful
        assistant_content = response.summary
        if response.priorities:
            priority_lines = [f"- {p.title}: {p.action}" for p in response.priorities]
            assistant_content += "\n\nPriorities:\n" + "\n".join(priority_lines)

        assistant_message = self._conversation_repo.add_message(
            external_user_id=req.user_id,
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_content,
            metadata_json=response.model_dump(),
        )

        if image_url or req.message:
            self._conversation_repo.add_meal_log(
                external_user_id=req.user_id,
                conversation_id=conversation.id,
                meal_text=req.message,
                image_url=image_url,
                analysis_json={
                    "summary": response.summary,
                    "priorities": [item.model_dump() for item in response.priorities],
                    "safety_watchouts": response.safety_watchouts,
                },
            )

        return ChatResponse(
            conversation_id=conversation.id,
            response_message_id=assistant_message.id,
            response=response,
        )
