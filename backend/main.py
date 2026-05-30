import datetime
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()  # Must run before any os.getenv() calls in imported modules

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.auth.db import User, init_db as init_users_db
from app.auth.deps import get_current_user
from app.auth.routes import router as auth_router
from app.bible.db import startup_check
from app.collects.loader import load_collects
from app.lectionary.loader import load_lectionary
from app.api.bible import router as bible_router
from app.api.habits import router as habits_router
from app.api.office import router as office_router, build_office_context
from app.api.office_full import router as office_full_router
from app.api.psalms import router as psalms_router
from app.habits.db import get_completions, init_db, is_complete, mark_complete, unmark
from app.office.loader import load_office_texts

app = FastAPI(
    title="Anglican Daily Office API",
    version="0.4.0",
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
- **Habit log** *(Phase 5)* — per-user morning/evening completion tracking

### Data sources

| Dataset | Location | License |
|---------|----------|---------|
| BCP 1979 lectionary JSON | `data/readings/` | MIT (Reuben Lillie) |
| BCP 1979 collects | `data/collects/` | Scraped from bcponline.org |
| KJVA Bible | `data/web.sqlite` | Public domain (not in repo — see setup) |

### Notes

- All date parameters use **ISO 8601** format: `YYYY-MM-DD`
- Bible reference range separators are Unicode **en-dash** (U+2013), not ASCII hyphen
- The `reflection` field is always `null` in MVP; reserved for Phase 11 Claude AI integration
""",
    contact={"name": "Frank L Engel"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret-change-in-production"),
    https_only=os.getenv("HTTPS_ONLY", "false").lower() == "true",
    same_site="lax",
)

TEMPLATES = Jinja2Templates(directory=Path(__file__).parent / "app" / "templates")


def _user_today(user: User | None) -> datetime.date:
    """Return today's date in the user's timezone (UTC if no user or unknown TZ)."""
    if user is None:
        return datetime.date.today()
    try:
        return datetime.datetime.now(ZoneInfo(user.timezone)).date()
    except Exception:
        return datetime.date.today()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    if exc.status_code == 404:
        return TEMPLATES.TemplateResponse(request, "404.html", {}, status_code=404)
    return TEMPLATES.TemplateResponse(
        request, "500.html", {"detail": str(exc.detail)}, status_code=exc.status_code
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Internal server error"}, status_code=500)
    return TEMPLATES.TemplateResponse(request, "500.html", {}, status_code=500)


@app.on_event("startup")
async def startup() -> None:
    load_lectionary()
    load_collects()
    load_office_texts()
    await startup_check()
    await init_db()
    await init_users_db()


app.include_router(auth_router)
app.include_router(office_router)
app.include_router(office_full_router)
app.include_router(bible_router)
app.include_router(psalms_router)
app.include_router(habits_router)


# ── HTML routes ──────────────────────────────────────────────────────────────

async def _require_user_html(request: Request) -> User | None:
    """Check auth for HTML routes; returns None and triggers redirect on failure."""
    return await get_current_user(request)


@app.get("/", include_in_schema=False, response_class=HTMLResponse)
async def index(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    today = _user_today(user).isoformat()
    return TEMPLATES.TemplateResponse(request, "index.html", {"today": today, "user": user})


@app.get("/office/{office_date}", include_in_schema=False, response_class=HTMLResponse)
async def office_html(request: Request, office_date: str):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(f"/login?next=/office/{office_date}", status_code=303)

    try:
        d = datetime.date.fromisoformat(office_date)
    except ValueError:
        today = _user_today(user).isoformat()
        return TEMPLATES.TemplateResponse(
            request,
            "office.html",
            {
                "error": f"Invalid date: {office_date!r}. Use YYYY-MM-DD.",
                "date": office_date,
                "formatted_date": office_date,
                "prev_date": None,
                "next_date": None,
                "today": today,
                "user": user,
            },
            status_code=422,
        )

    prev_date = (d - datetime.timedelta(days=1)).isoformat()
    next_date = (d + datetime.timedelta(days=1)).isoformat()
    today = _user_today(user).isoformat()
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
                "user": user,
            },
            status_code=404,
        )

    morning_complete = await is_complete(office_date, "morning", user_id=user.id)
    evening_complete = await is_complete(office_date, "evening", user_id=user.id)

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
            "user": user,
            **ctx,
        },
    )


@app.get("/partials/office/{office_date}/{tab}", include_in_schema=False, response_class=HTMLResponse)
async def office_tab_partial(request: Request, office_date: str, tab: str):
    user = await get_current_user(request)
    if user is None:
        return HTMLResponse('<p class="text-stone-400">Session expired. Please <a href="/login" class="underline">sign in</a>.</p>', status_code=401)
    if tab not in ("morning", "evening"):
        return HTMLResponse(content="<p>Invalid tab.</p>", status_code=400)
    ctx = await build_office_context(office_date)
    if ctx is None:
        return HTMLResponse(
            content=f'<p class="text-red-600 p-4">No office data for {office_date}.</p>',
            status_code=404,
        )
    morning_complete = await is_complete(office_date, "morning", user_id=user.id)
    evening_complete = await is_complete(office_date, "evening", user_id=user.id)
    return TEMPLATES.TemplateResponse(
        request,
        "_office_tab.html",
        {
            "tab": tab,
            "morning_complete": morning_complete,
            "evening_complete": evening_complete,
            "user": user,
            **ctx,
        },
    )


@app.post("/partials/habits/{date}/{office}/toggle", include_in_schema=False, response_class=HTMLResponse)
async def habit_toggle(request: Request, date: str, office: str, style: str = "pill"):
    user = await get_current_user(request)
    if user is None:
        return HTMLResponse('<p class="text-stone-400">Session expired. Please <a href="/login" class="underline">sign in</a>.</p>', status_code=401)
    if office not in ("morning", "evening"):
        return HTMLResponse("<p>Invalid office.</p>", status_code=400)
    currently_complete = await is_complete(date, office, user_id=user.id)
    if currently_complete:
        await unmark(date, office, user_id=user.id)
        new_complete = False
    else:
        await mark_complete(date, office, user_id=user.id)
        new_complete = True
    return TEMPLATES.TemplateResponse(
        request,
        "_habit_toggle.html",
        {"date": date, "office": office, "complete": new_complete, "style": style},
    )


# ── Full Office page ─────────────────────────────────────────────────────────

@app.get("/full/{office_date}", include_in_schema=False, response_class=HTMLResponse)
async def office_full_html(request: Request, office_date: str, suffrages: str = "A"):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(f"/login?next=/full/{office_date}", status_code=303)

    try:
        d = datetime.date.fromisoformat(office_date)
    except ValueError:
        today = _user_today(user).isoformat()
        return TEMPLATES.TemplateResponse(
            request, "office_full.html",
            {"error": f"Invalid date: {office_date!r}", "date": office_date,
             "formatted_date": office_date, "prev_date": None, "next_date": None,
             "today": today, "user": user},
            status_code=422,
        )

    from app.office.builder import build_office
    from app.api.office_full import _expand_blocks

    prev_date = (d - datetime.timedelta(days=1)).isoformat()
    next_date = (d + datetime.timedelta(days=1)).isoformat()
    today = _user_today(user).isoformat()
    formatted_date = d.strftime("%A, %B %d, %Y")

    ctx = await build_office_context(office_date)
    suffrages_form = suffrages.upper() if suffrages.upper() in ("A", "B") else "A"

    morning_raw = build_office(d, "morning", suffrages_form)
    evening_raw = build_office(d, "evening", suffrages_form)
    morning_blocks = await _expand_blocks(morning_raw)
    evening_blocks = await _expand_blocks(evening_raw)

    return TEMPLATES.TemplateResponse(
        request,
        "office_full.html",
        {
            "date": office_date,
            "formatted_date": formatted_date,
            "prev_date": prev_date,
            "next_date": next_date,
            "today": today,
            "title": ctx["title"] if ctx else None,
            "week": ctx["week"] if ctx else "",
            "season": ctx["season"] if ctx else "",
            "cycle": ctx["cycle"] if ctx else "",
            "service_name": "Daily Office",
            "suffrages_form": suffrages_form,
            "morning_blocks": morning_blocks,
            "evening_blocks": evening_blocks,
            "user": user,
        },
    )


# ── Habits page ──────────────────────────────────────────────────────────────

@app.get("/habits", include_in_schema=False, response_class=HTMLResponse)
async def habits_html(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse("/login?next=/habits", status_code=303)

    today = _user_today(user)
    from_date = (today - datetime.timedelta(days=29)).isoformat()
    to_date = today.isoformat()

    completions = await get_completions(from_date, to_date, user_id=user.id)
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
        {"days": days, "today": today.isoformat(), "user": user},
    )


# ── Meta ─────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["meta"], summary="Health check")
async def health():
    """Returns `{"status": "ok"}` when the server is running."""
    return {"status": "ok"}
