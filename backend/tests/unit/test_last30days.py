from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import respx
from fastapi.testclient import TestClient
from httpx import Response

from app.main import app

# Mock both search endpoints since query= calls /search, no-query calls /search_by_date
ALGOLIA_BASE = "https://hn.algolia.com/api/v1"

NOW = datetime.now(UTC)


def _make_hit(
    object_id: str,
    title: str = "Test",
    url: str | None = None,
    points: int = 10,
    num_comments: int = 5,
    author: str = "user",
    story_text: str | None = None,
) -> dict:
    created_at = (NOW - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return {
        "objectID": object_id,
        "created_at": created_at,
        "created_at_i": int((NOW - timedelta(days=1)).timestamp()),
        "title": title,
        "url": url,
        "author": author,
        "points": points,
        "num_comments": num_comments,
        "story_text": story_text,
    }


def _algolia_response(hits: list[dict]) -> dict:
    return {
        "hits": hits,
        "nbHits": len(hits),
        "page": 0,
        "nbPages": 1,
        "hitsPerPage": 20,
        "processingTimeMS": 5,
        "query": "",
    }


client = TestClient(app)


def _mock_algolia(hits: list[dict]) -> None:
    """Mock both Algolia search endpoints."""
    body = _algolia_response(hits)
    respx.get(url__startswith=f"{ALGOLIA_BASE}/search").mock(return_value=Response(200, json=body))


class TestLast30DaysAPI:
    @respx.mock
    def test_working_status_with_results(self) -> None:
        hit1 = _make_hit("1", title="Story A", url="https://example.com/a", points=100, num_comments=50)
        hit2 = _make_hit("2", title="Story B", url="https://example.com/b", points=50, num_comments=20)
        _mock_algolia([hit1, hit2])

        resp = client.post("/api/v1/last30days", json={"query": "test", "limit": 50})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "working"
        assert len(data["items"]) == 2
        assert data["items"][0]["title"] == "Story A"  # ranked by points desc
        assert "fetched_at" in data

    @respx.mock
    def test_no_results_status(self) -> None:
        _mock_algolia([])

        resp = client.post("/api/v1/last30days", json={"query": "nonexistent"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "no-results"
        assert data["items"] == []

    @respx.mock
    def test_error_status_on_api_failure(self) -> None:
        respx.get(url__startswith=f"{ALGOLIA_BASE}/search").mock(
            return_value=Response(500, text="Internal Server Error")
        )

        resp = client.post("/api/v1/last30days", json={"query": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
        assert "message" in data

    @respx.mock
    def test_skipped_when_disabled(self) -> None:
        with patch("app.last30days.service.settings") as mock_settings:
            mock_settings.last30days_enabled = False
            mock_settings.last30days_base_url = "https://hn.algolia.com/api/v1"
            resp = client.post("/api/v1/last30days", json={"query": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "skipped"
        assert data["items"] == []

    @respx.mock
    def test_partial_status_with_duplicates(self) -> None:
        hit1 = _make_hit("1", title="Story A", url="https://example.com/a", points=100)
        hit_dup = _make_hit("1", title="Story A dup", url="https://example.com/a", points=50)
        hit2 = _make_hit("2", title="Story B", points=30)
        _mock_algolia([hit1, hit_dup, hit2])

        resp = client.post("/api/v1/last30days", json={"query": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "partial"
        assert len(data["items"]) == 2

    @respx.mock
    def test_dedup_by_url_prefers_higher_points(self) -> None:
        hit_low = _make_hit("10", title="Low Points", url="https://example.com/same", points=10)
        hit_high = _make_hit("11", title="High Points", url="https://example.com/same", points=200)
        _mock_algolia([hit_low, hit_high])

        resp = client.post("/api/v1/last30days", json={"query": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "High Points"

    @respx.mock
    def test_ranking_order(self) -> None:
        hit_a = _make_hit("1", title="A", points=50, num_comments=10)
        hit_b = _make_hit("2", title="B", points=100, num_comments=5)
        hit_c = _make_hit("3", title="C", points=100, num_comments=20)
        _mock_algolia([hit_a, hit_b, hit_c])

        resp = client.post("/api/v1/last30days", json={"query": "test"})
        data = resp.json()
        titles = [item["title"] for item in data["items"]]
        assert titles == ["C", "B", "A"]  # points desc, then num_comments desc

    @respx.mock
    def test_citation_url_fallback(self) -> None:
        hit = _make_hit("42", title="No URL", url=None, points=10)
        _mock_algolia([hit])

        resp = client.post("/api/v1/last30days", json={"query": "test"})
        data = resp.json()
        assert data["items"][0]["citation_url"] == "https://news.ycombinator.com/item?id=42"

    @respx.mock
    def test_citation_url_external(self) -> None:
        hit = _make_hit("43", title="Has URL", url="https://example.com/article", points=10)
        _mock_algolia([hit])

        resp = client.post("/api/v1/last30days", json={"query": "test"})
        data = resp.json()
        assert data["items"][0]["citation_url"] == "https://example.com/article"

    @respx.mock
    def test_limit_parameter(self) -> None:
        hits = [_make_hit(str(i), title=f"Story {i}", points=100 - i) for i in range(10)]
        _mock_algolia(hits)

        resp = client.post("/api/v1/last30days", json={"query": "test", "limit": 3})
        data = resp.json()
        assert len(data["items"]) == 3
        assert data["status"] == "working"  # limit truncation is not partial

    @respx.mock
    def test_response_normalization(self) -> None:
        hit = _make_hit(
            "99",
            title="Norm Test",
            url="https://x.com",
            points=42,
            num_comments=7,
            author="alice",
            story_text="hello",
        )
        _mock_algolia([hit])

        resp = client.post("/api/v1/last30days", json={"query": "test"})
        item = resp.json()["items"][0]
        assert item["object_id"] == "99"
        assert item["title"] == "Norm Test"
        assert item["url"] == "https://x.com"
        assert item["author"] == "alice"
        assert item["points"] == 42
        assert item["num_comments"] == 7
        assert item["story_text"] == "hello"

    @respx.mock
    def test_limit_truncation_returns_working_status(self) -> None:
        """Valid, deduplicated results truncated only by the requested limit
        should still return status 'working', not 'partial'."""
        hits = [_make_hit(str(i), title=f"Story {i}", points=100 - i) for i in range(10)]
        _mock_algolia(hits)

        resp = client.post("/api/v1/last30days", json={"query": "test", "limit": 5})
        data = resp.json()
        assert data["status"] == "working"
        assert len(data["items"]) == 5
        # Verify items are correctly ranked (top 5 by points)
        for item in data["items"]:
            assert item["points"] >= 96  # top 5 have points 100..96

    @respx.mock
    def test_partial_with_invalid_items(self) -> None:
        """Items dropped as invalid (missing objectID) should cause 'partial' status."""
        valid_hit = _make_hit("1", title="Valid", points=50)
        invalid_hit = {"created_at": "2025-01-01T00:00:00.000Z", "created_at_i": 1735689600, "title": "No ID"}
        # invalid_hit has no objectID -> will be filtered out by _is_valid
        _mock_algolia([valid_hit, invalid_hit])

        resp = client.post("/api/v1/last30days", json={"query": "test"})
        data = resp.json()
        assert data["status"] == "partial"
        assert len(data["items"]) == 1
