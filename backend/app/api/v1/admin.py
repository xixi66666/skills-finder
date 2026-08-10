from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.dependencies import require_admin_key
from app.core.scheduler import acquire_collection_lock, run_collection

router = APIRouter(prefix="/admin", tags=["admin"])

COLLECTION_ALREADY_RUNNING = "COLLECTION_ALREADY_RUNNING"


@router.post("/collections", status_code=status.HTTP_202_ACCEPTED)
async def trigger_collection(
    background_tasks: BackgroundTasks,
    _: None = Depends(require_admin_key),
) -> dict[str, str]:
    lease = await acquire_collection_lock()
    if lease is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": COLLECTION_ALREADY_RUNNING,
                "message": "A collection run is already in progress",
            },
        )
    background_tasks.add_task(run_collection, lease)
    return {"status": "accepted"}
