from fastapi import APIRouter, Depends, HTTPException

from database import db
from models import CreateUserRequest, UpdateUserRequest, new_id, now_iso
from auth import get_current_admin, hash_password, public_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
async def list_users(admin: dict = Depends(get_current_admin)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(1000)
    return users


@router.post("")
async def create_user(payload: CreateUserRequest, admin: dict = Depends(get_current_admin)):
    email = payload.email.lower().strip()
    if payload.role not in ("staff", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'staff' or 'admin'")
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="An account with this email already exists")
    user = {
        "id": new_id(),
        "email": email,
        "name": payload.name.strip(),
        "role": payload.role,
        "auth_provider": "local",
        "picture": None,
        "password_hash": hash_password(payload.password),
        "created_at": now_iso(),
    }
    await db.users.insert_one(user)
    return public_user(user)


@router.put("/{user_id}")
async def update_user(user_id: str, payload: UpdateUserRequest, admin: dict = Depends(get_current_admin)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updates = {}
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.role is not None:
        if payload.role not in ("staff", "admin"):
            raise HTTPException(status_code=400, detail="Role must be 'staff' or 'admin'")
        if user_id == admin["id"] and payload.role != "admin":
            raise HTTPException(status_code=400, detail="You cannot change your own administrator role")
        updates["role"] = payload.role
    if payload.password:
        updates["password_hash"] = hash_password(payload.password)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    await db.users.update_one({"id": user_id}, {"$set": updates})
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    return updated


@router.delete("/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_current_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True}
