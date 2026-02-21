from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.schemas import ChatRequest, UserProfileUpsertRequest


class TestChatRequestImageUrl:
    def test_valid_upload_path_accepted(self):
        # Valid: /uploads/<32 hex chars>.<ext>
        req = ChatRequest(user_id="u1", message="hi", image_url="/uploads/" + "a" * 32 + ".jpg")
        assert req.image_url == "/uploads/" + "a" * 32 + ".jpg"

    def test_none_image_url_accepted(self):
        req = ChatRequest(user_id="u1", message="hi")
        assert req.image_url is None

    def test_arbitrary_url_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(user_id="u1", message="hi", image_url="https://evil.com/image.jpg")

    def test_path_traversal_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(user_id="u1", message="hi", image_url="/uploads/../etc/passwd")

    def test_wrong_length_hex_rejected(self):
        # Only 31 hex chars — too short
        with pytest.raises(ValidationError):
            ChatRequest(user_id="u1", message="hi", image_url="/uploads/" + "a" * 31 + ".jpg")


class TestChatRequestListLimits:
    def test_goals_max_20_items_accepted(self):
        goals = [f"goal_{i}" for i in range(20)]
        req = ChatRequest(user_id="u1", message="hi", goals=goals)
        assert len(req.goals) == 20

    def test_goals_21_items_rejected(self):
        goals = [f"goal_{i}" for i in range(21)]
        with pytest.raises(ValidationError):
            ChatRequest(user_id="u1", message="hi", goals=goals)

    def test_goal_item_100_chars_accepted(self):
        req = ChatRequest(user_id="u1", message="hi", goals=["a" * 100])
        assert req.goals == ["a" * 100]

    def test_goal_item_101_chars_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(user_id="u1", message="hi", goals=["a" * 101])


class TestChatRequestContentRequired:
    def test_message_only_accepted(self):
        req = ChatRequest(user_id="u1", message="hello")
        assert req.message == "hello"

    def test_image_url_only_accepted(self):
        req = ChatRequest(user_id="u1", image_url="/uploads/" + "b" * 32 + ".png")
        assert req.image_url is not None

    def test_neither_message_nor_image_rejected(self):
        with pytest.raises(ValidationError, match="At least one of message or image_url is required"):
            ChatRequest(user_id="u1")


class TestUserProfileUpsertRequest:
    def test_valid_profile_accepted(self):
        req = UserProfileUpsertRequest(goals=["lose weight"], dietary_preferences=["vegan"])
        assert req.goals == ["lose weight"]

    def test_none_fields_accepted(self):
        req = UserProfileUpsertRequest()
        assert req.goals is None

    def test_list_limit_enforced(self):
        with pytest.raises(ValidationError):
            UserProfileUpsertRequest(allergies=[f"allergy_{i}" for i in range(21)])
