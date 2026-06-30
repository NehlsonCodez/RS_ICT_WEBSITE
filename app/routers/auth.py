"""Authentication router — register, login, logout, profile."""
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.models import User, UserRole
from app.dependencies.auth import (
    hash_password, verify_password, create_session_token,
    get_current_user, require_login
)

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


def flash(response, message: str, category: str = "success"):
    """Store flash message in cookie."""
    response.set_cookie("flash_msg", message, max_age=10, httponly=True)
    response.set_cookie("flash_cat", category, max_age=10, httponly=True)


def get_flash(request: Request):
    return {
        "flash_message": request.cookies.get("flash_msg"),
        "flash_category": request.cookies.get("flash_cat"),
    }


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/dashboard"):
    user = await get_current_user(request, await get_db().__anext__())
    if user:
        return RedirectResponse(next, status_code=302)
    return templates.TemplateResponse(request, "auth/login.html", {
        "request": request, "page": "login", "next": next, **get_flash(request)
    })


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form(default="/dashboard"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == email.lower().strip()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        resp = templates.TemplateResponse(request, "auth/login.html", {
            "request": request, "page": "login", "next": next,
            "flash_message": "Invalid email or password.", "flash_category": "error",
            "email": email
        })
        return resp
    if not user.is_active:
        resp = templates.TemplateResponse(request, "auth/login.html", {
            "request": request, "page": "login", "next": next,
            "flash_message": "Account is deactivated. Contact admin.", "flash_category": "error"
        })
        return resp
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    token = create_session_token(user.id)
    redirect_to = next if next.startswith("/") else "/dashboard"
    response = RedirectResponse(redirect_to, status_code=302)
    response.set_cookie("session_token", token, httponly=True, max_age=60 * 60 * 24 * 7, samesite="lax")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "auth/register.html", {
        "request": request, "page": "register", **get_flash(request)
    })


@router.post("/register")
async def register_submit(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(default=""),
    password: str = Form(...),
    confirm_password: str = Form(...),
    role: str = Form(default="citizen"),
    agency_name: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    errors = {}
    if len(password) < 6:
        errors["password"] = "Password must be at least 6 characters."
    if password != confirm_password:
        errors["confirm_password"] = "Passwords do not match."
    existing = await db.execute(select(User).where(User.email == email.lower().strip()))
    if existing.scalar_one_or_none():
        errors["email"] = "An account with this email already exists."

    if errors:
        return templates.TemplateResponse(request, "auth/register.html", {
            "request": request, "page": "register",
            "errors": errors, "values": {"full_name": full_name, "email": email, "phone": phone, "role": role, "agency_name": agency_name}
        })

    safe_role = UserRole.citizen
    if role in [r.value for r in UserRole]:
        safe_role = UserRole(role)
    if safe_role == UserRole.admin:
        safe_role = UserRole.citizen  # cannot self-register as admin

    user = User(
        full_name=full_name.strip(),
        email=email.lower().strip(),
        phone=phone.strip() or None,
        hashed_password=hash_password(password),
        role=safe_role,
        agency_name=agency_name.strip() or None,
    )
    db.add(user)
    await db.commit()
    token = create_session_token(user.id)
    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie("session_token", token, httponly=True, max_age=60 * 60 * 24 * 7, samesite="lax")
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("session_token")
    return response


@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    return templates.TemplateResponse(request, "auth/profile.html", {
        "request": request, "page": "profile", "user": user, **get_flash(request)
    })
