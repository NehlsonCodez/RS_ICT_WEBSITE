"""Service 1 — E-Government Portal Management."""
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.database import get_db
from app.models.models import PortalRequest, Portal, AuditLog, PortalStatus, UserRole
from app.dependencies.auth import require_login, require_admin, get_current_user, gen_ref

router = APIRouter(prefix="/services/portal", tags=["portal"])
templates = Jinja2Templates(directory="app/templates")
PAGE_SIZE = 10


# ─── PUBLIC: Browse approved portals ─────────────────────────────────────────
@router.get("", response_class=HTMLResponse)
async def portal_index(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    portals = (await db.execute(
        select(Portal).where(Portal.is_active == True).order_by(Portal.name)
    )).scalars().all()
    return templates.TemplateResponse(request, "services/portal/index.html", {
        "request": request, "page": "services", "user": user, "portals": portals
    })


# ─── CITIZEN: Submit portal request ──────────────────────────────────────────
@router.get("/request", response_class=HTMLResponse)
async def portal_request_form(request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    return templates.TemplateResponse(request, "services/portal/request.html", {
        "request": request, "page": "services", "user": user
    })


@router.post("/request")
async def portal_request_submit(
    request: Request,
    ministry: str = Form(...),
    portal_name: str = Form(...),
    target_domain: str = Form(default=""),
    description: str = Form(...),
    contact_officer: str = Form(...),
    contact_email: str = Form(...),
    phone: str = Form(default=""),
    purpose: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await require_login(request, db)
    ref = gen_ref("PRT")
    req = PortalRequest(
        reference=ref, user_id=user.id,
        ministry=ministry, portal_name=portal_name,
        target_domain=target_domain or None, description=description,
        contact_officer=contact_officer, contact_email=contact_email,
        phone=phone or None, purpose=purpose,
    )
    db.add(req)
    await db.flush()
    log = AuditLog(portal_request_id=req.id, action="submitted", performed_by=user.email)
    db.add(log)
    await db.commit()
    return RedirectResponse(f"/services/portal/track/{ref}?success=1", status_code=302)


@router.get("/track/{reference}", response_class=HTMLResponse)
async def portal_track(reference: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    result = await db.execute(select(PortalRequest).where(PortalRequest.reference == reference))
    req = result.scalar_one_or_none()
    if not req or (req.user_id != user.id and user.role != UserRole.admin):
        raise HTTPException(404, "Request not found")
    logs = (await db.execute(
        select(AuditLog).where(AuditLog.portal_request_id == req.id).order_by(AuditLog.created_at)
    )).scalars().all()
    return templates.TemplateResponse(request, "services/portal/track.html", {
        "request": request, "page": "services", "user": user,
        "req": req, "logs": logs, "success": request.query_params.get("success")
    })


# ─── ADMIN ────────────────────────────────────────────────────────────────────
@router.get("/admin", response_class=HTMLResponse)
async def portal_admin(
    request: Request,
    page: int = 1,
    status: str = "",
    q: str = "",
    db: AsyncSession = Depends(get_db),
):
    user = await require_admin(request, db)
    query = select(PortalRequest).order_by(PortalRequest.submitted_at.desc())
    if status:
        query = query.where(PortalRequest.status == status)
    if q:
        query = query.where(or_(
            PortalRequest.portal_name.ilike(f"%{q}%"),
            PortalRequest.ministry.ilike(f"%{q}%"),
            PortalRequest.reference.ilike(f"%{q}%"),
        ))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    requests = (await db.execute(query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).scalars().all()
    return templates.TemplateResponse(request, "services/portal/admin.html", {
        "request": request, "page": "admin", "user": user,
        "requests": requests, "total": total, "current_page": page,
        "total_pages": (total + PAGE_SIZE - 1) // PAGE_SIZE,
        "status_filter": status, "q": q,
        "statuses": [s.value for s in PortalStatus]
    })


@router.post("/admin/{req_id}/update")
async def portal_admin_update(
    req_id: str,
    request: Request,
    status: str = Form(...),
    admin_notes: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    user = await require_admin(request, db)
    result = await db.execute(select(PortalRequest).where(PortalRequest.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404)
    old_status = req.status
    req.status = PortalStatus(status)
    req.admin_notes = admin_notes
    req.updated_at = datetime.utcnow()
    log = AuditLog(
        portal_request_id=req.id,
        action=f"Status changed: {old_status} → {status}",
        performed_by=user.email, notes=admin_notes
    )
    db.add(log)
    await db.commit()
    return RedirectResponse(f"/services/portal/admin?updated=1", status_code=302)
