from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator, model_validator

# Only accept paths that the upload endpoint produces: /uploads/<uuid-hex>.<ext>
_UPLOAD_PATH_RE = re.compile(r"^/uploads/[a-f0-9]{32}\.\w{2,5}$")

_MAX_LIST_ITEMS = 20
_MAX_ITEM_LEN = 100


def _validate_string_list(v: list[str]) -> list[str]:
    if len(v) > _MAX_LIST_ITEMS:
        raise ValueError(f"Maximum {_MAX_LIST_ITEMS} items allowed")
    for item in v:
        if len(item) > _MAX_ITEM_LEN:
            raise ValueError(f"Each item must be {_MAX_ITEM_LEN} characters or fewer")
    return v


class GenerationConfig(BaseModel):
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, gt=0.0, le=1.0)
    max_output_tokens: int = Field(default=1200, ge=100, le=4000)


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    user_name: str | None = Field(default=None, max_length=128)
    conversation_id: int | None = Field(default=None, ge=1)
    message: str | None = Field(default=None, max_length=4000)
    image_url: str | None = Field(default=None)
    goals: list[str] = Field(default_factory=list)
    dietary_preferences: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not _UPLOAD_PATH_RE.match(v):
            raise ValueError("image_url must be a valid /uploads/ path produced by the upload endpoint")
        return v

    @field_validator("goals", "dietary_preferences", "allergies", "medications")
    @classmethod
    def validate_list_fields(cls, v: list[str]) -> list[str]:
        return _validate_string_list(v)

    @model_validator(mode="after")
    def validate_content(self) -> ChatRequest:
        if not self.message and not self.image_url:
            raise ValueError("At least one of message or image_url is required")
        return self


class PlanPriority(BaseModel):
    title: str
    action: str
    why_it_matters: str
    timeframe: str


class CoachResponse(BaseModel):
    summary: str
    priorities: list[PlanPriority]
    meal_focus: list[str]
    supplement_options: list[str]
    safety_watchouts: list[str]
    follow_up_questions: list[str]
    disclaimer: str


class ChatResponse(BaseModel):
    conversation_id: int
    response_message_id: int
    response: CoachResponse


class UserProfileUpsertRequest(BaseModel):
    user_name: str | None = Field(default=None, max_length=128)
    goals: list[str] | None = None
    dietary_preferences: list[str] | None = None
    allergies: list[str] | None = None
    medications: list[str] | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("goals", "dietary_preferences", "allergies", "medications")
    @classmethod
    def validate_list_fields(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        return _validate_string_list(v)


class UserProfileResponse(BaseModel):
    user_id: str
    user_name: str | None
    goals: list[str]
    dietary_preferences: list[str]
    allergies: list[str]
    medications: list[str]
    notes: str | None


class ConversationSummary(BaseModel):
    conversation_id: int
    title: str | None
    updated_at: str


class ConversationListResponse(BaseModel):
    user_id: str
    conversations: list[ConversationSummary]


class MessageRecord(BaseModel):
    message_id: int
    role: str
    content: str
    image_url: str | None
    created_at: str


class ConversationMessagesResponse(BaseModel):
    user_id: str
    conversation_id: int
    messages: list[MessageRecord]
