from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from starlette.testclient import TestClient

from app.main import app
from app.models.schemas import (
    CoachResponse,
)


@pytest.fixture()
def client(db_session_factory):
    """TestClient with all module-level singletons patched to use in-memory SQLite."""
    from app.repositories.conversation_repository import ConversationRepository
    from app.repositories.user_repository import UserRepository
    from app.services.chat_service import ChatService
    from app.services.memory_store import MemoryStore

    user_repo = UserRepository(db_session_factory)
    conv_repo = ConversationRepository(db_session_factory)
    mem_store = MemoryStore(db_session_factory)

    mock_llm = MagicMock()
    mock_llm.enabled = False

    _coach_response = CoachResponse(
        summary="Test summary",
        priorities=[],
        meal_focus=[],
        supplement_options=[],
        safety_watchouts=[],
        follow_up_questions=[],
        disclaimer="Test disclaimer",
    )

    mock_engine = MagicMock()
    # build_plan must return a (CoachResponse, list) tuple — matches real CoachEngine.build_plan
    mock_engine.build_plan.return_value = (_coach_response, [])

    chat_svc = ChatService(
        user_repo=user_repo,
        conversation_repo=conv_repo,
        coach_engine=mock_engine,
        llm_client=mock_llm,
    )

    # Patch the rate limiter's acquire so it never blocks
    mock_limiter = MagicMock()
    mock_limiter.acquire.return_value = None

    with (
        patch.multiple(
            "app.api.routes",
            user_repo=user_repo,
            conversation_repo=conv_repo,
            memory_store=mem_store,
            chat_service=chat_svc,
            llm_client=mock_llm,
            _limiter=mock_limiter,
        ),
        TestClient(app, raise_server_exceptions=True) as c,
    ):
        yield c


class TestHealth:
    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestUserProfile:
    def test_get_profile_creates_user(self, client):
        resp = client.get("/api/users/test-user/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "test-user"
        assert isinstance(data["goals"], list)

    def test_put_profile_updates_goals(self, client):
        resp = client.put(
            "/api/users/test-user/profile",
            json={"goals": ["lose weight", "build muscle"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["goals"] == ["lose weight", "build muscle"]

    def test_get_after_put_returns_updated(self, client):
        client.put("/api/users/test-user/profile", json={"goals": ["hydration"]})
        resp = client.get("/api/users/test-user/profile")
        assert resp.status_code == 200
        assert resp.json()["goals"] == ["hydration"]


class TestChat:
    def test_chat_creates_conversation(self, client):
        resp = client.post(
            "/api/chat",
            json={"user_id": "u1", "message": "Is pasta good for training?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["conversation_id"] > 0
        assert data["response"]["summary"] == "Test summary"

    def test_chat_empty_request_rejected(self, client):
        # No message and no image_url — should be 422
        resp = client.post("/api/chat", json={"user_id": "u1"})
        assert resp.status_code == 422


class TestConversations:
    def test_list_conversations_empty(self, client):
        resp = client.get("/api/conversations/new-user")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "new-user"
        assert data["conversations"] == []

    def test_list_conversations_after_chat(self, client):
        client.post("/api/chat", json={"user_id": "chat-user", "message": "hello"})
        resp = client.get("/api/conversations/chat-user")
        assert resp.status_code == 200
        assert len(resp.json()["conversations"]) == 1

    def test_list_messages(self, client):
        chat_resp = client.post("/api/chat", json={"user_id": "msg-user", "message": "hello"})
        conv_id = chat_resp.json()["conversation_id"]
        resp = client.get(f"/api/conversations/msg-user/{conv_id}/messages")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["messages"]) == 2  # user + assistant
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"


class TestMemory:
    def test_get_memory_returns_structure(self, client):
        resp = client.get("/api/memory/mem-user")
        assert resp.status_code == 200
        data = resp.json()
        assert "user_id" in data
        assert "snapshot" in data
        assert "recent" in data
