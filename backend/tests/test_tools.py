from __future__ import annotations

from app.services.memory_store import MemoryStore
from app.tools.registry import ToolRegistry


class StubOFF:
    def search_products(self, query: str, page_size: int = 6):
        return [{"id": "p1", "name": f"{query} product", "source": "openfoodfacts"}]


class StubUSDA:
    def __init__(self) -> None:
        self.enabled = True

    def search_food(self, query: str, page_size: int = 5):
        if "unknown" in query:
            return {"foods": []}
        return {
            "foods": [
                {
                    "description": f"{query} item",
                    "calories": 100.0,
                    "protein": 10.0,
                    "carbs": 20.0,
                    "fat": 5.0,
                }
            ]
        }


class StubFDA:
    def search_label_safety(self, ingredient_or_term: str, limit: int = 3):
        return {"results": [{"generic_name": ingredient_or_term, "warnings": ["sample warning"]}]}


class StubPubMed:
    def search_evidence(self, query: str, max_results: int = 5):
        return {"articles": [{"pmid": "1", "title": f"Evidence on {query}"}]}


def test_tool_registry_lookup_products(db_session_factory) -> None:
    memory = MemoryStore(db_session_factory)
    tools = ToolRegistry(
        memory_store=memory,
        openfoodfacts=StubOFF(),
        usda=StubUSDA(),
        openfda=StubFDA(),
        pubmed=StubPubMed(),
    )

    result = tools.execute("lookup_products", {"query": "creatine"}, user_id="u1")
    assert result["products"]
    assert result["source"] == "openfoodfacts_live"


def test_tool_registry_estimate_meal(db_session_factory) -> None:
    memory = MemoryStore(db_session_factory)
    tools = ToolRegistry(
        memory_store=memory,
        openfoodfacts=StubOFF(),
        usda=StubUSDA(),
        openfda=StubFDA(),
        pubmed=StubPubMed(),
    )

    result = tools.execute(
        "estimate_meal_nutrition",
        {"food_items": ["chicken", "rice", "unknown item"]},
        user_id="u1",
    )

    totals = result["estimated_totals"]
    assert totals["calories"] == 200.0
    assert "unknown item" in result["unmatched_items"]


def test_tool_registry_memory_roundtrip(db_session_factory) -> None:
    memory = MemoryStore(db_session_factory)
    tools = ToolRegistry(
        memory_store=memory,
        openfoodfacts=StubOFF(),
        usda=StubUSDA(),
        openfda=StubFDA(),
        pubmed=StubPubMed(),
    )

    tools.execute(
        "store_user_memory",
        {"user_id": "u1", "key": "goal", "value": "muscle_gain", "reason": "stated explicitly"},
        user_id="u1",
    )
    result = tools.execute("get_user_memory", {"user_id": "u1"}, user_id="u1")

    assert result["snapshot"]["goal"] == "muscle_gain"
    assert result["recent"]
