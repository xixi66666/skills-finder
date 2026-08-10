from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CollectionRun, Repository, StarSnapshot


class StatsService:
    def __init__(self, business_timezone: str = "Asia/Shanghai") -> None:
        self._timezone = ZoneInfo(business_timezone)

    async def get_stats(self, session: AsyncSession) -> dict:
        total = await session.scalar(
            select(func.count(Repository.id)).where(Repository.available.is_(True))
        )
        today = datetime.now(self._timezone).date()

        latest_date_row = await session.execute(
            select(func.max(StarSnapshot.snapshot_date))
        )
        latest_date = latest_date_row.scalar()
        positive_growth = 0
        if latest_date is not None:
            latest_rows = await session.execute(
                select(StarSnapshot.repository_id, StarSnapshot.stars_count).where(
                    StarSnapshot.snapshot_date == latest_date
                )
            )
            for repo_id, stars in latest_rows.all():
                prev = await session.scalar(
                    select(StarSnapshot.stars_count)
                    .where(
                        StarSnapshot.repository_id == repo_id,
                        StarSnapshot.snapshot_date <= today - timedelta(days=1),
                    )
                    .order_by(StarSnapshot.snapshot_date.desc())
                    .limit(1)
                )
                if prev is not None and stars > prev:
                    positive_growth += 1

        success_row = await session.execute(
            select(CollectionRun)
            .where(CollectionRun.status == "SUCCESS")
            .order_by(CollectionRun.finished_at.desc())
            .limit(1)
        )
        success = success_row.scalar_one_or_none()

        latest_run_row = await session.execute(
            select(CollectionRun).order_by(CollectionRun.started_at.desc()).limit(1)
        )
        latest_run = latest_run_row.scalar_one_or_none()

        return {
            "total_repositories": total,
            "positive_growth_today": positive_growth,
            "last_successful_collection_at": _iso(success.finished_at if success else None),
            "last_run_status": latest_run.status if latest_run else None,
        }

    async def get_languages(self, session: AsyncSession) -> list[dict]:
        rows = await session.execute(
            select(Repository.language, func.count(Repository.id).label("count"))
            .where(
                Repository.available.is_(True),
                Repository.language.isnot(None),
            )
            .group_by(Repository.language)
            .order_by(func.count(Repository.id).desc(), Repository.language.asc())
        )
        return [{"language": language, "count": count} for language, count in rows.all()]


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
