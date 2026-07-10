import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Auth models ----------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SessionRequest(BaseModel):
    session_id: str


# ---------- Admin user management ----------
class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "staff"


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None


# ---------- Visitor models ----------
class VisitorCreate(BaseModel):
    visit_date: str
    visitor_name: str
    address: Optional[str] = ""
    telephone: Optional[str] = ""
    whom_to_see: str
    department: str
    purpose: str  # official | workshop | meetings
    floor: Optional[str] = ""
    tag_number: Optional[str] = ""
    time_in: Optional[str] = None
    notes: Optional[str] = ""
    photo: Optional[str] = None


class VisitorUpdate(BaseModel):
    visit_date: Optional[str] = None
    visitor_name: Optional[str] = None
    address: Optional[str] = None
    telephone: Optional[str] = None
    whom_to_see: Optional[str] = None
    department: Optional[str] = None
    purpose: Optional[str] = None
    floor: Optional[str] = None
    tag_number: Optional[str] = None
    time_in: Optional[str] = None
    time_out: Optional[str] = None
    tag_status: Optional[str] = None
    visit_status: Optional[str] = None
    notes: Optional[str] = None
    photo: Optional[str] = None
