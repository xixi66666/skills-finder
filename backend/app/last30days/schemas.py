from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

StatusType = Literal[
    "working",
    "no-results",
    "partial",
    "error",
    "skipped",
    "unconfigured",
]


class Last30DaysRequest(BaseModel):
    query: str | None = None
    limit: int = Field(default=50, ge=1, le=100)


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
    status: StatusType
    items: list[Last30DaysItem]
    fetched_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    message: str | None = None
