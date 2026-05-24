from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Daily Office")

TEMPLATES = Jinja2Templates(directory=Path(__file__).parent / "app" / "templates")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Daily Office API — Phase 1"}


@app.get("/health")
async def health():
    return {"status": "ok"}
