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
cd backend
uvicorn main:app --reload
```

The API is available at `http://localhost:8000`.  
Interactive docs (Swagger UI): `http://localhost:8000/docs`  
Alternative docs (ReDoc): `http://localhost:8000/redoc`

## 5. Run tests

```powershell
cd backend
pytest tests/ -v
```

Bible DB integration tests (`test_bible_db.py`) are automatically skipped when
`web.sqlite` is absent, so CI passes without the database file.

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

## Android (Phase 6)

Once the APK is installed, forward the server port over USB:

```bash
adb reverse tcp:8000 tcp:8000
```

The Android WebView points at `http://localhost:8000` and the forwarding makes that
resolve to your development machine.
