"""Shared retry decorators for HTTP and LLM calls."""

from __future__ import annotations

import requests
from openai import APIError, APITimeoutError, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

retry_requests = retry(
    wait=wait_exponential(multiplier=1, min=1, max=8),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=True,
)

retry_llm = retry(
    wait=wait_exponential(multiplier=1, min=1, max=15),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError)),
    reraise=True,
)
