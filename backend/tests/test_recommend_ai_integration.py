"""Integration-style test for hybrid recommendation endpoint contract."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app


class _FakeHybridRecommender:
    def recommend_recipes(self, user_ingredients, top_k, filters=None):
        _ = user_ingredients
        _ = top_k
        _ = filters
        return type(
            "_FakeHybridResult",
            (),
            {
                "normalized_ingredients": ["egg", "spinach", "feta cheese"],
                "on_hand_recipes": [
                    {
                        "type": "generated",
                        "title": "Spinach Egg Skillet",
                        "ingredients": ["egg", "spinach", "feta cheese"],
                        "instructions": ["Whisk eggs", "Saute spinach", "Cook together"],
                        "missing_ingredients": [],
                        "score": 0.93,
                    }
                ],
                "related_recipes": [
                    {
                        "id": 1,
                        "type": "database",
                        "title": "Spinach Feta Omelette",
                        "ingredients": ["egg", "spinach", "feta cheese", "olive oil"],
                        "instructions": "Beat eggs and cook with spinach.",
                        "missing_ingredients": ["olive oil"],
                        "match_score": 0.75,
                        "score": 0.7,
                    }
                ],
                "used_fallback": False,
                "fallback_reason": None,
            },
        )()


class _CaptureHybridRecommender:
    def __init__(self) -> None:
        self.last_filters = None

    def recommend_recipes(self, user_ingredients, top_k, filters=None):
        _ = user_ingredients
        _ = top_k
        self.last_filters = filters
        return type(
            "_FakeHybridResult",
            (),
            {
                "normalized_ingredients": ["egg"],
                "on_hand_recipes": [],
                "related_recipes": [],
                "used_fallback": False,
                "fallback_reason": None,
            },
        )()


def test_recommend_ai_endpoint_contract() -> None:
    with TestClient(app) as client:
        app.state.hybrid_recommender = _FakeHybridRecommender()
        app.state.ai_config_error = None

        payload = {
            "ingredients": ["egg", "spinach", "feta cheese"],
            "filters": [],
            "top_k": 3,
        }
        response = client.post("/api/recommend/ai", json=payload)

    assert response.status_code == 200

    body = response.json()
    assert "on_hand_recipes" in body
    assert "related_recipes" in body
    assert "normalized_ingredients" in body
    assert isinstance(body["on_hand_recipes"], list)
    assert isinstance(body["related_recipes"], list)

    if body["on_hand_recipes"]:
        first = body["on_hand_recipes"][0]
        assert "type" in first
        assert "title" in first
        assert "ingredients" in first
        assert "score" in first


def test_recommend_endpoint_propagates_filters_to_hybrid_engine() -> None:
    with TestClient(app) as client:
        fake = _CaptureHybridRecommender()
        app.state.hybrid_recommender = fake
        app.state.ai_config_error = None

        payload = {
            "ingredients": ["egg", "spinach"],
            "filters": ["vegan"],
            "top_k": 3,
        }
        response = client.post("/api/recommend", json=payload)

    assert response.status_code == 200
    assert fake.last_filters == ["vegan"]
