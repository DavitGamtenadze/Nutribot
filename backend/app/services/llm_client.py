from __future__ import annotations

import base64
import logging
import mimetypes
from pathlib import Path
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletion

from app.config import Settings
from app.models.schemas import CoachResponse, GenerationConfig
from app.services.rate_limiter import SlidingWindowRateLimiter
from app.utils.retry import retry_llm

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._rate_limiter = SlidingWindowRateLimiter(settings.requests_per_minute)
        self._enabled = bool(settings.openai_api_key)
        self._client = OpenAI(api_key=settings.openai_api_key) if self._enabled else None

    @property
    def enabled(self) -> bool:
        return self._enabled

    @retry_llm
    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        generation: GenerationConfig,
        tools: list[dict[str, Any]] | None = None,
    ) -> ChatCompletion:
        """Raw chat completion with optional tool definitions. Used in the tool-calling loop."""
        self._require_enabled()
        self._rate_limiter.acquire()

        kwargs: dict[str, Any] = {
            "model": self._settings.openai_model,
            "messages": messages,
            "temperature": generation.temperature,
            "top_p": generation.top_p,
            "max_tokens": generation.max_output_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        return self._client.chat.completions.create(**kwargs)

    @retry_llm
    def generate_coach_response(
        self,
        messages: list[dict[str, Any]],
        generation: GenerationConfig,
    ) -> CoachResponse:
        """Structured output call using OpenAI's beta parse() for automatic schema handling."""
        self._require_enabled()
        self._rate_limiter.acquire()

        response = self._client.beta.chat.completions.parse(
            model=self._settings.openai_model,
            messages=messages,
            temperature=generation.temperature,
            top_p=generation.top_p,
            max_tokens=generation.max_output_tokens,
            response_format=CoachResponse,
        )

        parsed = response.choices[0].message.parsed
        if parsed is None:
            refusal = response.choices[0].message.refusal
            raise ValueError(f"Model refused to respond: {refusal}")
        return parsed

    @retry_llm
    def generate_text(
        self,
        prompt: str,
        generation: GenerationConfig,
        system_message: str = "You are a concise helpful assistant.",
    ) -> str:
        self._require_enabled()
        self._rate_limiter.acquire()

        response = self._client.chat.completions.create(
            model=self._settings.openai_model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            temperature=generation.temperature,
            top_p=generation.top_p,
            max_tokens=generation.max_output_tokens,
        )

        return response.choices[0].message.content or ""

    def to_data_uri(self, image_path: str) -> str:
        if image_path.startswith(("data:", "http://", "https://")):
            return image_path
        upload_root = Path(self._settings.upload_dir).resolve()
        candidate = (upload_root / image_path.lstrip("/")).resolve()
        if not str(candidate).startswith(str(upload_root) + "/"):
            raise ValueError("Image path is outside the allowed uploads directory")
        if not candidate.exists():
            raise FileNotFoundError("Image not found")
        mime, _ = mimetypes.guess_type(str(candidate))
        mime = mime or "image/jpeg"
        raw = candidate.read_bytes()
        b64 = base64.b64encode(raw).decode()
        return f"data:{mime};base64,{b64}"

    def classify_image(self, image_url: str) -> str:
        self._require_enabled()
        self._rate_limiter.acquire()
        data_uri = self.to_data_uri(image_url)
        response = self._client.chat.completions.create(
            model=self._settings.openai_vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Is this image food or nutrition related? "
                                "Reply with exactly one word: 'food' or 'rejected'."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            temperature=0.0,
            max_tokens=10,
        )
        result = (response.choices[0].message.content or "").strip().lower()
        return "food" if "food" in result else "rejected"

    def _require_enabled(self) -> None:
        if not self._enabled or self._client is None:
            raise RuntimeError("AI service is not configured.")
