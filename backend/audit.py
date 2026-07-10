from fastapi import APIRouter, Depends, Query
from typing import Optional

from database import db
from models import new_id, now_iso
from auth import get_current_user

router = APIRouter(prefix="/api/audit", tags=["audit"])

PROJ = {"_id": 0}


async def log_event(action: str, visitor: dict, officer: dict, details: str = ""):
    """Record a check-in / check-out (or related) event in the audit log."""
    await db.audit_log.insert_one({
        "id": new_id(),
        "action": action,  # check_in | check_out | updated | deleted
        "visitor_id": visitor.get("id"),
        "visitor_name": visitor.get("visitor_name"),
        "department": visitor.get("department"),
        "whom_to_see": visitor.get("whom_to_see"),
        "officer_id": officer.get("id"),
        "officer_name": officer.get("name"),
        "details": details,
        "timestamp": now_iso(),
    })


@router.get("")
async def list_audit(
    user: dict = Depends(get_current_user),
    action: Optional[str] = None,
    visitor_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(300, le=1000),
):
    q = {}
    if action and action != "all":
        q["action"] = action
    if visitor_id:
        q["visitor_id"] = visitor_id
    if search:
        rx = {"$regex": search, "$options": "i"}
        q["$or"] = [{"visitor_name": rx}, {"officer_name": rx}]
    items = await db.audit_log.find(q, PROJ).sort("timestamp", -1).to_list(limit)
    return items
