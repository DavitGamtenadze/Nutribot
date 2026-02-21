from __future__ import annotations

from typing import Any

import requests

from app.config import Settings
from app.utils.retry import retry_requests


class OpenFoodFactsClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.openfoodfacts_base_url
        self._headers = {"User-Agent": settings.openfoodfacts_user_agent}

    @retry_requests
    def search_products(
        self,
        query: str,
        page_size: int = 6,
        category_tag: str = "en:dietary-supplements",
    ) -> list[dict[str, Any]]:
        params = {
            "search_terms": query,
            "categories_tags": category_tag,
            "page": 1,
            "page_size": page_size,
            "fields": ",".join(
                [
                    "code",
                    "product_name",
                    "brands",
                    "categories_tags",
                    "ingredients_text",
                    "nutriments",
                    "quantity",
                    "image_front_url",
                    "url",
                ]
            ),
        }
        response = requests.get(self._base_url, params=params, headers=self._headers, timeout=20)
        response.raise_for_status()
        payload = response.json()
        products = payload.get("products") or []

        normalized: list[dict[str, Any]] = []
        for p in products:
            name = str(p.get("product_name") or "").strip()
            if not name:
                continue

            nutriments = p.get("nutriments") or {}
            normalized.append(
                {
                    "id": str(p.get("code") or name),
                    "name": name,
                    "brands": p.get("brands"),
                    "quantity": p.get("quantity"),
                    "ingredients_text": p.get("ingredients_text"),
                    "categories": p.get("categories_tags") or [],
                    "energy_kcal_100g": nutriments.get("energy-kcal_100g") or nutriments.get("energy_kcal_100g"),
                    "proteins_100g": nutriments.get("proteins_100g"),
                    "carbs_100g": nutriments.get("carbohydrates_100g"),
                    "fat_100g": nutriments.get("fat_100g"),
                    "url": p.get("url"),
                    "image_url": p.get("image_front_url"),
                    "source": "openfoodfacts",
                }
            )

        return normalized
