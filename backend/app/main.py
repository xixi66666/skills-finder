from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    ApiError,
    api_error_handler,
    http_exception_handler,
    internal_error_handler,
)
from app.api.v1 import admin, health, last30days, repositories, stats
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
app.include_router(repositories.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(last30days.router, prefix="/api/v1")

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(Exception, internal_error_handler)