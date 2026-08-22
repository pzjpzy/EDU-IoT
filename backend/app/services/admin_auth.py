"""Minimal admin authentication for the /admin feedback panel.

A single shared password (config.ADMIN_PASSWORD) is exchanged for a random
bearer token held in memory; protected endpoints require that token. This is
deliberately lightweight for a single-educator lab tool - there are no user
accounts. Tokens are lost on restart (the admin just logs in again), which is
an acceptable trade for not persisting secrets.
"""
import secrets

from fastapi import Header, HTTPException

from app.config import ADMIN_PASSWORD

_valid_tokens: set[str] = set()


def login(password: str) -> str:
    if not secrets.compare_digest(password, ADMIN_PASSWORD):
        raise PermissionError("Invalid admin password")
    token = secrets.token_urlsafe(24)
    _valid_tokens.add(token)
    return token


def logout(token: str) -> None:
    _valid_tokens.discard(token)


def require_admin(authorization: str | None = Header(default=None)) -> None:
    """FastAPI dependency: 401 unless a valid 'Authorization: Bearer <token>'
    header is present."""
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token or token not in _valid_tokens:
        raise HTTPException(status_code=401, detail="Admin authentication required.")
