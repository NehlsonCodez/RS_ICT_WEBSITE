"""Dashboard router — citizen dashboard and admin overview."""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.models import (
    User, UserRole, PortalRequest, InfrastructureRequest,
    Incident, CloudRequest, Enrollment, ComplianceRequest,
    Startup, Ticket, TicketStatus, PortalStatus, InfraStatus,
    IncidentStatus, CloudStatus, EnrollmentStatus, ComplianceStatus, StartupStatus
)
from app.dependencies.auth import require_login, require_admin

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)

    if user.role == UserRole.admin:
        # Admin stats
        stats = {}
        for model, name in [
            (PortalRequest, "portals"), (InfrastructureRequest, "infra"),
            (Incident, "incidents"), (CloudRequest, "cloud"),
            (Enrollment, "enrollments"), (Ticket, "tickets"),
        ]:
            r = await db.execute(select(func.count(model.id)))
            stats[name] = r.scalar_one()

        # Pending counts
        pending = {}
        pending["portals"] = (await db.execute(
            select(func.count(PortalRequest.id)).where(PortalRequest.status == PortalStatus.pending)
        )).scalar_one()
        pending["infra"] = (await db.execute(
            select(func.count(InfrastructureRequest.id)).where(InfrastructureRequest.status == InfraStatus.submitted)
        )).scalar_one()
        pending["incidents"] = (await db.execute(
            select(func.count(Incident.id)).where(Incident.status == IncidentStatus.reported)
        )).scalar_one()
        pending["tickets"] = (await db.execute(
            select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.open)
        )).scalar_one()

        recent_tickets = (await db.execute(
            select(Ticket).order_by(Ticket.created_at.desc()).limit(5)
        )).scalars().all()

        return templates.TemplateResponse(request, "admin/dashboard.html", {
            "request": request, "page": "dashboard", "user": user,
            "stats": stats, "pending": pending, "recent_tickets": recent_tickets
        })

    # Citizen dashboard
    my_portals = (await db.execute(
        select(PortalRequest).where(PortalRequest.user_id == user.id).order_by(PortalRequest.submitted_at.desc()).limit(5)
    )).scalars().all()
    my_infra = (await db.execute(
        select(InfrastructureRequest).where(InfrastructureRequest.user_id == user.id).order_by(InfrastructureRequest.submitted_at.desc()).limit(5)
    )).scalars().all()
    my_incidents = (await db.execute(
        select(Incident).where(Incident.user_id == user.id).order_by(Incident.reported_at.desc()).limit(5)
    )).scalars().all()
    my_tickets = (await db.execute(
        select(Ticket).where(Ticket.user_id == user.id).order_by(Ticket.created_at.desc()).limit(5)
    )).scalars().all()
    my_enrollments = (await db.execute(
        select(Enrollment).where(Enrollment.user_id == user.id).order_by(Enrollment.applied_at.desc()).limit(5)
    )).scalars().all()

    return templates.TemplateResponse(request, "dashboard/citizen.html", {
        "request": request, "page": "dashboard", "user": user,
        "my_portals": my_portals, "my_infra": my_infra,
        "my_incidents": my_incidents, "my_tickets": my_tickets,
        "my_enrollments": my_enrollments,
    })
