# Anglican Daily Office App

A personal liturgical practice app serving the **BCP 1979 Daily Office** (Morning Prayer,
Evening Prayer, Noonday, Compline) for any calendar date. Provides accurate lectionary and
psalm assignments, full Bible text, and a minimal habit log.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ · FastAPI · Jinja2 · HTMX |
| Frontend | Tailwind CSS · HTMX (CDN, no build step) |
| Database | SQLite (`web.sqlite` — KJVA Bible, `habits.sqlite` — habit log) |
| Mobile | Android WebView wrapper via `adb reverse` |

## Quick Start

```powershell
# 1. Create and activate virtualenv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies (from project root)
cd backend
pip install -e ".[dev]"

# 3. Acquire the Bible database (see below)

# 4. Start the server
uvicorn main:app --reload
```

Open `http://localhost:8000` — the API is live.  
Interactive API docs (Swagger UI): `http://localhost:8000/docs`

## Bible Database Setup

The KJVA (KJV with Apocrypha) SQLite file is **not committed** to this repo because it is a
binary asset (~5 MB). Acquire it once from [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases):

```powershell
# Sparse-clone — only downloads the one file you need
git clone --depth 1 --filter=blob:none --sparse https://github.com/scrollmapper/bible_databases.git bible_dbs
Set-Location bible_dbs
git sparse-checkout set --skip-checks formats/sqlite/KJVA.db
git checkout
Copy-Item formats/sqlite/KJVA.db ..\daily-office-app\backend\data\web.sqlite
Set-Location ..
Remove-Item -Recurse -Force bible_dbs
```

The server logs a warning at startup for any missing Apocryphal books; it will never crash on
a missing book — it returns `"[Text not available in this edition]"` for those verses.

## Running Tests

```powershell
cd backend
pytest tests/ -v
```

87 tests pass as of Phase 3: 23 calendar, 40 lectionary, 13 reference-parser, 9 Bible DB
(Bible DB tests are skipped automatically when `web.sqlite` is absent, so CI works without it).

## Security

| Concern | Status |
|---|---|
| `web.sqlite` committed to git | Gitignored (`backend/data/*.sqlite`) |
| `habits.sqlite` committed to git | Gitignored (`backend/data/*.sqlite`) |
| Secrets in code | None — no API keys or passwords in source |
| `.env` committed | Gitignored; only `.env.example` (no real values) is tracked |

No environment secrets are required for the MVP. The `.env.example` documents the two
optional path overrides (`BIBLE_DB_PATH`, `HABITS_DB_PATH`).

## API Reference

Full interactive documentation is available at `http://localhost:8000/docs` (Swagger UI)
or `http://localhost:8000/redoc` (ReDoc) when the server is running.

See also [`docs/api/`](docs/api/) for static Markdown reference.

| Endpoint | Description |
|---|---|
| `GET /api/office/{YYYY-MM-DD}` | Complete Daily Office — lectionary, psalms, and verse text |
| `GET /api/bible/{reference}` | Verse text for any BCP reference string |
| `GET /api/psalms/{n[,n,...]}` | Full text of one or more psalms |
| `GET /health` | Server health check |

## Build Phases

| Phase | Status | Scope |
|---|---|---|
| 1 — Foundation | ✅ Done | Directory layout, `pyproject.toml`, Easter algorithm, 23 calendar tests |
| 2 — Lectionary Engine | ✅ Done | Liturgical calendar, normalizer, loader, resolver, `/api/office/{date}` |
| 3 — Bible Database | ✅ Done | KJVA SQLite, reference parser, `/api/bible`, `/api/psalms`, verse text in office API |
| 4 — Frontend | Pending | HTMX templates, readable office in browser |
| 5 — Habits | Pending | Habit log, 30-day grid |
| 6 — Android | Pending | WebView wrapper APK |
| 7 — Polish | Ongoing | Holy day interrupt logic, error pages, edge cases |

## Data

| Source | Location | License |
|---|---|---|
| BCP 1979 Lectionary JSON | `backend/data/readings/` | MIT (Reuben Lillie) |
| BCP 1979 Collects | `backend/data/collects/` | Scraped from bcponline.org |
| KJVA Bible | `backend/data/web.sqlite` | Public domain (not committed — acquire separately) |

## Android (Phase 6)

```bash
adb reverse tcp:8000 tcp:8000
```

Install the APK from `android/` and open the app on the device.
