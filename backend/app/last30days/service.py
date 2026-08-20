from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.config import settings

HN_ITEM_URL = "https://news.ycombinator.com/item?id="


def _is_valid(item: dict[str, Any]) -> bool:
    return bool(item.get("objectID") and item.get("created_at_i"))


def _normalize(item: dict[str, Any]) -> dict[str, Any]:
    object_id = str(item["objectID"])
    external_url = item.get("url") or ""
    citation_url = external_url if external_url else f"{HN_ITEM_URL}{object_id}"
    return {
        "object_id": object_id,
        "created_at": item.get("created_at", ""),
        "title": item.get("title") or "",
        "url": external_url,
        "author": item.get("author") or "",
        "points": int(item.get("points") or 0),
        "num_comments": int(item.get("num_comments") or 0),
        "story_text": item.get("story_text") or "",
        "citation_url": citation_url,
    }


def _dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_oid: dict[str, dict[str, Any]] = {}
    by_url: dict[str, dict[str, Any]] = {}
    for item in items:
        oid = item["object_id"]
        url = item["url"].strip().rstrip("/").lower() if item["url"] else ""
        if oid in by_oid:
            existing = by_oid[oid]
            if item["points"] > existing["points"]:
                by_oid[oid] = item
            continue
        if url and url in by_url:
            existing = by_url[url]
            if item["points"] > existing["points"]:
                old_oid = existing["object_id"]
                by_url[url] = item
                by_oid[oid] = item
                by_oid.pop(old_oid, None)
            continue
        by_oid[oid] = item
        if url:
            by_url[url] = item
    return list(by_oid.values())


def _rank(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda x: (x["points"], x["num_comments"], x["created_at"]),
        reverse=True,
    )


async def fetch_last30days(
    query: str = "",
    limit: int = 50,
) -> dict[str, Any]:
    if not settings.last30days_enabled:
        return {"status": "skipped", "items": [], "fetched_at": _now_iso(), "message": "Module disabled"}

    base_url = settings.last30days_base_url.rstrip("/")
    thirty_days_ago = int((datetime.now(UTC) - timedelta(days=30)).timestamp())
    tags = "(story,comment,poll,show_hn,ask_hn)"
    params: dict[str, Any] = {
        "numericFilters": f"created_at_i>{thirty_days_ago}",
        "tags": tags,
        "hitsPerPage": min(limit * 2, 200),
    }
    if query:
        endpoint = f"{base_url}/search"
        params["query"] = query
    else:
        endpoint = f"{base_url}/search_by_date"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(endpoint, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "items": [],
            "fetched_at": _now_iso(),
            "message": f"Fetch failed: {exc}",
        }

    raw_hits = data.get("hits", [])
    total_raw = len(raw_hits)
    valid = [_normalize(h) for h in raw_hits if _is_valid(h)]
    total_valid = len(valid)
    deduped = _dedupe(valid)
    total_deduped = len(deduped)
    ranked = _rank(deduped)[:limit]

    if not ranked:
        status = "no-results"
    elif total_deduped < total_valid or total_valid < total_raw:
        # Some items were dropped as invalid or duplicates
        status = "partial"
    else:
        status = "working"

    return {"status": status, "items": ranked, "fetched_at": _now_iso()}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
