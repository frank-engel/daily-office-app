import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.bible.db import startup_check
from app.collects.loader import load_collects
from app.lectionary.loader import load_lectionary
from app.api.bible import router as bible_router
from app.api.habits import router as habits_router
from app.api.office import router as office_router, build_office_context
from app.api.psalms import router as psalms_router
from app.habits.db import get_completions, init_db, is_complete, mark_complete, unmark

app = FastAPI(
    title="Anglican Daily Office API",
    version="0.3.0",
    description="""
## Anglican Daily Office — BCP 1979

A personal liturgical practice API serving the **Book of Common Prayer 1979**
Daily Office (Morning Prayer, Evening Prayer, Noonday, Compline) for any
calendar date.

### Features

- **Lectionary engine** — accurate readings and psalm assignments for every
  season: Advent, Christmas, Epiphany, Lent, Holy Week, Easter, Pentecost,
  Trinity, and the Season after Pentecost (Propers 1–29)
- **Bible text** — full verse text from the King James Version with Apocrypha
  (KJVA), including all Deuterocanonical books required by the Anglican lectionary
- **Calendar math** — Easter computed via the Gregorian Computus algorithm;
  all moveable feasts derived from it; Advent and Proper Sundays calculated per
  BCP rubrics
- **Habit log** *(Phase 5)* — persistent morning/evening completion tracking

### Data sources

| Dataset | Location | License |
|---------|----------|---------|
| BCP 1979 lectionary JSON | `data/readings/` | MIT (Reuben Lillie) |
| BCP 1979 collects | `data/collects/` | Scraped from bcponline.org |
| KJVA Bible | `data/web.sqlite` | Public domain (not in repo — see setup) |

### Notes

- All date parameters use **ISO 8601** format: `YYYY-MM-DD`
- Bible reference range separators are Unicode **en-dash** (U+2013), not ASCII hyphen
- The `reflection` field is always `null` in the MVP; reserved for a future Claude AI integration
""",
    contact={"name": "Frank L Engel"},
    license_info={"name": "MIT"},
)

TEMPLATES = Jinja2Templates(directory=Path(__file__).parent / "app" / "templates")


@app.on_event("startup")
async def startup() -> None:
    load_lectionary()
    load_collects()
    await startup_check()
    await init_db()


app.include_router(office_router)
app.include_router(bible_router)
app.include_router(psalms_router)
app.include_router(habits_router)


# ── HTML routes ──────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False, response_class=HTMLResponse)
async def index(request: Request):
    today = datetime.date.today().isoformat()
    return TEMPLATES.TemplateResponse(request, "index.html", {"today": today})


@app.get("/office/{office_date}", include_in_schema=False, response_class=HTMLResponse)
async def office_html(request: Request, office_date: str):
    try:
        d = datetime.date.fromisoformat(office_date)
    except ValueError:
        return TEMPLATES.TemplateResponse(
            request,
            "office.html",
            {
                "error": f"Invalid date: {office_date!r}. Use YYYY-MM-DD.",
                "date": office_date,
                "formatted_date": office_date,
                "prev_date": None,
                "next_date": None,
                "today": datetime.date.today().isoformat(),
            },
            status_code=422,
        )

    prev_date = (d - datetime.timedelta(days=1)).isoformat()
    next_date = (d + datetime.timedelta(days=1)).isoformat()
    today = datetime.date.today().isoformat()
    formatted_date = d.strftime("%A, %B %d, %Y")

    ctx = await build_office_context(office_date)
    if ctx is None:
        return TEMPLATES.TemplateResponse(
            request,
            "office.html",
            {
                "error": f"No lectionary entry found for {office_date}.",
                "date": office_date,
                "formatted_date": formatted_date,
                "prev_date": prev_date,
                "next_date": next_date,
                "today": today,
            },
            status_code=404,
        )

    morning_complete = await is_complete(office_date, "morning")
    evening_complete = await is_complete(office_date, "evening")

    return TEMPLATES.TemplateResponse(
        request,
        "office.html",
        {
            "tab": "morning",
            "formatted_date": formatted_date,
            "prev_date": prev_date,
            "next_date": next_date,
            "today": today,
            "morning_complete": morning_complete,
            "evening_complete": evening_complete,
            **ctx,
        },
    )


@app.get("/partials/office/{office_date}/{tab}", include_in_schema=False, response_class=HTMLResponse)
async def office_tab_partial(request: Request, office_date: str, tab: str):
    if tab not in ("morning", "evening"):
        return HTMLResponse(content="<p>Invalid tab.</p>", status_code=400)
    ctx = await build_office_context(office_date)
    if ctx is None:
        return HTMLResponse(
            content=f'<p class="text-red-600 p-4">No office data for {office_date}.</p>',
            status_code=404,
        )
    morning_complete = await is_complete(office_date, "morning")
    evening_complete = await is_complete(office_date, "evening")
    return TEMPLATES.TemplateResponse(
        request,
        "_office_tab.html",
        {
            "tab": tab,
            "morning_complete": morning_complete,
            "evening_complete": evening_complete,
            **ctx,
        },
    )


@app.post("/partials/habits/{date}/{office}/toggle", include_in_schema=False, response_class=HTMLResponse)
async def habit_toggle(request: Request, date: str, office: str, style: str = "pill"):
    if office not in ("morning", "evening"):
        return HTMLResponse("<p>Invalid office.</p>", status_code=400)
    currently_complete = await is_complete(date, office)
    if currently_complete:
        await unmark(date, office)
        new_complete = False
    else:
        await mark_complete(date, office)
        new_complete = True
    return TEMPLATES.TemplateResponse(
        request,
        "_habit_toggle.html",
        {"date": date, "office": office, "complete": new_complete, "style": style},
    )


# ── Habits page ──────────────────────────────────────────────────────────────

@app.get("/habits", include_in_schema=False, response_class=HTMLResponse)
async def habits_html(request: Request):
    today = datetime.date.today()
    from_date = (today - datetime.timedelta(days=29)).isoformat()
    to_date = today.isoformat()

    completions = await get_completions(from_date, to_date)
    completed_set = {(c["date"], c["office"]) for c in completions}

    days = []
    for i in range(29, -1, -1):
        d = today - datetime.timedelta(days=i)
        iso = d.isoformat()
        days.append({
            "date": iso,
            "formatted": d.strftime("%a %b %d"),
            "is_today": d == today,
            "morning_complete": (iso, "morning") in completed_set,
            "evening_complete": (iso, "evening") in completed_set,
        })

    return TEMPLATES.TemplateResponse(
        request,
        "habits.html",
        {"days": days, "today": today.isoformat()},
    )


# ── Meta ─────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["meta"], summary="Health check")
async def health():
    """Returns `{"status": "ok"}` when the server is running."""
    return {"status": "ok"}
