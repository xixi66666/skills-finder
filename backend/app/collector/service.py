from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.collector.classifier import classify_repository
from app.collector.github_client import (
    GitHubAuthError,
    GitHubClient,
    GitHubRateLimitError,
    GitHubRepository,
    GitHubRequestError,
)
from app.core.config import settings
from app.db.models import CollectionRun, Repository
from app.repositories.collection_runs import CollectionRunStore
from app.repositories.repositories import RepositoryStore
from app.repositories.snapshots import SnapshotStore

logger = logging.getLogger(__name__)

DISCOVERY_QUERIES = (
    "topic:ai-agent",
    '"agent framework" in:name,description',
    "topic:agentic-ai",
    "topic:agent-skills",
    '"agent skills" in:name,description',
    "topic:mcp-server",
    "topic:model-context-protocol",
)

STATUS_SUCCESS = "SUCCESS"
STATUS_PARTIAL = "PARTIAL"
STATUS_FAILED = "FAILED"


@dataclass
class CollectionResult:
    run_id: int
    status: str
    query_count: int
    discovered_count: int
    updated_count: int
    failed_count: int
    rate_limit_remaining: int | None = None
    rate_limit_reset_at: datetime | None = None
    error_summary: str | None = None
    skipped_locked: bool = False


@dataclass
class CollectionService:
    github_client: GitHubClient
    repository_store: RepositoryStore
    snapshot_store: SnapshotStore
    run_store: CollectionRunStore
    session: AsyncSession
    business_timezone: str = "Asia/Shanghai"
    min_stars: int = 100
    trigger_type: str = "scheduled"
    discovered: list[GitHubRepository] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._timezone = ZoneInfo(self.business_timezone)

    @property
    def _business_date(self) -> date:
        return datetime.now(self._timezone).date()

    async def run(self) -> CollectionResult:
        run = await self.run_store.create(self.trigger_type)
        result = CollectionResult(
            run_id=run.id,
            status=STATUS_SUCCESS,
            query_count=len(DISCOVERY_QUERIES),
            discovered_count=0,
            updated_count=0,
            failed_count=0,
        )
        try:
            await self._discover(run, result)
            await self._persist_discovered(result)
            await self._refresh_available(result)
            result.status = STATUS_SUCCESS
            if result.failed_count > 0:
                result.status = STATUS_PARTIAL
            await self._finish(run, result, status=result.status)
            return result
        except (GitHubAuthError, GitHubRateLimitError) as exc:
            result.status = STATUS_FAILED
            result.error_summary = _error_summary(exc)
            await self._finish(run, result, status=STATUS_FAILED)
            raise
        except Exception as exc:
            result.status = STATUS_FAILED
            result.error_summary = _error_summary(exc)
            await self._finish(run, result, status=STATUS_FAILED)
            raise

    async def _discover(self, run: CollectionRun, result: CollectionResult) -> None:
        for query in DISCOVERY_QUERIES:
            repos = await self.github_client.search_repositories(query, self.min_stars)
            self.discovered.extend(repos)
        result.discovered_count = len(self.discovered)
        rate_limit = await self.github_client.get_rate_limit()
        result.rate_limit_remaining = rate_limit.remaining
        result.rate_limit_reset_at = rate_limit.reset_at

    async def _persist_discovered(self, result: CollectionResult) -> None:
        seen_ids: set[int] = set()
        intro_pending: list[Repository] = []
        for repo in self.discovered:
            if repo.github_id in seen_ids:
                continue
            if not self._eligible(repo):
                continue
            seen_ids.add(repo.github_id)
            classification = classify_repository(
                name=repo.name,
                description=repo.description or "",
                topics=repo.topics,
            )
            updated = await self.repository_store.upsert(repo, classification)
            result.updated_count += 1
            await self.snapshot_store.upsert_daily(
                repository_id=updated.id,
                snapshot_date=self._business_date,
                stars_count=repo.stars_count,
            )
            if settings.intro_enabled and updated.introduction is None:
                intro_pending.append(updated)
        await self._generate_introductions(intro_pending)
        await self.session.commit()

    async def _refresh_available(self, result: CollectionResult) -> None:
        available = await self.repository_store.list_available()
        unavailable: list[int] = []
        intro_pending: list[Repository] = []
        for repository in available:
            try:
                repo = await self.github_client.get_repository(repository.full_name)
            except GitHubRequestError:
                result.failed_count += 1
                continue
            except (GitHubAuthError, GitHubRateLimitError):
                raise
            if repo is None:
                unavailable.append(repository.github_id)
                continue
            classification = classify_repository(
                name=repo.name,
                description=repo.description or "",
                topics=repo.topics,
            )
            updated = await self.repository_store.upsert(repo, classification)
            await self.snapshot_store.upsert_daily(
                repository_id=updated.id,
                snapshot_date=self._business_date,
                stars_count=repo.stars_count,
            )
            result.updated_count += 1
            if settings.intro_enabled and updated.introduction is None:
                intro_pending.append(updated)
        await self._generate_introductions(intro_pending)
        await self.repository_store.mark_unavailable(unavailable)
        await self.session.commit()

    async def _generate_introductions(self, repos: list[Repository]) -> None:
        if not repos:
            return
        import asyncio

        from app.services.introduction_service import (
            IntroductionGenerationError,
            brief_from_repository,
            generate_introductions,
        )

        batch_size = settings.intro_batch_size
        for start in range(0, len(repos), batch_size):
            batch = repos[start : start + batch_size]
            try:
                texts = await asyncio.to_thread(
                    generate_introductions,
                    [brief_from_repository(repo) for repo in batch],
                )
            except IntroductionGenerationError as exc:
                logger.warning("introduction generation failed: %s", exc)
                continue
            for repo, text in zip(batch, texts):
                if text:
                    await self.repository_store.update_introduction(repo.github_id, text)

    def _eligible(self, repo: GitHubRepository) -> bool:
        if repo.archived or repo.disabled or repo.fork:
            return False
        return repo.stars_count >= self.min_stars

    async def _finish(
        self,
        run: CollectionRun,
        result: CollectionResult,
        *,
        status: str,
    ) -> None:
        await self.run_store.finish(
            run,
            status=status,
            query_count=result.query_count,
            discovered_count=result.discovered_count,
            updated_count=result.updated_count,
            failed_count=result.failed_count,
            rate_limit_remaining=result.rate_limit_remaining,
            rate_limit_reset_at=result.rate_limit_reset_at,
            error_summary=result.error_summary,
        )
        await self.session.commit()


def _error_summary(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"
