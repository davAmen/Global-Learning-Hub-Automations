"""Require a configured secret for operator-only API routes."""

import hmac

from fastapi import Header, HTTPException

from src.config import get_settings


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    expected = get_settings().admin_api_key
    if not expected or not x_admin_key or not hmac.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=403, detail="Operator authorization required")
