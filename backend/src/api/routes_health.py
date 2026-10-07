"""GET /health - uptime check with dependency verification."""

from fastapi import APIRouter, HTTPException
from src.database import get_db
from src.config import get_settings

router = APIRouter()


@router.get("/health")
def health_check():
    """Basic health check - returns ok if service is running."""
    return {"status": "ok", "service": "global-learning-hub"}


@router.get("/health/detailed")
def detailed_health_check():
    """Detailed health check including database connectivity."""
    checks = {"service": "ok", "database": "unknown", "config": "unknown"}
    
    # Check database
    try:
        db = get_db()
        db.table("students").select("id").limit(1).execute()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"failed: {str(e)}"
    
    # Check config
    try:
        settings = get_settings()
        if settings.supabase_url and settings.supabase_key:
            checks["config"] = "ok"
        else:
            checks["config"] = "missing_required_settings"
    except Exception as e:
        checks["config"] = f"failed: {str(e)}"
    
    # Overall status
    all_ok = all(v == "ok" for v in checks.values())
    if not all_ok:
        raise HTTPException(status_code=503, detail=checks)
    
    return checks
