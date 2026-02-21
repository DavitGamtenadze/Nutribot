from __future__ import annotations

from typing import Any

import requests

from app.config import Settings
from app.utils.retry import retry_requests


class OpenFDAClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.openfda_base_url
        self._api_key = settings.openfda_api_key

    @retry_requests
    def search_label_safety(self, ingredient_or_term: str, limit: int = 3) -> dict[str, Any]:
        term = ingredient_or_term.strip()
        if not term:
            return {"results": []}

        params = {
            "search": f'openfda.generic_name:"{term}"+openfda.brand_name:"{term}"',
            "limit": limit,
        }
        if self._api_key:
            params["api_key"] = self._api_key

        response = requests.get(self._base_url, params=params, timeout=20)
        if response.status_code == 404:
            return {"results": []}
        response.raise_for_status()

        data = response.json()
        normalized: list[dict[str, Any]] = []
        for item in data.get("results") or []:
            openfda = item.get("openfda") or {}
            normalized.append(
                {
                    "brand_name": (openfda.get("brand_name") or [None])[0],
                    "generic_name": (openfda.get("generic_name") or [None])[0],
                    "warnings": (item.get("warnings") or [])[:2],
                    "adverse_reactions": (item.get("adverse_reactions") or [])[:2],
                    "contraindications": (item.get("contraindications") or [])[:2],
                    "source": "openfda",
                }
            )

        return {"results": normalized}
