from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import admin, health
from app.core.config import settings
from app.core.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    scheduler = start_scheduler() if settings.scheduler_enabled else None
    yield
    if scheduler is not None:
        scheduler.shutdown()


app = FastAPI(title="Skill Finder API", lifespan=lifespan)

app.include_router(health.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
