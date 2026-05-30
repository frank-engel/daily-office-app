"""Auth HTML routes: /login, /logout, /register, /profile, and preference partials."""

import datetime
import os
from collections import defaultdict
from pathlib import Path
from threading import Lock

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.db import (
    User,
    create_user,
    get_user_by_email,
    get_user_by_id,
    set_user_password,
    update_preferences,
    verify_password,
)
from app.auth.deps import get_current_user
from app.auth.tokens import create_invite_token, verify_invite_token

router = APIRouter(include_in_schema=False)
_TEMPLATES = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

COMMON_TIMEZONES = [
    ("UTC", "UTC"),
    ("America/New_York", "Eastern Time (US & Canada)"),
    ("America/Chicago", "Central Time (US & Canada)"),
    ("America/Denver", "Mountain Time (US & Canada)"),
    ("America/Los_Angeles", "Pacific Time (US & Canada)"),
    ("America/Anchorage", "Alaska"),
    ("Pacific/Honolulu", "Hawaii"),
    ("Europe/London", "London"),
    ("Europe/Paris", "Paris"),
    ("Europe/Berlin", "Berlin"),
    ("Asia/Tokyo", "Tokyo"),
    ("Asia/Shanghai", "Beijing / Shanghai"),
    ("Asia/Kolkata", "New Delhi"),
    ("Australia/Sydney", "Sydney"),
    ("Pacific/Auckland", "Auckland"),
]

_VALID_TZ = {tz for tz, _ in COMMON_TIMEZONES}

# In-memory failed-login rate limiter (resets on restart; WAF handles sustained attacks).
_failed: dict[str, list[datetime.datetime]] = defaultdict(list)
_lock = Lock()
_MAX_FAILURES = 10
_LOCKOUT_MINUTES = 15


def _is_rate_limited(ip: str) -> bool:
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=_LOCKOUT_MINUTES)
    with _lock:
        _failed[ip] = [t for t in _failed[ip] if t > cutoff]
        return len(_failed[ip]) >= _MAX_FAILURES


def _record_failure(ip: str) -> None:
    with _lock:
        _failed[ip].append(datetime.datetime.now(datetime.timezone.utc))


def _clear_failures(ip: str) -> None:
    with _lock:
        _failed.pop(ip, None)


def _safe_redirect(url: str | None) -> str:
    """Allow only same-origin relative paths to prevent open redirect."""
    if url and url.startswith("/") and not url.startswith("//"):
        return url
    return "/"


