from datetime import UTC, datetime

import httpx
import pytest
import respx

from app.collector.github_client import (
    GitHubAuthError,
    GitHubClient,
    GitHubRateLimitError,
    GitHubRequestError,
)

API = "https://api.github.com"


def make_repo_payload(github_id: int = 1, name: str = "agent-hub") -> dict:
    return {
        "id": github_id,
        "name": name,
        "full_name": f"octocat/{name}",
        "owner": {"login": "octocat"},
        "html_url": f"https://github.com/octocat/{name}",
        "homepage": None,
        "description": "A useful agent",
        "language": "Python",
        "topics": ["ai-agent"],
        "stargazers_count": 150,
        "forks_count": 10,
        "open_issues_count": 2,
        "archived": False,
        "disabled": False,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-08-01T00:00:00Z",
        "ignored_field": "must be ignored",
    }


@pytest.fixture()
def client() -> GitHubClient:
    return GitHubClient(token="test-token", retry_delays=(0.0, 0.0, 0.0))


@respx.mock
async def test_search_sends_expected_headers(client: GitHubClient) -> None:
    route = respx.get(f"{API}/search/repositories").mock(
        return_value=httpx.Response(200, json={"items": [make_repo_payload()]})
    )
    async with client:
        await client.search_repositories("topic:ai-agent", 100)
    request = route.calls[0].request
    assert request.headers["accept"] == "application/vnd.github+json"
    assert request.headers["authorization"] == "Bearer test-token"
    assert request.headers["x-github-api-version"] == "2022-11-28"
    assert "stars:>=100" in request.url.params["q"]
    assert "fork:false" in request.url.params["q"]
    assert "archived:false" in request.url.params["q"]
    assert request.url.params["sort"] == "stars"
    assert request.url.params["per_page"] == "100"


@respx.mock
async def test_search_follows_link_header_pagination(client: GitHubClient) -> None:
    next_url = f"{API}/search/repositories?q=topic:ai-agent&page=2"
    respx.get(f"{API}/search/repositories").mock(
        side_effect=[
            httpx.Response(
                200,
                json={"items": [make_repo_payload(1, "repo-a")]},
                headers={"Link": f'<{next_url}>; rel="next"'},
            ),
            httpx.Response(200, json={"items": [make_repo_payload(2, "repo-b")]}),
        ]
    )
    async with client:
        repos = await client.search_repositories("topic:ai-agent", 100)
    assert [repo.name for repo in repos] == ["repo-a", "repo-b"]
    assert [repo.github_id for repo in repos] == [1, 2]


@respx.mock
async def test_search_stops_at_1000_results(client: GitHubClient) -> None:
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        headers = {}
        if call_count < 10:
            headers["Link"] = (
                f'<{API}/search/repositories?q=topic:ai-agent&page={call_count + 1}>; rel="next"'
            )
        items = [make_repo_payload(call_count * 100 + i) for i in range(100)]
        return httpx.Response(200, json={"items": items}, headers=headers)

    respx.get(f"{API}/search/repositories").mock(side_effect=handler)
    async with client:
        repos = await client.search_repositories("topic:ai-agent", 100)
    assert len(repos) == 1000


@respx.mock
async def test_get_repository_returns_none_on_404(client: GitHubClient) -> None:
    respx.get(f"{API}/repos/octocat/missing").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    async with client:
        repo = await client.get_repository("octocat/missing")
    assert repo is None


@respx.mock
async def test_get_repository_parses_dto(client: GitHubClient) -> None:
    respx.get(f"{API}/repos/octocat/agent-hub").mock(
        return_value=httpx.Response(200, json=make_repo_payload())
    )
    async with client:
        repo = await client.get_repository("octocat/agent-hub")
    assert repo is not None
    assert repo.full_name == "octocat/agent-hub"
    assert repo.stars_count == 150
    assert repo.topics == ["ai-agent"]
    assert repo.github_created_at.year == 2026


@respx.mock
async def test_rate_limit_error_when_remaining_zero(client: GitHubClient) -> None:
    respx.get(f"{API}/search/repositories").mock(
        return_value=httpx.Response(
            403,
            json={"message": "API rate limit exceeded"},
            headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1752000000"},
        )
    )
    async with client:
        with pytest.raises(GitHubRateLimitError) as exc_info:
            await client.search_repositories("topic:ai-agent", 100)
    assert exc_info.value.reset_at == datetime.fromtimestamp(1752000000, tz=UTC)


@respx.mock
async def test_auth_error_on_401(client: GitHubClient) -> None:
    respx.get(f"{API}/search/repositories").mock(
        return_value=httpx.Response(401, json={"message": "Bad credentials"})
    )
    async with client:
        with pytest.raises(GitHubAuthError):
            await client.search_repositories("topic:ai-agent", 100)


@respx.mock
async def test_retries_three_times_then_raises(client: GitHubClient) -> None:
    route = respx.get(f"{API}/search/repositories").mock(
        return_value=httpx.Response(500, json={"message": "boom"})
    )
    async with client:
        with pytest.raises(GitHubRequestError):
            await client.search_repositories("topic:ai-agent", 100)
    assert len(route.calls) == 3


@respx.mock
async def test_retries_transport_disconnect_then_wraps_error(client: GitHubClient) -> None:
    route = respx.get(f"{API}/repos/octocat/flaky").mock(
        side_effect=httpx.RemoteProtocolError("server disconnected")
    )

    async with client:
        with pytest.raises(GitHubRequestError, match="transport failed"):
            await client.get_repository("octocat/flaky")

    assert len(route.calls) == 3


@respx.mock
async def test_get_rate_limit_parses_headers(client: GitHubClient) -> None:
    respx.get(f"{API}/rate_limit").mock(
        return_value=httpx.Response(
            200,
            json={"resources": {"core": {"remaining": 42, "reset": 1752000000}}},
            headers={"X-RateLimit-Remaining": "42"},
        )
    )
    async with client:
        rate_limit = await client.get_rate_limit()
    assert rate_limit.remaining == 42
    assert rate_limit.reset_at == datetime.fromtimestamp(1752000000, tz=UTC)




