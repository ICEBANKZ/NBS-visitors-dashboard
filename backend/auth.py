import os
from datetime import datetime, timezone, timedelta

import bcrypt
import jwt
import requests
from fastapi import APIRouter, Request, Response, HTTPException, Depends

from database import db
from models import (
    RegisterRequest,
    LoginRequest,
    SessionRequest,
    new_id,
    now_iso,
)

JWT_ALGORITHM = "HS256"
ACCESS_TTL_MIN = 60 * 12          # 12h
REFRESH_TTL_DAYS = 7
SESSION_TTL_DAYS = 7

EMERGENT_SESSION_URL = (
    "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------------- Password helpers ----------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


# ---------------- JWT helpers ----------------
def _secret() -> str:
    return os.environ["JWT_SECRET"]


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TTL_MIN),
    }
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TTL_DAYS),
    }
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGORITHM)


# ---------------- Cookies ----------------
def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie("access_token", access_token, httponly=True, secure=True,
                        samesite="none", max_age=ACCESS_TTL_MIN * 60, path="/")
    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True,
                        samesite="none", max_age=REFRESH_TTL_DAYS * 86400, path="/")


def clear_auth_cookies(response: Response):
    for key in ("access_token", "refresh_token", "session_token"):
        response.delete_cookie(key, path="/")


# ---------------- User serialization ----------------
def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user.get("name", ""),
        "role": user.get("role", "staff"),
        "auth_provider": user.get("auth_provider", "local"),
        "picture": user.get("picture"),
        "created_at": user.get("created_at"),
    }


async def _user_by_id(user_id: str):
    return await db.users.find_one({"id": user_id}, {"_id": 0})


async def _user_from_jwt(token: str):
    try:
        payload = jwt.decode(token, _secret(), algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    return await _user_by_id(payload.get("sub"))


async def _user_from_session(token: str):
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        return None
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and expires_at < datetime.now(timezone.utc):
        return None
    return await _user_by_id(session.get("user_id"))


# ---------------- Dependencies ----------------
async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("session_token")
    if token:
        user = await _user_from_session(token)
        if user:
            return public_user(user)

    token = request.cookies.get("access_token")
    if token:
        user = await _user_from_jwt(token)
        if user:
            return public_user(user)

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        raw = auth_header[7:]
        user = await _user_from_jwt(raw)
        if not user:
            user = await _user_from_session(raw)
        if user:
            return public_user(user)

    raise HTTPException(status_code=401, detail="Not authenticated")


async def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


# ---------------- Endpoints ----------------
@router.post("/register")
async def register(payload: RegisterRequest, response: Response):
    email = payload.email.lower().strip()
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="An account with this email already exists")
    user = {
        "id": new_id(),
        "email": email,
        "name": payload.name.strip(),
        "role": "staff",
        "auth_provider": "local",
        "picture": None,
        "password_hash": hash_password(payload.password),
        "created_at": now_iso(),
    }
    await db.users.insert_one(user)
    set_auth_cookies(response, create_access_token(user["id"], email),
                     create_refresh_token(user["id"]))
    return public_user(user)


@router.post("/login")
async def login(payload: LoginRequest, response: Response):
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    set_auth_cookies(response, create_access_token(user["id"], email),
                     create_refresh_token(user["id"]))
    return public_user(user)


@router.post("/session")
async def google_session(payload: SessionRequest, response: Response):
    try:
        resp = requests.get(
            EMERGENT_SESSION_URL,
            headers={"X-Session-ID": payload.session_id},
            timeout=10,
        )
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Auth service unavailable")
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    data = resp.json()
    email = (data.get("email") or "").lower().strip()
    if not email:
        raise HTTPException(status_code=401, detail="Invalid session data")

    user = await db.users.find_one({"email": email})
    if not user:
        user = {
            "id": new_id(),
            "email": email,
            "name": data.get("name") or email,
            "role": "staff",
            "auth_provider": "google",
            "picture": data.get("picture"),
            "password_hash": None,
            "created_at": now_iso(),
        }
        await db.users.insert_one(user)

    session_token = data.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Invalid session data")
    expires_at = (datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)).isoformat()
    await db.user_sessions.insert_one({
        "session_token": session_token,
        "user_id": user["id"],
        "expires_at": expires_at,
        "created_at": now_iso(),
    })
    response.set_cookie("session_token", session_token, httponly=True, secure=True,
                        samesite="none", max_age=SESSION_TTL_DAYS * 86400, path="/")
    return public_user(user)


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return user


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    clear_auth_cookies(response)
    return {"success": True}
