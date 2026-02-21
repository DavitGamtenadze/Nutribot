from __future__ import annotations

from typing import Any

from app.integrations.openfda import OpenFDAClient
from app.integrations.openfoodfacts import OpenFoodFactsClient
from app.integrations.pubmed import PubMedClient
from app.integrations.usda_fdc import USDAFoodDataCentralClient
from app.services.memory_store import MemoryStore


class ToolRegistry:
    def __init__(
        self,
        memory_store: MemoryStore,
        openfoodfacts: OpenFoodFactsClient,
        usda: USDAFoodDataCentralClient,
        openfda: OpenFDAClient,
        pubmed: PubMedClient,
    ) -> None:
        self._memory = memory_store
        self._openfoodfacts = openfoodfacts
        self._usda = usda
        self._openfda = openfda
        self._pubmed = pubmed

    @property
    def schemas(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "lookup_products",
                    "description": "Search real supplement products from Open Food Facts in real time.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "default": 6},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "lookup_nutrients",
                    "description": "Search USDA FoodData Central for authoritative nutrition values.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "default": 5},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "estimate_meal_nutrition",
                    "description": "Estimate total meal macros by querying USDA for each food item.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "food_items": {
                                "type": "array",
                                "items": {"type": "string"},
                            }
                        },
                        "required": ["food_items"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "lookup_safety_signals",
                    "description": "Fetch relevant safety/label signals from openFDA.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "term": {"type": "string"},
                            "limit": {"type": "integer", "default": 3},
                        },
                        "required": ["term"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "lookup_evidence",
                    "description": "Search PubMed evidence summaries for a nutrition/supplement claim.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "max_results": {"type": "integer", "default": 5},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_user_memory",
                    "description": "Retrieve remembered user profile/preferences for personalization.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string"},
                        },
                        "required": ["user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "store_user_memory",
                    "description": "Persist durable user preferences for future conversations.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string"},
                            "key": {"type": "string"},
                            "value": {"type": "string"},
                            "reason": {"type": "string"},
                        },
                        "required": ["user_id", "key", "value"],
                    },
                },
            },
        ]

    def execute(self, name: str, args: dict[str, Any], user_id: str) -> dict[str, Any]:
        try:
            if name == "lookup_products":
                query = str(args.get("query") or "").strip()
                limit = int(args.get("limit", 6))
                return {
                    "query": query,
                    "products": self._openfoodfacts.search_products(query=query, page_size=max(1, min(limit, 12))),
                    "source": "openfoodfacts_live",
                }

            if name == "lookup_nutrients":
                query = str(args.get("query") or "").strip()
                limit = int(args.get("limit", 5))
                result = self._usda.search_food(query=query, page_size=max(1, min(limit, 10)))
                result["source"] = "usda_live"
                return result

            if name == "estimate_meal_nutrition":
                food_items = [str(item).strip() for item in args.get("food_items", []) if str(item).strip()]
                return self._estimate_meal_nutrition(food_items)

            if name == "lookup_safety_signals":
                term = str(args.get("term") or "").strip()
                limit = int(args.get("limit", 3))
                result = self._openfda.search_label_safety(term, limit=max(1, min(limit, 10)))
                result["source"] = "openfda_live"
                return result

            if name == "lookup_evidence":
                query = str(args.get("query") or "").strip()
                max_results = int(args.get("max_results", 5))
                result = self._pubmed.search_evidence(query=query, max_results=max(1, min(max_results, 10)))
                result["source"] = "pubmed_live"
                return result

            if name == "get_user_memory":
                target_user = str(args.get("user_id") or user_id)
                return {
                    "snapshot": self._memory.get_snapshot(target_user),
                    "recent": self._memory.recent_memories(target_user, limit=10),
                }

            if name == "store_user_memory":
                target_user = str(args.get("user_id") or user_id)
                key = str(args.get("key") or "").strip()
                value = str(args.get("value") or "").strip()
                reason = str(args.get("reason") or "").strip() or None
                if not key or not value:
                    return {"status": "skipped", "reason": "missing key/value"}
                self._memory.add_memory(target_user, key, value, reason)
                return {"status": "stored", "key": key, "value": value}

            return {"error": f"Unknown tool '{name}'"}
        except Exception as exc:  # noqa: BLE001
            return {"error": f"Tool '{name}' failed: {exc}"}

    def _estimate_meal_nutrition(self, food_items: list[str]) -> dict[str, Any]:
        totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
        per_item: list[dict[str, Any]] = []
        unmatched: list[str] = []

        for item in food_items:
            lookup = self._usda.search_food(item, page_size=1)
            foods = lookup.get("foods") or []
            if not foods:
                unmatched.append(item)
                continue

            top = foods[0]
            calories = float(top.get("calories") or 0.0)
            protein = float(top.get("protein") or 0.0)
            carbs = float(top.get("carbs") or 0.0)
            fat = float(top.get("fat") or 0.0)

            totals["calories"] += calories
            totals["protein"] += protein
            totals["carbs"] += carbs
            totals["fat"] += fat

            per_item.append(
                {
                    "query": item,
                    "match": top.get("description"),
                    "calories": round(calories, 2),
                    "protein": round(protein, 2),
                    "carbs": round(carbs, 2),
                    "fat": round(fat, 2),
                }
            )

        return {
            "items": per_item,
            "unmatched_items": unmatched,
            "estimated_totals": {k: round(v, 2) for k, v in totals.items()},
            "assumption": "Values reflect top USDA search match per item and may vary by serving size.",
            "source": "usda_live",
        }
