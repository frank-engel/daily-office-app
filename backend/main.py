from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from app.lectionary.loader import load_lectionary
from app.api.office import router as office_router

app = FastAPI(title="Daily Office")

TEMPLATES = Jinja2Templates(directory=Path(__file__).parent / "app" / "templates")


@app.on_event("startup")
async def startup() -> None:
    load_lectionary()


app.include_router(office_router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Daily Office API — Phase 2"}


@app.get("/health")
async def health():
    return {"status": "ok"}