# ── Login ─────────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request, next: str = "/"):
    if await get_current_user(request):
        return RedirectResponse("/", status_code=303)
    return _TEMPLATES.TemplateResponse(request, "login.html", {"next": next, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
):
    ip = request.client.host if request.client else "unknown"
    if _is_rate_limited(ip):
        return _TEMPLATES.TemplateResponse(
            request,
            "login.html",
            {"next": next, "error": "Too many failed attempts. Please wait 15 minutes."},
            status_code=429,
        )

    result = await get_user_by_email(email)
    if result is None:
        _record_failure(ip)
        return _TEMPLATES.TemplateResponse(
            request,
            "login.html",
            {"next": next, "error": "Invalid email or password."},
            status_code=401,
        )

    user, password_hash = result

    # Invited user — password not yet set; send them to the set-password flow.
    if password_hash is None:
        token = create_invite_token(user.id)
        return RedirectResponse(f"/set-password?token={token}", status_code=303)

    if not verify_password(password, password_hash):
        _record_failure(ip)
        return _TEMPLATES.TemplateResponse(
            request,
            "login.html",
            {"next": next, "error": "Invalid email or password."},
            status_code=401,
        )

    _clear_failures(ip)
    request.session["user_id"] = user.id
    return RedirectResponse(_safe_redirect(next), status_code=303)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# ── Register ──────────────────────────────────────────────────────────────────

@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    enabled = os.getenv("REGISTRATION_ENABLED", "false").lower() == "true"
    return _TEMPLATES.TemplateResponse(
        request, "register.html", {"disabled": not enabled, "error": None}
    )


@router.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    email: str = Form(...),
    display_name: str = Form(""),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    enabled = os.getenv("REGISTRATION_ENABLED", "false").lower() == "true"
    if not enabled:
        return _TEMPLATES.TemplateResponse(
            request, "register.html", {"disabled": True, "error": "Registration is currently closed."}
        )

    # ALLOWED_EMAILS allowlist: when set, only those addresses may self-register.
    allowed_raw = os.getenv("ALLOWED_EMAILS", "").strip()
    if allowed_raw:
        allowed = {e.strip().lower() for e in allowed_raw.split(",") if e.strip()}
        if email.lower().strip() not in allowed:
            return _TEMPLATES.TemplateResponse(
                request, "register.html",
                {"disabled": False, "error": "Registration is not open for that email address."}
            )

    if password != password_confirm:
        return _TEMPLATES.TemplateResponse(
            request, "register.html", {"disabled": False, "error": "Passwords do not match."}
        )
    if len(password) < 8:
        return _TEMPLATES.TemplateResponse(
            request, "register.html", {"disabled": False, "error": "Password must be at least 8 characters."}
        )
    if await get_user_by_email(email) is not None:
        return _TEMPLATES.TemplateResponse(
            request, "register.html", {"disabled": False, "error": "An account with that email already exists."}
        )

    user = await create_user(
        email=email,
        password=password,
        display_name=display_name.strip() or None,
    )
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/profile", response_class=HTMLResponse)
async def profile_get(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse("/login?next=/profile", status_code=303)
    return _TEMPLATES.TemplateResponse(
        request,
        "profile.html",
        {"user": user, "timezones": COMMON_TIMEZONES, "saved": False, "error": None},
    )


@router.post("/profile", response_class=HTMLResponse)
async def profile_post(
    request: Request,
    display_name: str = Form(""),
    timezone: str = Form("UTC"),
    collect_style: str = Form("contemporary"),
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse("/login?next=/profile", status_code=303)

    if timezone not in _VALID_TZ:
        timezone = "UTC"
    if collect_style not in ("contemporary", "traditional"):
        collect_style = "contemporary"

    await update_preferences(
        user_id=user.id,
        timezone=timezone,
        collect_style=collect_style,
        display_name=display_name.strip() or None,
    )
    user = await get_user_by_id(user.id)
    return _TEMPLATES.TemplateResponse(
        request,
        "profile.html",
        {"user": user, "timezones": COMMON_TIMEZONES, "saved": True, "error": None},
    )


# ── Preferences partial (HTMX collect-style toggle) ───────────────────────────

# ── Set password (first-login invite flow) ────────────────────────────────────

@router.get("/set-password", response_class=HTMLResponse)
async def set_password_get(request: Request, token: str = ""):
    user_id = verify_invite_token(token)
    if not user_id:
        return _TEMPLATES.TemplateResponse(
            request,
            "set_password.html",
            {"token": "", "error": "This link is invalid or has expired. Please ask for a new invite.", "expired": True},
        )
    user = await get_user_by_id(user_id)
    if user is None:
        return _TEMPLATES.TemplateResponse(
            request, "set_password.html",
            {"token": "", "error": "Account not found.", "expired": True},
        )
    return _TEMPLATES.TemplateResponse(
        request, "set_password.html", {"token": token, "email": user.email, "error": None, "expired": False}
    )


@router.post("/set-password", response_class=HTMLResponse)
async def set_password_post(
    request: Request,
    token: str = Form(""),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    user_id = verify_invite_token(token)
    if not user_id:
        return _TEMPLATES.TemplateResponse(
            request, "set_password.html",
            {"token": "", "error": "This link is invalid or has expired. Please ask for a new invite.", "expired": True},
        )
    if password != password_confirm:
        user = await get_user_by_id(user_id)
        return _TEMPLATES.TemplateResponse(
            request, "set_password.html",
            {"token": token, "email": user.email if user else "", "error": "Passwords do not match.", "expired": False},
        )
    if len(password) < 8:
        user = await get_user_by_id(user_id)
        return _TEMPLATES.TemplateResponse(
            request, "set_password.html",
            {"token": token, "email": user.email if user else "", "error": "Password must be at least 8 characters.", "expired": False},
        )

    await set_user_password(user_id, password)
    request.session["user_id"] = user_id
    return RedirectResponse("/", status_code=303)


# ── Preferences partial (HTMX collect-style toggle) ───────────────────────────

@router.post("/partials/preferences/collect-style", response_class=HTMLResponse)
async def save_collect_style(request: Request, value: str = Form("contemporary")):
    """Called by HTMX on collect-style toggle; persists the preference silently."""
    user = await get_current_user(request)
    if user is None:
        return HTMLResponse("", status_code=401)
    if value not in ("contemporary", "traditional"):
        value = "contemporary"
    await update_preferences(
        user_id=user.id,
        timezone=user.timezone,
        collect_style=value,
        display_name=user.display_name,
    )
    return HTMLResponse("", status_code=200)
