"""Validation-focused API tests for recommendation endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app


class _EchoHybridRecommender:
    def __init__(self) -> None:
        self.last_filters: list[str] | None = None

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
                "used_fallback": True,
                "fallback_reason": "missing_api_key",
            },
        )()


def test_recommend_rejects_unknown_filters() -> None:
    with TestClient(app) as client:
        app.state.hybrid_recommender = _EchoHybridRecommender()
        response = client.post(
            "/api/recommend",
            json={"ingredients": ["egg"], "filters": ["unknown_filter"], "top_k": 3},
        )

    assert response.status_code == 400
    assert "Unknown filter(s)" in response.json()["detail"]


def test_recommend_rejects_whitespace_only_ingredients() -> None:
    with TestClient(app) as client:
        app.state.hybrid_recommender = _EchoHybridRecommender()
        response = client.post(
            "/api/recommend",
            json={"ingredients": ["   ", ""], "filters": [], "top_k": 3},
        )

    assert response.status_code == 400
    assert "must not be empty" in response.json()["detail"]


def test_recommend_normalizes_and_deduplicates_filters() -> None:
    with TestClient(app) as client:
        fake = _EchoHybridRecommender()
        app.state.hybrid_recommender = fake

        response = client.post(
            "/api/recommend",
            json={"ingredients": ["egg"], "filters": ["Vegan", "vegan", "  VEGAN  "], "top_k": 3},
        )

    assert response.status_code == 200
    assert fake.last_filters == ["vegan"]


def test_recommend_response_includes_fallback_metadata() -> None:
    with TestClient(app) as client:
        app.state.hybrid_recommender = _EchoHybridRecommender()

        response = client.post(
            "/api/recommend",
            json={"ingredients": ["egg"], "filters": [], "top_k": 3},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["used_fallback"] is True
    assert body["fallback_reason"] == "missing_api_key"
    assert "normalized_ingredients" in body
    assert "on_hand_recipes" in body
    assert "related_recipes" in body
