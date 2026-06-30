"""
Session-based authentication dependencies.
Uses itsdangerous signed cookies for session management.
"""
import os
import random
import string
import bcrypt
from typing import Optional
from datetime import datetime

from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.models import User, UserRole

SECRET_KEY = os.environ.get("SECRET_KEY", "rs-ict-secret-change-in-production-2024")
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

serializer = URLSafeTimedSerializer(SECRET_KEY)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly (avoids passlib/bcrypt version bugs)."""
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_session_token(user_id: str) -> str:
    return serializer.dumps(user_id, salt="session")


def decode_session_token(token: str) -> Optional[str]:
    try:
        return serializer.loads(token, salt="session", max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def gen_ref(prefix: str = "REF") -> str:
    return f"{prefix}-" + "".join(random.choices(string.digits, k=6))


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    token = request.cookies.get("session_token")
    if not token:
        return None
    user_id = decode_session_token(token)
    if not user_id:
        return None
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    return result.scalar_one_or_none()


async def require_login(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=302, headers={"Location": "/auth/login?next=" + str(request.url.path)})
    return user


async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await require_login(request, db)
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def require_staff(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Admin, analyst, engineer, or technician."""
    user = await require_login(request, db)
    staff_roles = {UserRole.admin, UserRole.analyst, UserRole.engineer, UserRole.technician}
    if user.role not in staff_roles:
        raise HTTPException(status_code=403, detail="Staff access required")
    return user
