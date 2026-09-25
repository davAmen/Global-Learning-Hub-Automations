"""POST /webhooks/{channel} - receives delivery-status callbacks."""

from fastapi import APIRouter, HTTPException

router = APIRouter()
@router.post("/webhooks/{channel}")
def handle_webhook(channel: str, payload: dict):
    # A provider message id is not a local reminder_log id. Provider-specific
    # signatures and id mapping must be implemented before callbacks can write.
    raise HTTPException(status_code=501, detail="Verified delivery callbacks are not configured")
