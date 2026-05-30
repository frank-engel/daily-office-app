"""Signed invite tokens for the first-login set-password flow."""

import os

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

_SALT = "set-password-invite"
_DEFAULT_MAX_AGE_HOURS = 48


def _serializer() -> URLSafeTimedSerializer:
    secret = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    return URLSafeTimedSerializer(secret, salt=_SALT)


def create_invite_token(user_id: str) -> str:
    return _serializer().dumps(user_id)


def verify_invite_token(token: str, max_age_hours: int = _DEFAULT_MAX_AGE_HOURS) -> str | None:
    """Return the user_id encoded in the token, or None if invalid/expired."""
    try:
        return _serializer().loads(token, max_age=max_age_hours * 3600)
    except (BadSignature, SignatureExpired):
        return None
