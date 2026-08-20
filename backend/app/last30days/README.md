# Last 30 Days Module

Fetches and ranks the latest Hacker News stories from the past 30 days using the public keyless Algolia HN API.

## Endpoint

```
POST /api/v1/last30days
```

### Request Body (JSON)

| Field   | Type   | Default | Description                     |
|---------|--------|---------|----------------------------------|
| query   | string | null    | Optional search query            |
| limit   | int    | 50      | Max items to return (1–100)      |

### Example

```bash
curl -X POST http://localhost:8000/api/v1/last30days \
  -H 'Content-Type: application/json' \
  -d '{"query": "python", "limit": 20}'
```

### Response

```json
{
  "status": "working",
  "items": [
    {
      "object_id": "12345",
      "created_at": "2026-08-19T10:00:00.000Z",
      "title": "Example Story",
      "url": "https://example.com/article",
      "author": "user1",
      "points": 150,
      "num_comments": 42,
      "story_text": "",
      "citation_url": "https://example.com/article"
    }
  ],
  "fetched_at": "2026-08-20T01:00:00+00:00"
}
```

## Source Status Values

| Status         | Meaning                                                    |
|----------------|------------------------------------------------------------|
| `working`      | Success with at least one result                           |
| `no-results`   | Success but zero results after normalization               |
| `partial`      | Some items were dropped (invalid/duplicate); results exist |
| `error`        | An exception occurred during fetch or processing           |
| `skipped`      | Module disabled via `LAST30DAYS_ENABLED=false`             |
| `unconfigured` | Critical config missing (cannot occur with defaults)       |

## Configuration

Set via environment variables or `.env` file (no secrets required):

| Variable              | Default                                  | Description           |
|-----------------------|------------------------------------------|------------------------|
| `LAST30DAYS_ENABLED`  | `true`                                   | Enable/disable module  |
| `LAST30DAYS_BASE_URL` | `https://hn.algolia.com/api/v1`         | Algolia HN API base    |

## Frontend

Visit `/last30days` in the app to use the interactive query page.

## Design Notes

- Items are deduplicated by `objectID` and normalized external URL (preferring higher-point version)
- Ranked by: points (desc) → num_comments (desc) → created_at (desc)
- Citation URL falls back to `https://news.ycombinator.com/item?id=<objectID>` when no external URL
- No secrets, cookies, tokens, or local data are read or sent
