from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _research_result() -> dict:
    return {
        "status": "working",
        "query": "OpenAI",
        "items": [
            {
                "candidate_id": "reddit-1",
                "title": "What developers are saying",
                "source": "reddit",
                "url": "https://www.reddit.com/r/example/1",
                "published_at": "2026-08-20T00:00:00Z",
                "summary": "A grounded community summary.",
                "engagement": {"score": 210, "comments": 42},
                "relevance_score": 0.95,
                "cluster": 0,
            }
        ],
        "clusters": [
            {
                "title": "Developer reactions",
                "summary": "Developers discussed the latest changes.",
                "sources": ["reddit", "hackernews"],
                "engagement_total": 320,
            }
        ],
        "sources": ["github", "hackernews", "reddit"],
        "source_status": {
            "github": "ok",
            "hackernews": "ok",
            "reddit": "ok",
        },
        "fetched_at": "2026-08-21T00:00:00Z",
        "message": None,
    }


def test_research_endpoint_returns_multisource_result() -> None:
    runner = AsyncMock(return_value=_research_result())
    with patch("app.api.v1.last30days.fetch_last30days", runner):
        response = client.post("/api/v1/last30days", json={"query": "  OpenAI  ", "limit": 10})

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "OpenAI"
    assert payload["sources"] == ["github", "hackernews", "reddit"]
    assert payload["clusters"][0]["title"] == "Developer reactions"
    assert payload["items"][0]["source"] == "reddit"
    runner.assert_awaited_once_with(query="OpenAI", limit=10)


def test_research_endpoint_rejects_blank_topic() -> None:
    response = client.post("/api/v1/last30days", json={"query": "   "})

    assert response.status_code == 422


def test_status_endpoint_reports_available_sources() -> None:
    runner = AsyncMock(
        return_value={
            "status": "working",
            "sources": ["reddit", "hackernews", "polymarket", "github", "grounding"],
            "message": None,
        }
    )
    with patch("app.api.v1.last30days.diagnose_last30days", runner):
        response = client.get("/api/v1/last30days/status")

    assert response.status_code == 200
    assert response.json()["sources"] == [
        "reddit",
        "hackernews",
        "polymarket",
        "github",
        "grounding",
    ]


def test_research_endpoint_preserves_unconfigured_status() -> None:
    result = _research_result()
    result.update(
        {
            "status": "unconfigured",
            "items": [],
            "clusters": [],
            "sources": [],
            "source_status": {},
            "message": "runtime missing",
        }
    )
    with patch("app.api.v1.last30days.fetch_last30days", AsyncMock(return_value=result)):
        response = client.post("/api/v1/last30days", json={"query": "OpenAI"})

    assert response.status_code == 200
    assert response.json()["status"] == "unconfigured"
    assert response.json()["message"] == "runtime missing"
