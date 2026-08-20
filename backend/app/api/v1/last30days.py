from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.last30days.service import fetch_last30days

router = APIRouter()


class Last30DaysRequest(BaseModel):
    query: str | None = Field(default=None, description="Search query")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of items")


class Last30DaysItem(BaseModel):
    object_id: str
    created_at: str
    title: str | None = None
    url: str | None = None
    author: str | None = None
    points: int | None = None
    num_comments: int | None = None
    story_text: str | None = None
    citation_url: str


class Last30DaysResponse(BaseModel):
    status: str
    items: list[Last30DaysItem] = []
    fetched_at: str
    message: str | None = None


@router.post("/last30days", response_model=Last30DaysResponse)
async def last30days_endpoint(request: Last30DaysRequest) -> Last30DaysResponse:
    try:
        result = await fetch_last30days(query=request.query or "", limit=request.limit)
        return Last30DaysResponse(
            status=result["status"],
            items=[Last30DaysItem(**item) for item in result["items"]],
            fetched_at=result["fetched_at"],
            message=result.get("message"),
        )
    except Exception as exc:  # noqa: BLE001
        return Last30DaysResponse(
            status="error",
            fetched_at=datetime.now(UTC).isoformat(),
            message=str(exc),
        )
