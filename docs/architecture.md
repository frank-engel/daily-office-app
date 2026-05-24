# Architecture

## Overview

The app is a single-process Python FastAPI server. There is no cloud infrastructure
in the MVP — everything runs locally and is accessed from an Android WebView over
`adb reverse`.

```
┌─────────────────────────────────────────────────────────┐
│  Android WebView  (localhost:8000 via adb reverse)      │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP
┌─────────────────────▼───────────────────────────────────┐
│  FastAPI  (uvicorn)                                     │
│                                                         │
│  Routers                                                │
│  ├─ /api/office/{date}   ─► Calendar engine             │
│  │                           Lectionary engine           │
│  │                           Bible DB                    │
│  ├─ /api/bible/{ref}     ─► Reference parser            │
│  │                           Bible DB                    │
│  ├─ /api/psalms/{n}      ─► Bible DB                    │
│  └─ /api/habits/*        ─► Habit DB  (Phase 5)         │
│                                                         │
│  Templates (Jinja2/HTMX)  (Phase 4)                     │
└──────────┬──────────────┬──────────────────────────────-┘
           │              │
    ┌──────▼──────┐  ┌────▼──────┐
    │  web.sqlite │  │habits.db  │
    │  (KJVA)     │  │(Phase 5)  │
    └─────────────┘  └───────────┘
```

## Module map

### `app/calendar/`

| Module | Responsibility |
|---|---|
| `computus.py` | Easter Sunday date — Gregorian algorithm |
| `liturgical_year.py` | Date → `{cycle, season, week, day}` context dict |

`liturgical_year.py` builds a Proper-number lookup table at import time (Proper 1–29
keyed on the nearest Sunday date) and binary-searches it at call time.

### `app/lectionary/`

| Module | Responsibility |
|---|---|
| `loader.py` | Parse JSON files into `DAILY_INDEX` and `HOLY_DAY_INDEX` at startup |
| `normalizer.py` | Fix known data-quality issues in the source JSON |
| `resolver.py` | `resolve_office(date)` — calendar context → lectionary entry |

`DAILY_INDEX` is keyed `(cycle: int, week: str, day: str)`.  
`HOLY_DAY_INDEX` is keyed on `"Dec 25"` / `"Nov 1"` etc.

### `app/bible/`

| Module | Responsibility |
|---|---|
| `book_map.py` | SBL abbreviation → KJVA `book_id` integer |
| `reference_parser.py` | Reference string → list of `VerseRange` objects |
| `db.py` | Async SQLite verse and psalm fetching |

`reference_parser.py` handles all BCP reference formats including multi-section,
cross-chapter, letter-suffixed verses, and parenthetical optionals.

### `app/api/`

FastAPI `APIRouter` modules. Each file is a thin HTTP layer — no business logic.

### `app/schemas.py`

Pydantic response models shared across all routers. These drive both Swagger UI
schema generation and runtime response validation.

## Data flow for `/api/office/{date}`

```
1. liturgical_context(date)
      → Easter math → season / week / day / cycle

2. DAILY_INDEX[(cycle, week, day)]
      → raw lectionary entry (JSON)

3. flatten_lessons(entry, "morning")
   flatten_lessons(entry, "evening")
      → {"first": "Isa 1:1–9", "second": "2 Pet 3:1–10", "gospel": "Matt 25:1–13"}

4. parse_reference("Isa 1:1–9")
      → [VerseRange(book="Isa", start_chapter=1, start_verse=1, end_chapter=1, end_verse=9)]

5. KJVA_verses WHERE book_id=23 AND chapter=1 AND verse BETWEEN 1 AND 9
      → [{book, chapter, verse, text}, ...]

6. OfficeResponse (Pydantic model) → JSON
```

## Key design decisions

**Why SQLite (not Postgres)?**  
MVP is a personal device app. SQLite is zero-config, ships in the standard library,
and handles the read-heavy Bible lookup workload without issue.

**Why aiosqlite?**  
FastAPI is async. Blocking SQLite I/O on the event loop would serialize requests.
`aiosqlite` wraps SQLite in a thread pool so async/await syntax works correctly.

**Why KJVA (not WEB)?**  
The original architecture specified the World English Bible (WEB), but the
scrollmapper database repository reorganized its layout and no longer ships a
`sqlite/web.db` file. KJVA is the only single public-domain SQLite file that covers
the full Anglican canon including Apocrypha (80 books). The code is database-agnostic
via `book_map.py`; switching translations in the future only requires updating that
file and the table name constants in `db.py`.

**Why in-memory lectionary index?**  
The JSON files are ~400 KB total and loaded once at startup. In-memory dict lookup
is O(1) and far simpler than an additional SQLite table for 810 lectionary entries.

**Why no ORM?**  
The Bible DB schema is read-only and the query patterns are simple range lookups.
Raw `aiosqlite` is less dependency surface and is faster for this access pattern.

## Future seams (post-MVP)

- `app/api/reflection.py` — `POST /api/reflection/{date}` returns HTTP 501. The
  `reflection: null` field in `OfficeResponse` is reserved for a Claude API integration.
- `user_id` in habits schema is nullable from day one — ready for Cognito post-MVP.
- `liturgical_context()` returns a rich dict (season, color, collect ref) intended as
  future Claude API system-prompt context.
