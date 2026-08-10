from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import Integer, Text, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import REPOSITORY_NOT_FOUND, ApiError
from app.db.models import CollectionRun, Repository, StarSnapshot
from app.schemas.common import PageParams
from app.schemas.repository import RepositoryDetail, RepositoryListItem


class RepositoryService:
    def __init__(self, business_timezone: str = "Asia/Shanghai") -> None:
        self._timezone = ZoneInfo(business_timezone)

    async def list_repositories(
        self,
        session: AsyncSession,
        page_params: PageParams,
        *,
        sort: str,
        category: str | None,
        language: str | None,
        min_stars: int | None,
        q: str | None,
    ) -> dict:
        latest, daily_base, weekly_base = self._snapshot_joins()

        latest_stars = cast(latest.c.stars_count, Integer).label("latest_stars")
        base_daily = cast(daily_base.c.stars_count, Integer)
        base_weekly = cast(weekly_base.c.stars_count, Integer)
        daily_stars = (latest_stars - base_daily).label("daily_stars")
        weekly_stars = (latest_stars - base_weekly).label("weekly_stars")

        query = (
            select(
                Repository,
                latest_stars,
                daily_stars,
                weekly_stars,
            )
            .join(latest, Repository.id == latest.c.repository_id)
            .outerjoin(daily_base, Repository.id == daily_base.c.repository_id)
            .outerjoin(weekly_base, Repository.id == weekly_base.c.repository_id)
            .where(Repository.available.is_(True))
        )

        if category:
            query = query.where(
                cast(Repository.categories, Text).like(f'%"{category}"%')
            )
        if language:
            query = query.where(Repository.language == language)
        if min_stars is not None:
            query = query.where(Repository.stars_count >= min_stars)
        if q:
            pattern = f"%{q}%"
            query = query.where(
                Repository.owner.like(pattern)
                | Repository.name.like(pattern)
                | Repository.description.like(pattern)
            )

        if sort == "total_stars":
            sort_col = Repository.stars_count
        elif sort == "weekly_stars":
            sort_col = weekly_stars
        else:
            sort_col = daily_stars

        query = query.order_by(
            sort_col.is_(None),
            sort_col.desc(),
            Repository.stars_count.desc(),
            Repository.id.desc(),
        )

        total = await session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await session.execute(
            query.offset((page_params.page - 1) * page_params.page_size).limit(
                page_params.page_size
            )
        )

        items = [
            self._to_list_item(row, daily, weekly)
            for row, _latest, daily, weekly in rows.all()
        ]
        last_success = await self._last_successful_collection(session)
        return {
            "items": items,
            "page": page_params.page,
            "page_size": page_params.page_size,
            "total": total,
            "last_successful_collection_at": last_success,
        }

    async def get_detail(
        self, session: AsyncSession, owner: str, name: str
    ) -> RepositoryDetail:
        result = await session.execute(
            select(Repository).where(
                Repository.owner == owner,
                Repository.name == name,
                Repository.available.is_(True),
            )
        )
        repository = result.scalar_one_or_none()
        if repository is None:
            raise ApiError(REPOSITORY_NOT_FOUND, "Repository not found", 404)

        today = datetime.now(self._timezone).date()
        daily = await self._growth_between(session, repository.id, today, 1)
        weekly = await self._growth_between(session, repository.id, today, 7)

        trend_rows = await session.execute(
            select(StarSnapshot)
            .where(StarSnapshot.repository_id == repository.id)
            .order_by(StarSnapshot.snapshot_date.desc())
            .limit(30)
        )
        trend = [
            {
                "snapshot_date": snap.snapshot_date.isoformat(),
                "stars_count": snap.stars_count,
            }
            for snap in reversed(trend_rows.scalars().all())
        ]

        return RepositoryDetail(
            id=repository.id,
            owner=repository.owner,
            name=repository.name,
            description=repository.description,
            html_url=repository.html_url,
            homepage=repository.homepage,
            language=repository.language,
            topics=list(repository.topics or []),
            categories=list(repository.categories or []),
            matched_rules=list(repository.matched_rules or []),
            stars_count=repository.stars_count,
            forks_count=repository.forks_count,
            open_issues_count=repository.open_issues_count,
            daily_stars=daily,
            weekly_stars=weekly,
            last_synced_at=_iso(repository.last_synced_at),
            github_created_at=_iso(repository.github_created_at),
            trend=trend,
        )

    def _snapshot_joins(self):
        latest = self._latest_snapshot()
        daily_base = self._baseline_snapshot(
            latest.c.snapshot_date, offset_days=1
        )
        weekly_base = self._baseline_snapshot(
            latest.c.snapshot_date, offset_days=7
        )
        return latest, daily_base, weekly_base

    def _latest_snapshot(self):
        latest_date = (
            select(
                StarSnapshot.repository_id.label("repository_id"),
                func.max(StarSnapshot.snapshot_date).label("latest_date"),
            )
            .group_by(StarSnapshot.repository_id)
            .subquery()
        )
        return (
            select(
                latest_date.c.repository_id,
                StarSnapshot.snapshot_date,
                StarSnapshot.stars_count,
            )
            .join(
                StarSnapshot,
                (StarSnapshot.repository_id == latest_date.c.repository_id)
                & (StarSnapshot.snapshot_date == latest_date.c.latest_date),
            )
            .subquery()
        )

    def _baseline_snapshot(self, latest_date, offset_days: int):
        cutoff = latest_date.op("-")(text(f"INTERVAL {offset_days} DAY"))
        base_date = (
            select(
                StarSnapshot.repository_id.label("repository_id"),
                func.max(StarSnapshot.snapshot_date).label("base_date"),
            )
            .where(StarSnapshot.snapshot_date <= cutoff)
            .group_by(StarSnapshot.repository_id)
            .subquery()
        )
        return (
            select(
                base_date.c.repository_id,
                StarSnapshot.stars_count,
            )
            .join(
                StarSnapshot,
                (StarSnapshot.repository_id == base_date.c.repository_id)
                & (StarSnapshot.snapshot_date == base_date.c.base_date),
            )
            .subquery()
        )

    def _to_list_item(self, row, daily: int | None, weekly: int | None) -> RepositoryListItem:
        return RepositoryListItem(
            id=row.id,
            owner=row.owner,
            name=row.name,
            description=row.description,
            html_url=row.html_url,
            language=row.language,
            topics=list(row.topics or []),
            categories=list(row.categories or []),
            stars_count=row.stars_count,
            daily_stars=daily,
            weekly_stars=weekly,
            last_synced_at=_iso(row.last_synced_at),
            trend=[],
        )

    async def _growth_between(
        self, session: AsyncSession, repository_id: int, target: datetime.date, days: int
    ) -> int | None:
        cutoff = target - timedelta(days=days)
        base_row = await session.execute(
            select(StarSnapshot)
            .where(
                StarSnapshot.repository_id == repository_id,
                StarSnapshot.snapshot_date <= cutoff,
            )
            .order_by(StarSnapshot.snapshot_date.desc())
            .limit(1)
        )
        base = base_row.scalar_one_or_none()
        latest_row = await session.execute(
            select(StarSnapshot)
            .where(
                StarSnapshot.repository_id == repository_id,
                StarSnapshot.snapshot_date <= target,
            )
            .order_by(StarSnapshot.snapshot_date.desc())
            .limit(1)
        )
        latest = latest_row.scalar_one_or_none()
        if latest is None or base is None:
            return None
        return latest.stars_count - base.stars_count

    async def _last_successful_collection(self, session: AsyncSession) -> str | None:
        row = await session.execute(
            select(CollectionRun)
            .where(CollectionRun.status == "SUCCESS")
            .order_by(CollectionRun.started_at.desc())
            .limit(1)
        )
        run = row.scalar_one_or_none()
        return _iso(run.finished_at if run else None)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
