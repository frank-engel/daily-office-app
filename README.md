# Anglican Daily Office App

A personal liturgical practice app serving the BCP 1979 Daily Office (Morning Prayer, Evening Prayer, Noonday, Compline) for any calendar date. Provides accurate lectionary and psalm assignments, full Bible text, and a minimal habit log.

## Stack

- **Backend:** Python FastAPI + Jinja2/HTMX
- **Frontend:** Tailwind CSS + HTMX (CDN, no build step)
- **Database:** SQLite (`web.sqlite` for Bible verses, `habits.sqlite` for habit log)
- **Mobile:** Android WebView wrapper via `adb reverse`

## Setup

```powershell
# Create and activate virtualenv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
cd backend
pip install -e ".[dev]"
```

### Bible database

The WEB Bible SQLite file is not committed. Obtain it from [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases):

```bash
git clone https://github.com/scrollmapper/bible_databases
cp bible_databases/sqlite/web.db backend/data/web.sqlite
```

## Running

```powershell
# From project root, with venv active
cd backend
uvicorn main:app --reload
```

Open `http://localhost:8000` in a browser.

### Android (Phase 6)

```bash
adb reverse tcp:8000 tcp:8000
```

Install the APK from `android/` and open the app on the device.

## Tests

```powershell
cd backend
pytest tests/
```

## Build Phases

| Phase | Status | Scope |
|---|---|---|
| 1 — Foundation | ✅ Done | Directory layout, `pyproject.toml`, Easter algorithm, 23 calendar tests |
| 2 — Lectionary Engine | ✅ Done | Liturgical calendar, normalizer, loader, resolver, `/api/office/{date}` |
| 3 — Bible Database | Pending | `web.sqlite` integration, `/api/bible`, `/api/psalms`, verse text in office |
| 4 — Frontend | Pending | HTMX templates, readable office in browser |
| 5 — Habits | Pending | Habit log, 30-day grid |
| 6 — Android | Pending | WebView wrapper APK |
| 7 — Polish | Ongoing | Holy day interrupt logic, error pages, edge cases |

## Data

| Source | Location | License |
|---|---|---|
| BCP 1979 Lectionary JSON | `backend/data/readings/` | MIT (Reuben Lillie) |
| BCP 1979 Collects | `backend/data/collects/` | Scraped from bcponline.org |
| WEB Bible | `backend/data/web.sqlite` | Public domain (not committed) |
