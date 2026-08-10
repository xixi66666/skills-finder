from __future__ import annotations

import re
from dataclasses import dataclass

CATEGORY_AGENT = "AGENT"
CATEGORY_SKILL = "SKILL"
CATEGORY_MCP = "MCP"

TOPIC_RULES: tuple[tuple[str, str], ...] = (
    ("ai-agent", CATEGORY_AGENT),
    ("agent-framework", CATEGORY_AGENT),
    ("agentic-ai", CATEGORY_AGENT),
    ("autonomous-agent", CATEGORY_AGENT),
    ("agent-skills", CATEGORY_SKILL),
    ("ai-skills", CATEGORY_SKILL),
    ("claude-skills", CATEGORY_SKILL),
    ("codex-skills", CATEGORY_SKILL),
    ("mcp-server", CATEGORY_MCP),
    ("model-context-protocol", CATEGORY_MCP),
)

PHRASE_RULES: tuple[tuple[str, str], ...] = (
    ("agent framework", CATEGORY_AGENT),
    ("agent frameworks", CATEGORY_AGENT),
    ("agent skills", CATEGORY_SKILL),
    ("ai skills", CATEGORY_SKILL),
    ("mcp server", CATEGORY_MCP),
    ("mcp servers", CATEGORY_MCP),
    ("model context protocol", CATEGORY_MCP),
)

_PHRASE_PATTERNS: tuple[tuple[re.Pattern[str], str, str], ...] = tuple(
    (re.compile(rf"\b{re.escape(phrase)}\b"), phrase, category)
    for phrase, category in PHRASE_RULES
)

_CATEGORY_ORDER: dict[str, int] = {
    CATEGORY_AGENT: 0,
    CATEGORY_SKILL: 1,
    CATEGORY_MCP: 2,
}


@dataclass(frozen=True)
class Classification:
    categories: tuple[str, ...]
    matched_rules: tuple[str, ...]


def _normalize(text: str) -> str:
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return re.sub(r"[^a-z0-9]+", " ", text.lower())


def classify_repository(name: str, description: str, topics: list[str]) -> Classification:
    matched_rules: list[str] = []
    categories: list[str] = []

    topic_set = {topic.lower() for topic in topics}
    for topic, category in TOPIC_RULES:
        if topic in topic_set:
            matched_rules.append(f"topic:{topic}")
            _add_category(categories, category)

    fields = (
        ("name", _normalize(name)),
        ("description", _normalize(description)),
    )
    for field, text in fields:
        for pattern, phrase, category in _PHRASE_PATTERNS:
            if pattern.search(text):
                matched_rules.append(f"{field}:{phrase}")
                _add_category(categories, category)

    categories.sort(key=_CATEGORY_ORDER.__getitem__)

    return Classification(categories=tuple(categories), matched_rules=tuple(matched_rules))


def _add_category(categories: list[str], category: str) -> None:
    if category not in categories:
        categories.append(category)
