from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.db.session import async_session_factory
from app.repositories.repositories import RepositoryStore

logger = logging.getLogger(__name__)


class IntroductionGenerationError(Exception):
    """Raised when the opencode CLI cannot produce an introduction."""


@dataclass
class RepositoryBrief:
    owner: str
    name: str
    description: str | None
    language: str | None
    topics: list[str]
    stars_count: int
    homepage: str | None
    html_url: str

    def to_payload(self) -> dict:
        return {
            "owner": self.owner,
            "name": self.name,
            "description": self.description,
            "language": self.language,
            "topics": self.topics,
            "stars": self.stars_count,
            "homepage": self.homepage,
        }


def _find_opencode() -> str:
    """Resolve the opencode executable (npm shims are not executable directly)."""
    for name in ("opencode.exe", "opencode.cmd", "opencode"):
        found = shutil.which(name)
        if found and not found.lower().endswith(".cmd"):
            return found
    shim = shutil.which("opencode.ps1")
    if shim:
        candidate = Path(shim).resolve().parent / "node_modules" / "opencode-ai" / "bin" / "opencode.exe"
        if candidate.exists():
            return str(candidate)
    shim = shutil.which("opencode.cmd")
    if shim:
        candidate = Path(shim).resolve().parent / "node_modules" / "opencode-ai" / "bin" / "opencode.exe"
        if candidate.exists():
            return str(candidate)
    raise IntroductionGenerationError(
        "opencode CLI not found on PATH; install opencode or set INTRO_OPCODE_BIN"
    )


def _build_prompt(repos: list[RepositoryBrief]) -> str:
    payload = json.dumps([r.to_payload() for r in repos], ensure_ascii=False, indent=2)
    return (
        "你是开源项目介绍撰写助手。请为下面每个 GitHub 仓库写一份中文介绍，"
        "每个仓库包含三个部分：\n"
        "1. introduction：简单介绍（2-3 句话，说明这个项目是什么、解决什么问题、主要特点）\n"
        "2. usage：用法（2-3 句话，说明如何使用、如何安装或集成，基于提供的信息，不要编造具体命令）\n"
        "3. domains：用到的领域（3-5 个名词短语，例如 AI Agent、RAG、自动化、前端开发）\n"
        "只能基于提供的信息撰写，不要编造事实，不要输出任何解释或前缀。"
        "不要使用任何工具，不要读取或搜索任何文件，直接回答。\n\n"
        f"仓库信息：\n{payload}\n\n"
        "输出要求：只输出一个 JSON 数组，数组元素为对象，顺序与输入完全一致，例如：\n"
        '[{"introduction": "简单介绍", "usage": "用法", "domains": ["领域一", "领域二"]}]'
    )


def _parse_opencode_output(output: str) -> str:
    """Extract assistant text from `opencode run --format json` event lines."""
    parts: list[str] = []
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "text":
            continue
        part = event.get("part") or {}
        if part.get("type") == "text":
            text = part.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "".join(parts)


def _parse_introductions(text: str, count: int) -> list[str]:
    """Extract a JSON array of {introduction, usage, domains} objects."""
    text = text.strip()
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        raise IntroductionGenerationError("could not parse introductions from model output")
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise IntroductionGenerationError(
            "could not parse introductions from model output"
        ) from exc
    if not isinstance(parsed, list) or len(parsed) < count:
        raise IntroductionGenerationError("could not parse introductions from model output")
    items: list[str] = []
    for entry in parsed[:count]:
        if isinstance(entry, str):
            items.append(json.dumps(
                {"introduction": entry, "usage": "", "domains": []},
                ensure_ascii=False,
            ))
            continue
        if not isinstance(entry, dict):
            raise IntroductionGenerationError(
                "could not parse introductions from model output"
            )
        items.append(json.dumps(
            {
                "introduction": str(entry.get("introduction", "")).strip(),
                "usage": str(entry.get("usage", "")).strip(),
                "domains": [
                    str(d).strip()
                    for d in entry.get("domains", [])
                    if isinstance(d, (str, int)) and str(d).strip()
                ],
            },
            ensure_ascii=False,
        ))
    return items


def generate_introductions(
    repos: list[RepositoryBrief],
    *,
    model: str | None = None,
    timeout: int | None = None,
) -> list[str]:
    """Generate Chinese introductions for the given repos via the opencode CLI."""
    if not repos:
        return []
    model = model or settings.intro_model
    timeout = timeout or settings.intro_timeout_seconds
    prompt = _build_prompt(repos)
    try:
        result = subprocess.run(
            [
                _find_opencode(),
                "run",
                "--format",
                "json",
                "-m",
                model,
                prompt,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise IntroductionGenerationError("opencode run timed out") from exc
    except OSError as exc:
        raise IntroductionGenerationError(f"failed to run opencode: {exc}") from exc
    output = result.stdout or ""
    if result.returncode != 0:
        logger.warning(
            "opencode exited with %s; stderr=%s", result.returncode, (result.stderr or "")[:500]
        )
    text = _parse_opencode_output(output)
    if not text.strip():
        raise IntroductionGenerationError("opencode produced no text output")
    return _parse_introductions(text, len(repos))


def brief_from_repository(repository) -> RepositoryBrief:
    return RepositoryBrief(
        owner=repository.owner,
        name=repository.name,
        description=repository.description,
        language=repository.language,
        topics=list(repository.topics or []),
        stars_count=repository.stars_count,
        homepage=repository.homepage,
        html_url=repository.html_url,
    )


async def run_introduction_backfill(
    *,
    category: str | None = None,
    limit: int = 5,
) -> dict:
    """Generate introductions for repositories missing one, in the background."""
    async with async_session_factory() as session:
        store = RepositoryStore(session)
        pending = await store.list_without_introduction(category=category, limit=limit)
        updated = 0
        failed = 0
        batch_size = settings.intro_batch_size
        for start in range(0, len(pending), batch_size):
            batch = pending[start : start + batch_size]
            try:
                texts = await asyncio.to_thread(
                    generate_introductions,
                    [brief_from_repository(repo) for repo in batch],
                )
            except IntroductionGenerationError as exc:
                logger.error("introduction batch failed: %s", exc)
                failed += len(batch)
                continue
            for repo, text in zip(batch, texts):
                if not text:
                    failed += 1
                    continue
                await store.update_introduction(repo.github_id, text)
                updated += 1
            await session.commit()
    return {"updated": updated, "failed": failed, "total": len(pending)}
