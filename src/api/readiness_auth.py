"""Authentication and role checks for Phase 2 notice-recording routes."""

import logging
from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.database import get_db

logger = logging.getLogger(__name__)
bearer_auth = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class ReadinessActor:
    """Identity and role loaded from a verified Supabase Auth account."""

    user_id: UUID
    role: Literal["staff", "learner"]
    student_id: UUID | None = None


def get_readiness_db(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_auth),
) -> Any:
    """Return the server database client only after a bearer token is present."""
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Sign-in required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return get_db()
    except Exception:
        logger.error("Supabase database client is unavailable for readiness API.")
        raise HTTPException(status_code=503, detail="Readiness service unavailable") from None


def get_readiness_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_auth),
    db: Any = Depends(get_readiness_db),
) -> ReadinessActor:
    """Validate a user's token and load their trusted server-managed profile."""
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Sign-in required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        auth_response = db.auth_get_user(credentials.credentials)
    except Exception as exc:
        if getattr(exc, "status", None) == 401:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired sign-in",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None
        logger.error("Supabase Auth could not validate a readiness API token.")
        raise HTTPException(status_code=503, detail="Readiness service unavailable") from None

    user = getattr(auth_response, "user", None)
    try:
        user_id = UUID(str(user.id))
    except (AttributeError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired sign-in",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    try:
        response = (
            db.table("app_user_profiles")
            .select("role, student_id")
            .eq("auth_user_id", str(user_id))
            .limit(1)
            .execute()
        )
    except Exception:
        logger.error("Could not load a readiness API profile.")
        raise HTTPException(status_code=503, detail="Readiness service unavailable") from None

    rows = getattr(response, "data", None)
    profile = rows[0] if isinstance(rows, list) and len(rows) == 1 else None
    if not isinstance(profile, dict):
        raise HTTPException(status_code=403, detail="No readiness access profile")

    role = profile.get("role")
    if role == "staff" and profile.get("student_id") is None:
        return ReadinessActor(user_id=user_id, role="staff")
    if role == "learner":
        try:
            student_id = UUID(str(profile.get("student_id")))
        except (TypeError, ValueError):
            raise HTTPException(status_code=403, detail="Invalid readiness access profile") from None
        return ReadinessActor(user_id=user_id, role="learner", student_id=student_id)
    raise HTTPException(status_code=403, detail="Invalid readiness access profile")


def require_readiness_staff(
    actor: ReadinessActor = Depends(get_readiness_actor),
) -> ReadinessActor:
    """Require a trusted staff profile for administrator-only actions."""
    if actor.role != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    return actor


def require_readiness_learner(
    actor: ReadinessActor = Depends(get_readiness_actor),
) -> ReadinessActor:
    """Require a trusted learner profile for self-service actions."""
    if actor.role != "learner" or actor.student_id is None:
        raise HTTPException(status_code=403, detail="Learner access required")
    return actor
