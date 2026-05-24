# API Reference

The Anglican Daily Office API is a FastAPI application. Interactive documentation
is available at runtime:

- **Swagger UI** — `http://localhost:8000/docs`
- **ReDoc** — `http://localhost:8000/redoc`
- **OpenAPI JSON** — `http://localhost:8000/openapi.json`

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | [`/api/office/{date}`](office.md) | Complete Daily Office for a date |
| `GET` | [`/api/bible/{reference}`](bible.md) | Verse text for a reference string |
| `GET` | [`/api/psalms/{numbers}`](psalms.md) | Full text of one or more psalms |
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

All endpoints return JSON error bodies in FastAPI's standard format:

```json
{"detail": "No lectionary entry found for 2026-06-15"}
```

| HTTP status | Meaning |
|---|---|
| 404 | Resource not found (no readings for that date; reference not parseable) |
| 422 | Validation error (bad date format; non-numeric psalm number) |
| 500 | Unexpected server error |
