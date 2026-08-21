# Last 30 Days Module

This module adapts the user-level `last30days` skill to Skill Finder. It runs the installed engine as a subprocess and returns its agent JSON profile instead of maintaining a separate Hacker News-only implementation.

## API

- `GET /api/v1/last30days/status` checks the installed skill/runtime and lists currently available sources.
- `POST /api/v1/last30days` runs research for a required topic.

```json
{
  "query": "OpenAI Codex",
  "limit": 20
}
```

The response contains `clusters`, individual `items`, `sources`, and per-source status. The UI is available from the primary navigation as **近 30 天研究**.

## Runtime discovery

By default the adapter searches these user-level installations:

1. `~/.codex/skills/last30days`
2. `~/.agents/skills/last30days`
3. `~/.claude/skills/last30days`

It also discovers Python 3.12+ from the current interpreter, `PATH`, or a bundled Codex runtime. Override discovery only when necessary:

| Variable | Purpose |
| --- | --- |
| `LAST30DAYS_ENABLED` | Enable or disable the module |
| `LAST30DAYS_SKILL_DIR` | Explicit installed skill directory |
| `LAST30DAYS_PYTHON` | Explicit Python 3.12+ executable |
| `LAST30DAYS_MEMORY_DIR` | Optional research artifact directory |
| `LAST30DAYS_TIMEOUT_SECONDS` | Subprocess timeout, default 600 seconds |

The subprocess receives only basic operating-system variables, `LAST30DAYS_*` configuration, and credential variables understood by the skill. Skill Finder database and admin configuration are not forwarded.

## Data access

Submitting research sends the topic to the external sources enabled by the user's `last30days` installation. The status endpoint exposes those sources before a run. Source availability depends on the local skill configuration and optional credentials.
