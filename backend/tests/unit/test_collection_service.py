from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.collector.github_client import (
    GitHubAuthError,
    GitHubClient,
    GitHubRateLimitError,
    GitHubRepository,
    GitHubRequestError,
)
from app.collector.service import DISCOVERY_QUERIES, CollectionService


def make_repo(
    github_id: int,
    full_name: str | None = None,
    stars: int = 200,
    archived: bool = False,
    disabled: bool = False,
    fork: bool = False,
    topics: list[str] | None = None,
) -> GitHubRepository:
    owner, name = (full_name or f"owner/repo-{github_id}").split("/")
    return GitHubRepository(
        github_id=github_id,
        owner=owner,
        name=name,
        full_name=f"{owner}/{name}",
        html_url=f"https://github.com/{owner}/{name}",
        homepage=None,
        description="An agent framework",
        language="Python",
        topics=topics or ["ai-agent"],
        stars_count=stars,
        forks_count=10,
        open_issues_count=1,
        archived=archived,
        disabled=disabled,
        fork=fork,
        github_created_at=datetime(2026, 1, 1, tzinfo=UTC),
        github_updated_at=datetime(2026, 8, 1, tzinfo=UTC),
    )


class FakeSession:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


class FakeRepositoryStore:
    def __init__(self, available: list[GitHubRepository] | None = None) -> None:
        self.upserted: list[GitHubRepository] = []
        self.available_repos = list(available or [])
        self.marked_unavailable: list[int] = []

    async def upsert(self, repo, classification):
        self.upserted.append((repo, classification))
        return SimpleNamespace(id=repo.github_id)

    async def list_available(self):
        return self.available_repos

    async def mark_unavailable(self, github_ids):
        self.marked_unavailable.extend(github_ids)


class FakeSnapshotStore:
    def __init__(self) -> None:
        self.writes: list[tuple[int, object, int]] = []

    async def upsert_daily(self, repository_id, snapshot_date, stars_count):
        self.writes.append((repository_id, snapshot_date, stars_count))


class FakeRunStore:
    def __init__(self) -> None:
        self.finished: list[dict] = []
        self._next_id = 1

    async def create(self, trigger_type):
        run = SimpleNamespace(id=self._next_id, trigger_type=trigger_type)
        self._next_id += 1
        return run

    async def finish(self, run, **kwargs):
        self.finished.append({"run_id": run.id, **kwargs})


class FakeGitHubClient(GitHubClient):
    def __init__(
        self,
        search_results: dict[str, list[GitHubRepository]] | None = None,
        repo_lookup: dict[str, GitHubRepository | None] | None = None,
        failures: dict[str, type[Exception]] | None = None,
    ) -> None:
        super().__init__(token="test-token", retry_delays=(0.0, 0.0, 0.0))
        self.search_results = search_results or {}
        self.repo_lookup = repo_lookup or {}
        self.failures = failures or {}
        self.search_calls: list[str] = []

    async def search_repositories(self, query, min_stars):
        self.search_calls.append(query)
        return self.search_results.get(query, [])

    async def get_repository(self, full_name):
        if full_name in self.failures:
            raise self.failures[full_name]
        return self.repo_lookup.get(full_name)

    async def get_rate_limit(self):
        return SimpleNamespace(remaining=5000, reset_at=datetime(2026, 8, 10, tzinfo=UTC))


@pytest.fixture()
def session() -> FakeSession:
    return FakeSession()


def make_service(
    session: FakeSession,
    github: FakeGitHubClient,
    available: list[GitHubRepository] | None = None,
) -> CollectionService:
    return CollectionService(
        github_client=github,
        repository_store=FakeRepositoryStore(available),
        snapshot_store=FakeSnapshotStore(),
        run_store=FakeRunStore(),
        session=session,
        trigger_type="manual",
    )


async def test_deduplicates_and_filters(session: FakeSession) -> None:
    duplicate = make_repo(1, "a/dup")
    github = FakeGitHubClient(
        search_results={
            "topic:ai-agent": [duplicate],
            "topic:agent-skills": [duplicate],
        }
    )
    service = make_service(session, github)

    result = await service.run()

    assert len(service.repository_store.upserted) == 1
    assert service.repository_store.upserted[0][0].github_id == 1
    assert result.status == "SUCCESS"
    assert len(service.repository_store.upserted[0][1].categories) > 0
    assert result.query_count == len(DISCOVERY_QUERIES)
    assert len(service.repository_store.upserted[0][1].matched_rules) > 0


async def test_filters_out_ineligible(session: FakeSession) -> None:
    github = FakeGitHubClient(
        search_results={
            "topic:ai-agent": [
                make_repo(1, "a/good"),
                make_repo(2, "a/forked", fork=True),
                make_repo(3, "a/archived", archived=True),
                make_repo(4, "a/disabled", disabled=True),
                make_repo(5, "a/low", stars=10),
            ]
        }
    )
    service = make_service(session, github)

    await service.run()

    ids = [repo.github_id for repo, _ in service.repository_store.upserted]
    assert ids == [1]


async def test_refresh_marks_unavailable_and_partial(session: FakeSession) -> None:
    available = [
        make_repo(10, "a/ok"),
        make_repo(11, "a/removed"),
        make_repo(12, "a/flaky"),
    ]
    github = FakeGitHubClient(
        repo_lookup={
            "a/ok": make_repo(10, "a/ok"),
            "a/removed": None,
        },
        failures={"a/flaky": GitHubRequestError("boom")},
    )
    service = make_service(session, github, available=available)

    result = await service.run()

    assert 11 in service.repository_store.marked_unavailable
    assert 12 not in service.repository_store.marked_unavailable
    assert result.status == "PARTIAL"
    assert result.failed_count == 1


async def test_refresh_skips_repositories_already_discovered(session: FakeSession) -> None:
    repository = make_repo(10, "a/current")
    github = FakeGitHubClient(
        search_results={"topic:ai-agent": [repository]},
        failures={"a/current": GitHubRequestError("must not refresh twice")},
    )
    service = make_service(session, github, available=[repository])

    result = await service.run()

    assert result.status == "SUCCESS"
    assert result.updated_count == 1
    assert result.failed_count == 0


async def test_auth_failure_marks_failed_and_reraises(session: FakeSession) -> None:
    github = FakeGitHubClient(failures={"a/any": GitHubAuthError("bad token")})
    service = make_service(
        session,
        github,
        available=[make_repo(10, "a/any")],
    )

    with pytest.raises(GitHubAuthError):
        await service.run()

    assert service.run_store.finished[0]["status"] == "FAILED"
    assert "GitHubAuthError" in service.run_store.finished[0]["error_summary"]


async def test_rate_limit_failure_marks_failed(session: FakeSession) -> None:
    github = FakeGitHubClient(
        failures={"a/any": GitHubRateLimitError(datetime(2026, 8, 10, tzinfo=UTC))}
    )
    service = make_service(
        session,
        github,
        available=[make_repo(10, "a/any")],
    )

    with pytest.raises(GitHubRateLimitError):
        await service.run()

    assert service.run_store.finished[0]["status"] == "FAILED"


async def test_writes_daily_snapshot_for_business_date(session: FakeSession) -> None:
    github = FakeGitHubClient(
        search_results={"topic:ai-agent": [make_repo(1, "a/snap")]}
    )
    service = make_service(session, github)

    result = await service.run()

    assert service.snapshot_store.writes[0][1] == service._business_date
    assert service.snapshot_store.writes[0][2] == 200
    assert result.status == "SUCCESS"
