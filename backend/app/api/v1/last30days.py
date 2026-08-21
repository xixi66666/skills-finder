from __future__ import annotations

from fastapi import APIRouter

from app.last30days.schemas import (
    Last30DaysRequest,
    Last30DaysResponse,
    Last30DaysStatusResponse,
)
from app.last30days.service import diagnose_last30days, fetch_last30days

router = APIRouter()


@router.get("/last30days/status", response_model=Last30DaysStatusResponse)
async def last30days_status_endpoint() -> Last30DaysStatusResponse:
    return Last30DaysStatusResponse(**await diagnose_last30days())


@router.post("/last30days", response_model=Last30DaysResponse)
async def last30days_endpoint(request: Last30DaysRequest) -> Last30DaysResponse:
    result = await fetch_last30days(query=request.query, limit=request.limit)
    return Last30DaysResponse(**result)
