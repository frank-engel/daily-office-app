# Anglican Daily Office App

A personal liturgical practice app serving the **BCP 1979 Daily Office** (Morning Prayer,
Evening Prayer, Noonday, Compline) for any calendar date. Provides accurate lectionary and
psalm assignments, full Bible text, collects, complete service texts, and a minimal habit log.

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

Open `http://localhost:8000` — the browser UI is live.  
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

103 tests across 5 test files (calendar, lectionary, reference parser, psalm tokens, Bible DB).
Bible DB tests are skipped automatically when `web.sqlite` is absent, so CI works without it.

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

**Browser UI:**

| URL | Description |
|---|---|
| `GET /` | Home page — link to today's office |
| `GET /office/{YYYY-MM-DD}` | Daily Office page — Morning/Evening Prayer tabs with readings |
| `GET /full/{YYYY-MM-DD}` | Full Office page — complete rendered Morning/Evening Prayer service |
| `GET /habits` | Habit log — 30-day morning/evening completion grid |

**JSON API:**

| Endpoint | Description |
|---|---|
| `GET /api/office/{YYYY-MM-DD}` | Complete Daily Office — lectionary, psalms, verse text, collect |
| `GET /api/office/{YYYY-MM-DD}/full` | Full ordered service blocks (canticles, versicles, fixed texts) |
| `GET /api/bible/{reference}` | Verse text for any BCP reference string |
| `GET /api/psalms/{n[,n,...]}` | Full text of one or more psalms |
| `GET /api/habits` | List morning/evening completions for a date range |
| `POST /api/habits/{YYYY-MM-DD}/{office}` | Mark an office (morning/evening) complete |
| `DELETE /api/habits/{YYYY-MM-DD}/{office}` | Unmark an office completion |
| `GET /health` | Server health check |

## Build Phases

| Phase | Status | Scope |
|---|---|---|
| 1 — Foundation | ✅ Done | Directory layout, `pyproject.toml`, Easter algorithm, 23 calendar tests |
| 2 — Lectionary Engine | ✅ Done | Liturgical calendar, normalizer, loader, resolver, `/api/office/{date}` |
| 3 — Bible Database | ✅ Done | KJVA SQLite, reference parser, `/api/bible`, `/api/psalms`, verse text in office API |
| 4 — Frontend | ✅ Done | Jinja2/HTMX templates, readable office in browser, prev/next date nav |
| 5 — Habits | ✅ Done | Habit log SQLite, CRUD API, 30-day completion grid |
| 6 — Collects | ✅ Done | Collect of the Day resolver, traditional/contemporary toggle |
| 7 — Android | ✅ Done | WebView wrapper APK, `adb reverse tcp:8000 tcp:8000` |
| 8 — Full Office Text | ✅ Done | Canticles, versicles, opening sentences, suffrages, `/api/office/{date}/full` |
| 9 — Polish | ✅ Done | Holy day interrupt logic, global error pages, edge case fixes |

## Data

| Source | Location | License |
|---|---|---|
| BCP 1979 Lectionary JSON | `backend/data/readings/` | MIT (Reuben Lillie) |
| BCP 1979 Collects | `backend/data/collects/` | Scraped from bcponline.org |
| BCP 1979 Office Texts | `backend/data/office/` | Encoded from BCP 1979 (public domain) |
| KJVA Bible | `backend/data/web.sqlite` | Public domain (not committed — acquire separately) |

## Android

```bash
adb reverse tcp:8000 tcp:8000
```

Install the APK from `android/` and open the app on the device. The WebView shell points at
`http://localhost:8000` and the port forwarding makes that resolve to your development machine.
