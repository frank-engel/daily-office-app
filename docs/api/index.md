# API Reference

The Anglican Daily Office API is a FastAPI application. Interactive documentation
is available at runtime:

- **Swagger UI** — `http://localhost:8000/docs`
- **ReDoc** — `http://localhost:8000/redoc`
- **OpenAPI JSON** — `http://localhost:8000/openapi.json`

## Browser routes

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Home page — link to today's office |
| `GET` | `/office/{date}` | Daily Office page — Morning/Evening Prayer tabs with readings |
| `GET` | `/full/{date}` | Full Office page — complete rendered Morning/Evening Prayer service |
| `GET` | `/habits` | Habit log — 30-day morning/evening completion grid |

## JSON API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | [`/api/office/{date}`](office.md) | Complete Daily Office — lectionary, psalms, verse text, collect |
| `GET` | `/api/office/{date}/full` | Full ordered service blocks (canticles, versicles, fixed texts) |
| `GET` | [`/api/bible/{reference}`](bible.md) | Verse text for a BCP reference string |
| `GET` | [`/api/psalms/{numbers}`](psalms.md) | Full text of one or more psalms |
| `GET` | `/api/habits` | List morning/evening completions for a date range |
| `POST` | `/api/habits/{date}/{office}` | Mark an office (morning/evening) complete |
| `DELETE` | `/api/habits/{date}/{office}` | Unmark an office completion |
| `GET` | `/health` | Server health check |

## Common conventions

### Date format

All date parameters use ISO 8601: `YYYY-MM-DD`

```
/api/office/2026-05-24
```

### Bible reference format

Both ASCII hyphen (`-`) and Unicode en-dash (`–`) are accepted as range separators.
You can type ordinary hyphens — they are normalized internally.

### Error responses

API endpoints (`/api/…`) return JSON error bodies in FastAPI's standard format:

```json
{"detail": "No lectionary entry found for 2026-06-15"}
```

Browser routes return styled HTML error pages.

| HTTP status | Meaning |
|---|---|
| 404 | Resource not found (no readings for that date; reference not parseable; unknown URL) |
| 422 | Validation error (bad date format; non-numeric psalm number) |
| 500 | Unexpected server error |

### Habits — office values

The `{office}` path segment must be exactly `morning` or `evening`. Any other value returns HTTP 422.
