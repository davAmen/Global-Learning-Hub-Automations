"""GET /groups - list groups, POST /groups - create group record."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from src.database import get_db

router = APIRouter()


class GroupCreate(BaseModel):
    whatsapp_jid: str
    name: str
    type: str  # announcement | proof_submission | class_access | community
    course_id: str | None = None
    parent_community_jid: str | None = None


@router.get("/groups")
def list_groups():
    db = get_db()
    resp = db.table("groups").select("*").order("created_at", desc=True).execute()
    return {"groups": resp.data or []}


@router.post("/groups")
def create_group(group: GroupCreate):
    db = get_db()
    
    data = group.model_dump()
    data["is_active"] = True
    data["created_at"] = datetime.utcnow().isoformat()
    
    resp = db.table("groups").insert(data).execute()
    if not resp.data:
        raise HTTPException(500, "Failed to create group")
    
    return {"status": "ok", "group": resp.data[0]}


@router.post("/groups/{group_jid}/sync-participants")
def sync_group_participants(group_jid: str):
    """Sync participants from WasenderAPI to local DB (future use)."""
    import httpx
    from src.config import get_settings
    settings = get_settings()
    
    url = f"{settings.wasender_base_url}/api/groups/{group_jid}/participants"
    headers = {"Authorization": f"Bearer {settings.wasender_api_key}"}
    r = httpx.get(url, headers=headers, timeout=15)
    
    return {"status": "ok", "data": r.json()}