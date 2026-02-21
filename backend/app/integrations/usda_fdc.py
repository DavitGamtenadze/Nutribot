from __future__ import annotations

from typing import Any

import requests

from app.config import Settings
from app.utils.retry import retry_requests


class USDAFoodDataCentralClient:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.usda_api_key
        self._endpoint = settings.usda_base_url

    @property
    def enabled(self) -> bool:
        return bool(self._api_key)

    @retry_requests
    def search_food(self, query: str, page_size: int = 5) -> dict[str, Any]:
        if not self._api_key:
            return {
                "warning": "USDA_API_KEY is not set. Configure it to enable authoritative nutrient lookup.",
                "foods": [],
            }

        payload = {
            "query": query,
            "pageSize": page_size,
        }
        response = requests.post(
            self._endpoint,
            params={"api_key": self._api_key},
            json=payload,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        foods: list[dict[str, Any]] = []
        for item in data.get("foods") or []:
            nutrients = item.get("foodNutrients") or []
            macro_map = {n.get("nutrientName", "").lower(): n.get("value") for n in nutrients}
            foods.append(
                {
                    "description": item.get("description"),
                    "brand": item.get("brandOwner"),
                    "calories": macro_map.get("energy"),
                    "protein": macro_map.get("protein"),
                    "carbs": macro_map.get("carbohydrate, by difference"),
                    "fat": macro_map.get("total lipid (fat)"),
                    "source": "usda_fdc",
                }
            )

        return {"foods": foods}
