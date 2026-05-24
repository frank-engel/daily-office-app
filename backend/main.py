from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from app.bible.db import startup_check
from app.lectionary.loader import load_lectionary
from app.api.bible import router as bible_router
from app.api.office import router as office_router
from app.api.psalms import router as psalms_router

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
    await startup_check()


app.include_router(office_router)
app.include_router(bible_router)
app.include_router(psalms_router)


@app.get("/", include_in_schema=False)
async def root():
    return {"status": "ok", "message": "Anglican Daily Office API v0.3.0"}


@app.get("/health", tags=["meta"], summary="Health check")
async def health():
    """Returns `{"status": "ok"}` when the server is running."""
    return {"status": "ok"}
