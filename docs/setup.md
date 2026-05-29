# Setup and Installation

## Requirements

- Python 3.11 or later
- PowerShell (Windows) or bash (macOS/Linux)
- Git

## 1. Clone and create the virtual environment

```powershell
git clone https://github.com/your-org/daily-office-app.git
cd daily-office-app

python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate         # macOS / Linux
```

## 2. Install dependencies

```powershell
cd backend
pip install -e ".[dev]"
```

The `[dev]` extra installs pytest, pytest-asyncio, and httpx for running tests.

## 3. Acquire the Bible database

The KJVA (King James Version with Apocrypha) SQLite file is **not committed** to this
repository because it is a 5 MB binary asset. Acquire it once from
[scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases):

```powershell
# Sparse-clone — only downloads the one file you need (~5 MB transfer)
git clone --depth 1 --filter=blob:none --sparse `
    https://github.com/scrollmapper/bible_databases.git bible_dbs

Set-Location bible_dbs
git sparse-checkout set --skip-checks formats/sqlite/KJVA.db
git checkout

Copy-Item formats/sqlite/KJVA.db ..\daily-office-app\backend\data\web.sqlite
Set-Location ..
Remove-Item -Recurse -Force bible_dbs
```

The file must be placed at `backend/data/web.sqlite`. The server logs a startup warning
for any missing Apocryphal books but will never crash — missing verses return the sentinel
string `"[Text not available in this edition]"`.

> **Why KJVA?** The BCP 1979 lectionary assigns Deuterocanonical readings (Sirach, Wisdom,
> Tobit, Judith, Baruch, 1–2 Maccabees, 1–2 Esdras). KJVA is the only widely-available
> public-domain English translation that covers these books in a single SQLite file.

## 4. Start the server

```powershell
# From the project root (where .venv lives)
.\.venv\Scripts\Activate.ps1

cd backend
uvicorn main:app --reload
```

| URL | What you see |
|---|---|
| `http://localhost:8000/` | Home page — "Open Today's Office" button |
| `http://localhost:8000/office/YYYY-MM-DD` | Daily Office with Morning/Evening Prayer tabs |
| `http://localhost:8000/full/YYYY-MM-DD` | Full rendered Morning/Evening Prayer service |
| `http://localhost:8000/habits` | 30-day habit completion grid |
| `http://localhost:8000/docs` | Swagger UI — interactive JSON API explorer |
| `http://localhost:8000/redoc` | ReDoc — alternative API documentation |

### Manual testing checklist

1. Open `http://localhost:8000/` — home page loads with today's date.
2. Click **Open Today's Office** — office page loads with liturgical title, season, and year cycle.
3. The Collect of the Day appears with Contemporary/Traditional toggle.
4. Morning Prayer tab is active by default; psalms and lessons render with verse text.
5. Click **Evening Prayer** — content swaps via HTMX without a page reload.
6. Click **‹ Prev** and **Next ›** — navigates to adjacent days correctly.
7. Click **Full Service** — renders the complete ordered Morning Prayer service with canticles, versicles, and all fixed texts.
8. Visit `http://localhost:8000/habits` — 30-day grid shows morning/evening toggles.
9. Visit a known feast day, e.g. `http://localhost:8000/office/2026-11-30` (St. Andrew's Day 2026) — title shows *Saint Andrew the Apostle*, not the ordinary Advent weekday.
10. Visit `http://localhost:8000/office/2026-04-05` (Easter Sunday 2026) — title shows *Easter Day*.
11. Visit `http://localhost:8000/office/2024-12-01` (First Sunday of Advent 2024) — season shows *Advent*, Year One.
12. Visit a non-existent URL, e.g. `http://localhost:8000/nothing` — styled 404 page appears.

## 5. Run tests

```powershell
cd backend
pytest tests/ -v
```

103 tests across 5 files. Bible DB integration tests (`test_bible_db.py`) are automatically
skipped when `web.sqlite` is absent, so CI passes without the database file.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `BIBLE_DB_PATH` | `data/web.sqlite` | Path to the KJVA SQLite file |
| `HABITS_DB_PATH` | `data/habits.sqlite` | Path to the habits log database |

Copy `backend/.env.example` to `backend/.env` and edit as needed. Neither variable is
required for the default layout.

## Security notes

- `backend/data/*.sqlite` is gitignored — the database files are never committed.
- `.env` is gitignored — only `.env.example` (with no real values) is tracked.
- There are no API keys or external service credentials in the MVP.

## Android

Once the APK is installed from `android/`, forward the server port over USB:

```bash
adb reverse tcp:8000 tcp:8000
```

The Android WebView points at `http://localhost:8000` and the forwarding makes that
resolve to your development machine. The app does not require an internet connection
once the server is running locally.
