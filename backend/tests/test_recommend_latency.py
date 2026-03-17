"""Lightweight latency check for hybrid recommendation endpoint."""

from __future__ import annotations

from dataclasses import dataclass
import time

from fastapi.testclient import TestClient

from backend.main import app


@dataclass(slots=True)
class _FakeHybridResult:
    normalized_ingredients: list[str]
    on_hand_recipes: list[dict]
    related_recipes: list[dict]
    used_fallback: bool
    fallback_reason: str | None


class _FastHybridRecommender:
    """Small deterministic recommender stub to measure endpoint overhead."""

    def recommend_recipes(self, user_ingredients, top_k):
        _ = top_k
        time.sleep(0.02)
        return _FakeHybridResult(
            normalized_ingredients=list(user_ingredients),
            on_hand_recipes=[
                {
                    "type": "generated",
                    "title": "Quick Egg Spinach Scramble",
                    "ingredients": ["egg", "spinach"],
                    "instructions": ["Cook eggs", "Fold in spinach"],
                    "missing_ingredients": [],
                    "score": 0.95,
                }
            ],
            related_recipes=[
                {
                    "id": 42,
                    "type": "database",
                    "title": "Spinach Omelette",
                    "ingredients": ["egg", "spinach", "olive oil"],
                    "instructions": "Cook eggs with spinach.",
                    "missing_ingredients": ["olive oil"],
                    "match_score": 0.67,
                    "score": 0.62,
                }
            ],
            used_fallback=False,
            fallback_reason=None,
        )


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(0.95 * (len(ordered) - 1))
    return ordered[idx]


def test_recommend_endpoint_p95_under_2_seconds() -> None:
    with TestClient(app) as client:
        app.state.hybrid_recommender = _FastHybridRecommender()

        payload = {"ingredients": ["eggs", "spinach"], "filters": [], "top_k": 5}

        latencies: list[float] = []
        for _ in range(30):
            start = time.perf_counter()
            response = client.post("/api/recommend", json=payload)
            elapsed = time.perf_counter() - start
            assert response.status_code == 200
            latencies.append(elapsed)

    assert _p95(latencies) <= 2.0
