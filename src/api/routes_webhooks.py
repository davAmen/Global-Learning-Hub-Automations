"""POST /webhooks/{channel} - receives delivery-status callbacks."""

from fastapi import APIRouter
from src.database import get_db
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/webhooks/{channel}")
def handle_webhook(channel: str, payload: dict):
    db = get_db()
    message_id = payload.get("message_id")
    status = payload.get("status")
    if message_id and status:
        db.table("reminder_log").update({"delivery_status": status}).eq("id", message_id).execute()
        logger.info(f"Webhook: {channel} message {message_id} -> {status}")
    return {"status": "ok"}
