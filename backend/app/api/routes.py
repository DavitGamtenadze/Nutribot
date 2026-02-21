from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.config import get_settings
from app.db.session import get_session_factory
from app.integrations.openfda import OpenFDAClient
from app.integrations.openfoodfacts import OpenFoodFactsClient
from app.integrations.pubmed import PubMedClient
from app.integrations.usda_fdc import USDAFoodDataCentralClient
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationListResponse,
    ConversationMessagesResponse,
    ConversationSummary,
    MessageRecord,
    UserProfileResponse,
    UserProfileUpsertRequest,
)
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.user_repository import UserRepository
from app.services.chat_service import ChatService
from app.services.coach_engine import CoachEngine
from app.services.image_service import ImageService
from app.services.llm_client import LLMClient
from app.services.memory_store import MemoryStore
from app.services.rate_limiter import SlidingWindowRateLimiter
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

router = APIRouter()
_settings = get_settings()
session_factory = get_session_factory()

user_repo = UserRepository(session_factory)
conversation_repo = ConversationRepository(session_factory)
memory_store = MemoryStore(session_factory)
llm_client = LLMClient(_settings)

openfoodfacts_client = OpenFoodFactsClient(_settings)
usda_client = USDAFoodDataCentralClient(_settings)
openfda_client = OpenFDAClient(_settings)
pubmed_client = PubMedClient(_settings)

tool_registry = ToolRegistry(
    memory_store=memory_store,
    openfoodfacts=openfoodfacts_client,
    usda=usda_client,
    openfda=openfda_client,
    pubmed=pubmed_client,
)

coach_engine = CoachEngine(llm_client, tool_registry=tool_registry)
image_service = ImageService()
chat_service = ChatService(
    user_repo=user_repo, conversation_repo=conversation_repo, coach_engine=coach_engine, llm_client=llm_client
)

# Shared rate limiter applied to expensive endpoints
_limiter = SlidingWindowRateLimiter(requests_per_minute=_settings.requests_per_minute)


def _rate_limit() -> None:
    """FastAPI dependency: blocks until within the per-process rate limit."""
    _limiter.acquire()


@router.post("/upload-image", dependencies=[Depends(_rate_limit)])
def upload_image(file: UploadFile) -> dict[str, str]:
    try:
        url = image_service.save_upload(file)
        return {"image_url": url}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(_rate_limit)])
def chat(req: ChatRequest) -> ChatResponse:
    try:
        return chat_service.handle_chat(req)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error handling chat request for user %s", req.user_id)
        raise HTTPException(status_code=500, detail="An internal error occurred") from exc


@router.get("/users/{user_id}/profile", response_model=UserProfileResponse)
def get_profile(user_id: str) -> UserProfileResponse:
    profile = user_repo.ensure_profile(user_id)
    user = user_repo.get_user(user_id)
    return UserProfileResponse(
        user_id=user_id,
        user_name=user.display_name if user else None,
        goals=profile.goals,
        dietary_preferences=profile.dietary_preferences,
        allergies=profile.allergies,
        medications=profile.medications,
        notes=profile.notes,
    )


@router.put("/users/{user_id}/profile", response_model=UserProfileResponse)
def upsert_profile(user_id: str, req: UserProfileUpsertRequest) -> UserProfileResponse:
    current = user_repo.ensure_profile(user_id, req.user_name)
    profile = user_repo.upsert_profile(
        external_id=user_id,
        display_name=req.user_name,
        goals=req.goals if req.goals is not None else current.goals,
        dietary_preferences=(
            req.dietary_preferences if req.dietary_preferences is not None else current.dietary_preferences
        ),
        allergies=req.allergies if req.allergies is not None else current.allergies,
        medications=req.medications if req.medications is not None else current.medications,
        notes=req.notes if req.notes is not None else current.notes,
    )
    user = user_repo.get_user(user_id)

    return UserProfileResponse(
        user_id=user_id,
        user_name=user.display_name if user else None,
        goals=profile.goals,
        dietary_preferences=profile.dietary_preferences,
        allergies=profile.allergies,
        medications=profile.medications,
        notes=profile.notes,
    )


@router.get("/conversations/{user_id}", response_model=ConversationListResponse)
def list_conversations(user_id: str) -> ConversationListResponse:
    items = conversation_repo.list_conversations(user_id)
    return ConversationListResponse(
        user_id=user_id,
        conversations=[
            ConversationSummary(
                conversation_id=item.id,
                title=item.title,
                updated_at=item.updated_at.isoformat(),
            )
            for item in items
        ],
    )


@router.get("/conversations/{user_id}/{conversation_id}/messages", response_model=ConversationMessagesResponse)
def list_messages(user_id: str, conversation_id: int) -> ConversationMessagesResponse:
    items = conversation_repo.list_messages(user_id, conversation_id, limit=120)
    return ConversationMessagesResponse(
        user_id=user_id,
        conversation_id=conversation_id,
        messages=[
            MessageRecord(
                message_id=item.id,
                role=item.role,
                content=item.content,
                image_url=item.image_url,
                created_at=item.created_at.isoformat(),
            )
            for item in items
        ],
    )


@router.get("/memory/{user_id}")
def get_memory(user_id: str) -> dict[str, object]:
    return {
        "user_id": user_id,
        "snapshot": memory_store.get_snapshot(user_id),
        "recent": memory_store.recent_memories(user_id),
    }
