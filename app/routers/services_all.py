"""
Services 2–8 routers consolidated.
Each service gets its own prefix and templates.
"""
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.database import get_db
from app.models.models import (
    InfrastructureRequest, EngineerAssignment, InfraStatus,
    Incident, Evidence, SecurityAdvisory, IncidentStatus, IncidentSeverity,
    CloudRequest, CloudAllocation, CloudStatus,
    Course, TrainingSession, Enrollment, Certificate, EnrollmentStatus,
    Policy, PolicyVersion, ComplianceRequest, ComplianceStatus, PolicyStatus,
    Startup, GrantApplication, StartupStatus,
    Ticket, TicketReply, TicketAttachment, TicketStatus, TicketPriority,
    UserRole
)
from app.dependencies.auth import require_login, require_admin, require_staff, get_current_user, gen_ref

templates = Jinja2Templates(directory="app/templates")
PAGE_SIZE = 10

# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE 2 — ICT INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════
infra_router = APIRouter(prefix="/services/infrastructure", tags=["infrastructure"])


@infra_router.get("", response_class=HTMLResponse)
async def infra_index(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    stats = {
        "total": (await db.execute(select(func.count(InfrastructureRequest.id)))).scalar_one(),
        "completed": (await db.execute(select(func.count(InfrastructureRequest.id)).where(InfrastructureRequest.status == InfraStatus.completed))).scalar_one(),
        "in_progress": (await db.execute(select(func.count(InfrastructureRequest.id)).where(InfrastructureRequest.status == InfraStatus.in_progress))).scalar_one(),
    }
    return templates.TemplateResponse(request, "services/infrastructure/index.html", {
        "request": request, "page": "services", "user": user, "stats": stats
    })


@infra_router.get("/report", response_class=HTMLResponse)
async def infra_report_form(request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    return templates.TemplateResponse(request, "services/infrastructure/report.html", {
        "request": request, "page": "services", "user": user
    })


@infra_router.post("/report")
async def infra_report_submit(
    request: Request,
    lga: str = Form(...), community: str = Form(...),
    institution: str = Form(default=""), gps_lat: str = Form(default=""),
    gps_lng: str = Form(default=""), issue_type: str = Form(...),
    description: str = Form(...), db: AsyncSession = Depends(get_db),
):
    user = await require_login(request, db)
    ref = gen_ref("INF")
    req = InfrastructureRequest(
        reference=ref, user_id=user.id,
        lga=lga, community=community,
        institution=institution or None,
        gps_lat=float(gps_lat) if gps_lat else None,
        gps_lng=float(gps_lng) if gps_lng else None,
        issue_type=issue_type, description=description,
    )
    db.add(req); await db.commit()
    return RedirectResponse(f"/services/infrastructure/track/{ref}?success=1", status_code=302)


@infra_router.get("/track/{reference}", response_class=HTMLResponse)
async def infra_track(reference: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    result = await db.execute(select(InfrastructureRequest).where(InfrastructureRequest.reference == reference))
    req = result.scalar_one_or_none()
    if not req or (req.user_id != user.id and user.role != UserRole.admin):
        raise HTTPException(404)
    assignments = (await db.execute(select(EngineerAssignment).where(EngineerAssignment.request_id == req.id))).scalars().all()
    return templates.TemplateResponse(request, "services/infrastructure/track.html", {
        "request": request, "page": "services", "user": user,
        "req": req, "assignments": assignments, "success": request.query_params.get("success")
    })


@infra_router.get("/admin", response_class=HTMLResponse)
async def infra_admin(request: Request, page: int = 1, status: str = "", q: str = "", db: AsyncSession = Depends(get_db)):
    user = await require_admin(request, db)
    query = select(InfrastructureRequest).order_by(InfrastructureRequest.submitted_at.desc())
    if status:
        query = query.where(InfrastructureRequest.status == status)
    if q:
        query = query.where(or_(InfrastructureRequest.lga.ilike(f"%{q}%"), InfrastructureRequest.community.ilike(f"%{q}%"), InfrastructureRequest.reference.ilike(f"%{q}%")))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    items = (await db.execute(query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).scalars().all()
    return templates.TemplateResponse(request, "services/infrastructure/admin.html", {
        "request": request, "page": "admin", "user": user,
        "items": items, "total": total, "current_page": page,
        "total_pages": (total + PAGE_SIZE - 1) // PAGE_SIZE,
        "status_filter": status, "q": q, "statuses": [s.value for s in InfraStatus]
    })


@infra_router.post("/admin/{req_id}/update")
async def infra_admin_update(
    req_id: str, request: Request,
    status: str = Form(...), admin_notes: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    user = await require_admin(request, db)
    result = await db.execute(select(InfrastructureRequest).where(InfrastructureRequest.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404)
    req.status = InfraStatus(status); req.admin_notes = admin_notes; req.updated_at = datetime.utcnow()
    if status == "completed":
        req.completed_at = datetime.utcnow()
    await db.commit()
    return RedirectResponse("/services/infrastructure/admin", status_code=302)


@infra_router.post("/admin/{req_id}/assign")
async def infra_assign(
    req_id: str, request: Request,
    engineer_name: str = Form(...), engineer_email: str = Form(default=""),
    notes: str = Form(default=""), db: AsyncSession = Depends(get_db),
):
    user = await require_admin(request, db)
    result = await db.execute(select(InfrastructureRequest).where(InfrastructureRequest.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404)
    assignment = EngineerAssignment(request_id=req.id, engineer_name=engineer_name, engineer_email=engineer_email or None, notes=notes or None)
    req.status = InfraStatus.assigned; req.updated_at = datetime.utcnow()
    db.add(assignment); await db.commit()
    return RedirectResponse("/services/infrastructure/admin", status_code=302)


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE 3 — CYBERSECURITY
# ═══════════════════════════════════════════════════════════════════════════════
cyber_router = APIRouter(prefix="/services/cybersecurity", tags=["cybersecurity"])

INCIDENT_TYPES = ["Phishing", "Malware", "Data Leak", "Unauthorized Access", "Website Defacement", "Ransomware", "DDoS Attack", "Other"]


@cyber_router.get("", response_class=HTMLResponse)
async def cyber_index(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    advisories = (await db.execute(
        select(SecurityAdvisory).where(SecurityAdvisory.is_published == True).order_by(SecurityAdvisory.published_at.desc()).limit(5)
    )).scalars().all()
    return templates.TemplateResponse(request, "services/cybersecurity/index.html", {
        "request": request, "page": "services", "user": user, "advisories": advisories
    })


@cyber_router.get("/report", response_class=HTMLResponse)
async def cyber_report_form(request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    return templates.TemplateResponse(request, "services/cybersecurity/report.html", {
        "request": request, "page": "services", "user": user,
        "incident_types": INCIDENT_TYPES, "severities": [s.value for s in IncidentSeverity]
    })


@cyber_router.post("/report")
async def cyber_report_submit(
    request: Request,
    incident_type: str = Form(...), severity: str = Form(...),
    title: str = Form(...), description: str = Form(...),
    affected_system: str = Form(default=""), affected_agency: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    user = await require_login(request, db)
    ref = gen_ref("CYB")
    incident = Incident(
        reference=ref, user_id=user.id,
        incident_type=incident_type, severity=IncidentSeverity(severity),
        title=title, description=description,
        affected_system=affected_system or None, affected_agency=affected_agency or None,
    )
    db.add(incident); await db.commit()
    return RedirectResponse(f"/services/cybersecurity/track/{ref}?success=1", status_code=302)


@cyber_router.get("/track/{reference}", response_class=HTMLResponse)
async def cyber_track(reference: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    result = await db.execute(select(Incident).where(Incident.reference == reference))
    inc = result.scalar_one_or_none()
    if not inc or (inc.user_id != user.id and user.role != UserRole.admin):
        raise HTTPException(404)
    return templates.TemplateResponse(request, "services/cybersecurity/track.html", {
        "request": request, "page": "services", "user": user,
        "inc": inc, "success": request.query_params.get("success")
    })


@cyber_router.get("/advisories", response_class=HTMLResponse)
async def cyber_advisories(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    advisories = (await db.execute(
        select(SecurityAdvisory).where(SecurityAdvisory.is_published == True).order_by(SecurityAdvisory.published_at.desc())
    )).scalars().all()
    return templates.TemplateResponse(request, "services/cybersecurity/advisories.html", {
        "request": request, "page": "services", "user": user, "advisories": advisories
    })


@cyber_router.get("/admin", response_class=HTMLResponse)
async def cyber_admin(request: Request, page: int = 1, status: str = "", severity: str = "", q: str = "", db: AsyncSession = Depends(get_db)):
    user = await require_admin(request, db)
    query = select(Incident).order_by(Incident.reported_at.desc())
    if status:
        query = query.where(Incident.status == status)
    if severity:
        query = query.where(Incident.severity == severity)
    if q:
        query = query.where(or_(Incident.title.ilike(f"%{q}%"), Incident.reference.ilike(f"%{q}%")))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    items = (await db.execute(query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).scalars().all()
    return templates.TemplateResponse(request, "services/cybersecurity/admin.html", {
        "request": request, "page": "admin", "user": user,
        "items": items, "total": total, "current_page": page,
        "total_pages": (total + PAGE_SIZE - 1) // PAGE_SIZE,
        "status_filter": status, "severity_filter": severity, "q": q,
        "statuses": [s.value for s in IncidentStatus], "severities": [s.value for s in IncidentSeverity]
    })


@cyber_router.post("/admin/{inc_id}/update")
async def cyber_admin_update(
    inc_id: str, request: Request,
    status: str = Form(...), severity: str = Form(...),
    analyst_notes: str = Form(default=""), db: AsyncSession = Depends(get_db),
):
    user = await require_admin(request, db)
    result = await db.execute(select(Incident).where(Incident.id == inc_id))
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(404)
    inc.status = IncidentStatus(status); inc.severity = IncidentSeverity(severity)
    inc.analyst_notes = analyst_notes; inc.updated_at = datetime.utcnow()
    if status in ("resolved", "closed"):
        inc.resolved_at = datetime.utcnow()
    await db.commit()
    return RedirectResponse("/services/cybersecurity/admin", status_code=302)


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE 4 — CLOUD & DATA CENTRE
# ═══════════════════════════════════════════════════════════════════════════════
cloud_router = APIRouter(prefix="/services/cloud", tags=["cloud"])

CLOUD_SERVICES = ["Virtual Server", "Cloud Storage", "Database Hosting", "Application Hosting", "Backup Services", "Disaster Recovery"]


@cloud_router.get("", response_class=HTMLResponse)
async def cloud_index(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "services/cloud/index.html", {
        "request": request, "page": "services", "user": user, "cloud_services": CLOUD_SERVICES
    })


@cloud_router.get("/request", response_class=HTMLResponse)
async def cloud_request_form(request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    return templates.TemplateResponse(request, "services/cloud/request.html", {
        "request": request, "page": "services", "user": user, "cloud_services": CLOUD_SERVICES
    })


@cloud_router.post("/request")
async def cloud_request_submit(
    request: Request,
    agency_name: str = Form(...), service_type: str = Form(...),
    cpu_cores: str = Form(default=""), ram_gb: str = Form(default=""),
    storage_gb: str = Form(default=""), purpose: str = Form(...),
    expected_users: str = Form(default=""), db: AsyncSession = Depends(get_db),
):
    user = await require_login(request, db)
    ref = gen_ref("CLD")
    req = CloudRequest(
        reference=ref, user_id=user.id,
        agency_name=agency_name, service_type=service_type,
        cpu_cores=int(cpu_cores) if cpu_cores else None,
        ram_gb=int(ram_gb) if ram_gb else None,
        storage_gb=int(storage_gb) if storage_gb else None,
        purpose=purpose,
        expected_users=int(expected_users) if expected_users else None,
    )
    db.add(req); await db.commit()
    return RedirectResponse(f"/services/cloud/track/{ref}?success=1", status_code=302)


@cloud_router.get("/track/{reference}", response_class=HTMLResponse)
async def cloud_track(reference: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    result = await db.execute(select(CloudRequest).where(CloudRequest.reference == reference))
    req = result.scalar_one_or_none()
    if not req or (req.user_id != user.id and user.role != UserRole.admin):
        raise HTTPException(404)
    return templates.TemplateResponse(request, "services/cloud/track.html", {
        "request": request, "page": "services", "user": user,
        "req": req, "success": request.query_params.get("success")
    })


@cloud_router.get("/admin", response_class=HTMLResponse)
async def cloud_admin(request: Request, page: int = 1, status: str = "", db: AsyncSession = Depends(get_db)):
    user = await require_admin(request, db)
    query = select(CloudRequest).order_by(CloudRequest.submitted_at.desc())
    if status:
        query = query.where(CloudRequest.status == status)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    items = (await db.execute(query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).scalars().all()
    return templates.TemplateResponse(request, "services/cloud/admin.html", {
        "request": request, "page": "admin", "user": user,
        "items": items, "total": total, "current_page": page,
        "total_pages": (total + PAGE_SIZE - 1) // PAGE_SIZE,
        "status_filter": status, "statuses": [s.value for s in CloudStatus]
    })


@cloud_router.post("/admin/{req_id}/update")
async def cloud_admin_update(
    req_id: str, request: Request,
    status: str = Form(...), admin_notes: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    user = await require_admin(request, db)
    result = await db.execute(select(CloudRequest).where(CloudRequest.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404)
    req.status = CloudStatus(status); req.admin_notes = admin_notes; req.updated_at = datetime.utcnow()
    await db.commit()
    return RedirectResponse("/services/cloud/admin", status_code=302)


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE 5 — DIGITAL SKILLS TRAINING
# ═══════════════════════════════════════════════════════════════════════════════
training_router = APIRouter(prefix="/services/training", tags=["training"])


@training_router.get("", response_class=HTMLResponse)
async def training_index(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    courses = (await db.execute(select(Course).where(Course.is_active == True).order_by(Course.title))).scalars().all()
    return templates.TemplateResponse(request, "services/training/index.html", {
        "request": request, "page": "services", "user": user, "courses": courses
    })


@training_router.get("/course/{course_id}", response_class=HTMLResponse)
async def course_detail(course_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(404)
    sessions = (await db.execute(
        select(TrainingSession).where(TrainingSession.course_id == course_id, TrainingSession.is_open == True)
    )).scalars().all()
    return templates.TemplateResponse(request, "services/training/course.html", {
        "request": request, "page": "services", "user": user,
        "course": course, "sessions": sessions
    })


@training_router.post("/enroll")
async def training_enroll(
    request: Request, session_id: str = Form(...), db: AsyncSession = Depends(get_db)
):
    user = await require_login(request, db)
    # Check not already enrolled
    existing = (await db.execute(
        select(Enrollment).where(Enrollment.user_id == user.id, Enrollment.session_id == session_id)
    )).scalar_one_or_none()
    if existing:
        return RedirectResponse(f"/services/training/my?already=1", status_code=302)
    ref = gen_ref("ENR")
    enr = Enrollment(reference=ref, user_id=user.id, session_id=session_id)
    db.add(enr); await db.commit()
    return RedirectResponse(f"/services/training/track/{ref}?success=1", status_code=302)


@training_router.get("/track/{reference}", response_class=HTMLResponse)
async def training_track(reference: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    result = await db.execute(select(Enrollment).where(Enrollment.reference == reference))
    enr = result.scalar_one_or_none()
    if not enr or (enr.user_id != user.id and user.role != UserRole.admin):
        raise HTTPException(404)
    return templates.TemplateResponse(request, "services/training/track.html", {
        "request": request, "page": "services", "user": user,
        "enr": enr, "success": request.query_params.get("success")
    })


@training_router.get("/my", response_class=HTMLResponse)
async def my_enrollments(request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    enrollments = (await db.execute(
        select(Enrollment).where(Enrollment.user_id == user.id).order_by(Enrollment.applied_at.desc())
    )).scalars().all()
    return templates.TemplateResponse(request, "services/training/my.html", {
        "request": request, "page": "services", "user": user,
        "enrollments": enrollments, "already": request.query_params.get("already")
    })


@training_router.get("/admin", response_class=HTMLResponse)
async def training_admin(request: Request, page: int = 1, status: str = "", db: AsyncSession = Depends(get_db)):
    user = await require_admin(request, db)
    query = select(Enrollment).order_by(Enrollment.applied_at.desc())
    if status:
        query = query.where(Enrollment.status == status)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    items = (await db.execute(query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).scalars().all()
    courses = (await db.execute(select(Course))).scalars().all()
    return templates.TemplateResponse(request, "services/training/admin.html", {
        "request": request, "page": "admin", "user": user,
        "items": items, "total": total, "current_page": page,
        "total_pages": (total + PAGE_SIZE - 1) // PAGE_SIZE,
        "status_filter": status, "statuses": [s.value for s in EnrollmentStatus],
        "courses": courses,
    })


@training_router.post("/admin/enrollment/{enr_id}/update")
async def training_admin_update(
    enr_id: str, request: Request,
    status: str = Form(...), admin_notes: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    user = await require_admin(request, db)
    result = await db.execute(select(Enrollment).where(Enrollment.id == enr_id))
    enr = result.scalar_one_or_none()
    if not enr:
        raise HTTPException(404)
    enr.status = EnrollmentStatus(status); enr.admin_notes = admin_notes; enr.updated_at = datetime.utcnow()
    if status == "completed" and not enr.certificate:
        import random, string as st
        cert_num = "RSICT-CERT-" + "".join(random.choices(st.digits, k=8))
        cert = Certificate(enrollment_id=enr.id, certificate_number=cert_num)
        db.add(cert)
    await db.commit()
    return RedirectResponse("/services/training/admin", status_code=302)


@training_router.post("/admin/course/create")
async def training_create_course(
    request: Request,
    title: str = Form(...), category: str = Form(...),
    description: str = Form(default=""), duration_weeks: str = Form(default=""),
    fee: str = Form(default="0"), is_free: str = Form(default="true"),
    level: str = Form(default=""), db: AsyncSession = Depends(get_db),
):
    user = await require_admin(request, db)
    course = Course(
        title=title, category=category,
        description=description or None,
        duration_weeks=int(duration_weeks) if duration_weeks else None,
        fee=float(fee) if fee else 0.0,
        is_free=is_free.lower() == "true",
        level=level or None,
    )
    db.add(course); await db.commit()
    return RedirectResponse("/services/training/admin", status_code=302)


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE 6 — ICT POLICY & COMPLIANCE
# ═══════════════════════════════════════════════════════════════════════════════
policy_router = APIRouter(prefix="/services/policy", tags=["policy"])


@policy_router.get("", response_class=HTMLResponse)
async def policy_index(request: Request, q: str = "", db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    query = select(Policy).where(Policy.status == PolicyStatus.active)
    if q:
        query = query.where(or_(Policy.title.ilike(f"%{q}%"), Policy.category.ilike(f"%{q}%")))
    policies = (await db.execute(query.order_by(Policy.title))).scalars().all()
    return templates.TemplateResponse(request, "services/policy/index.html", {
        "request": request, "page": "services", "user": user, "policies": policies, "q": q
    })


@policy_router.get("/compliance", response_class=HTMLResponse)
async def compliance_form(request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    policies = (await db.execute(select(Policy).where(Policy.status == PolicyStatus.active))).scalars().all()
    return templates.TemplateResponse(request, "services/policy/compliance.html", {
        "request": request, "page": "services", "user": user, "policies": policies
    })


@policy_router.post("/compliance")
async def compliance_submit(
    request: Request,
    agency_name: str = Form(...), procurement_title: str = Form(...),
    specifications: str = Form(...), estimated_value: str = Form(default=""),
    policy_id: str = Form(default=""), db: AsyncSession = Depends(get_db),
):
    user = await require_login(request, db)
    ref = gen_ref("CMP")
    req = ComplianceRequest(
        reference=ref, user_id=user.id,
        agency_name=agency_name, procurement_title=procurement_title,
        specifications=specifications,
        estimated_value=float(estimated_value) if estimated_value else None,
        policy_id=policy_id or None,
    )
    db.add(req); await db.commit()
    return RedirectResponse(f"/services/policy/track/{ref}?success=1", status_code=302)


@policy_router.get("/track/{reference}", response_class=HTMLResponse)
async def compliance_track(reference: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    result = await db.execute(select(ComplianceRequest).where(ComplianceRequest.reference == reference))
    req = result.scalar_one_or_none()
    if not req or (req.user_id != user.id and user.role != UserRole.admin):
        raise HTTPException(404)
    return templates.TemplateResponse(request, "services/policy/track.html", {
        "request": request, "page": "services", "user": user,
        "req": req, "success": request.query_params.get("success")
    })


@policy_router.get("/admin", response_class=HTMLResponse)
async def policy_admin(request: Request, page: int = 1, status: str = "", db: AsyncSession = Depends(get_db)):
    user = await require_admin(request, db)
    query = select(ComplianceRequest).order_by(ComplianceRequest.submitted_at.desc())
    if status:
        query = query.where(ComplianceRequest.status == status)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    items = (await db.execute(query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).scalars().all()
    policies = (await db.execute(select(Policy))).scalars().all()
    return templates.TemplateResponse(request, "services/policy/admin.html", {
        "request": request, "page": "admin", "user": user,
        "items": items, "total": total, "current_page": page,
        "total_pages": (total + PAGE_SIZE - 1) // PAGE_SIZE,
        "status_filter": status, "statuses": [s.value for s in ComplianceStatus],
        "policies": policies,
    })


@policy_router.post("/admin/{req_id}/update")
async def policy_admin_update(
    req_id: str, request: Request,
    status: str = Form(...), compliance_result: str = Form(default=""),
    reviewer_notes: str = Form(default=""), db: AsyncSession = Depends(get_db),
):
    user = await require_admin(request, db)
    result = await db.execute(select(ComplianceRequest).where(ComplianceRequest.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404)
    req.status = ComplianceStatus(status); req.compliance_result = compliance_result
    req.reviewer_notes = reviewer_notes; req.updated_at = datetime.utcnow()
    await db.commit()
    return RedirectResponse("/services/policy/admin", status_code=302)


@policy_router.post("/admin/policy/create")
async def create_policy(
    request: Request, title: str = Form(...),
    category: str = Form(default=""), description: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    user = await require_admin(request, db)
    policy = Policy(title=title, category=category or None, description=description or None)
    db.add(policy); await db.commit()
    return RedirectResponse("/services/policy/admin", status_code=302)


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE 7 — TECH ECOSYSTEM
# ═══════════════════════════════════════════════════════════════════════════════
ecosystem_router = APIRouter(prefix="/services/ecosystem", tags=["ecosystem"])

SECTORS = ["Fintech", "Edtech", "Healthtech", "Agritech", "Logistics", "AI/ML", "Cybersecurity", "E-commerce", "Media/Content", "Energy", "Other"]
ENTITY_TYPES = ["Startup", "Innovation Hub", "Incubator", "Accelerator", "Training Centre", "Investor"]
FUNDING_STAGES = ["Pre-seed", "Seed", "Series A", "Series B", "Series C+", "Bootstrapped", "Grant-funded"]


@ecosystem_router.get("", response_class=HTMLResponse)
async def ecosystem_index(request: Request, q: str = "", sector: str = "", page: int = 1, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    query = select(Startup).where(Startup.status == StartupStatus.verified)
    if q:
        query = query.where(or_(Startup.company_name.ilike(f"%{q}%"), Startup.description.ilike(f"%{q}%")))
    if sector:
        query = query.where(Startup.sector == sector)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    startups = (await db.execute(query.order_by(Startup.company_name).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).scalars().all()
    return templates.TemplateResponse(request, "services/ecosystem/index.html", {
        "request": request, "page_name": "services", "user": user,
        "startups": startups, "total": total, "current_page": page,
        "total_pages": (total + PAGE_SIZE - 1) // PAGE_SIZE,
        "q": q, "sector_filter": sector, "sectors": SECTORS
    })


@ecosystem_router.get("/register", response_class=HTMLResponse)
async def ecosystem_register_form(request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    return templates.TemplateResponse(request, "services/ecosystem/register.html", {
        "request": request, "page": "services", "user": user,
        "sectors": SECTORS, "entity_types": ENTITY_TYPES, "funding_stages": FUNDING_STAGES
    })


@ecosystem_router.post("/register")
async def ecosystem_register_submit(
    request: Request,
    company_name: str = Form(...), entity_type: str = Form(default="startup"),
    sector: str = Form(default=""), location: str = Form(default=""),
    lga: str = Form(default=""), founding_year: str = Form(default=""),
    website: str = Form(default=""), email: str = Form(default=""),
    phone: str = Form(default=""), employees: str = Form(default=""),
    funding_stage: str = Form(default=""), description: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    user = await require_login(request, db)
    startup = Startup(
        owner_id=user.id, company_name=company_name,
        entity_type=entity_type, sector=sector or None,
        location=location or None, lga=lga or None,
        founding_year=int(founding_year) if founding_year else None,
        website=website or None, email=email or None,
        phone=phone or None,
        employees=int(employees) if employees else None,
        funding_stage=funding_stage or None,
        description=description or None,
    )
    db.add(startup); await db.commit()
    return RedirectResponse(f"/services/ecosystem/profile/{startup.id}?success=1", status_code=302)


@ecosystem_router.get("/profile/{startup_id}", response_class=HTMLResponse)
async def ecosystem_profile(startup_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    result = await db.execute(select(Startup).where(Startup.id == startup_id))
    startup = result.scalar_one_or_none()
    if not startup:
        raise HTTPException(404)
    return templates.TemplateResponse(request, "services/ecosystem/profile.html", {
        "request": request, "page": "services", "user": user,
        "startup": startup, "success": request.query_params.get("success")
    })


@ecosystem_router.get("/admin", response_class=HTMLResponse)
async def ecosystem_admin(request: Request, page: int = 1, status: str = "", db: AsyncSession = Depends(get_db)):
    user = await require_admin(request, db)
    query = select(Startup).order_by(Startup.registered_at.desc())
    if status:
        query = query.where(Startup.status == status)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    items = (await db.execute(query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).scalars().all()
    return templates.TemplateResponse(request, "services/ecosystem/admin.html", {
        "request": request, "page": "admin", "user": user,
        "items": items, "total": total, "current_page": page,
        "total_pages": (total + PAGE_SIZE - 1) // PAGE_SIZE,
        "status_filter": status, "statuses": [s.value for s in StartupStatus]
    })


@ecosystem_router.post("/admin/{startup_id}/update")
async def ecosystem_admin_update(
    startup_id: str, request: Request,
    status: str = Form(...), admin_notes: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    user = await require_admin(request, db)
    result = await db.execute(select(Startup).where(Startup.id == startup_id))
    startup = result.scalar_one_or_none()
    if not startup:
        raise HTTPException(404)
    startup.status = StartupStatus(status); startup.admin_notes = admin_notes
    if status == "verified":
        startup.verified_at = datetime.utcnow()
    await db.commit()
    return RedirectResponse("/services/ecosystem/admin", status_code=302)


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE 8 — CITIZEN HELPDESK
# ═══════════════════════════════════════════════════════════════════════════════
helpdesk_router = APIRouter(prefix="/services/helpdesk", tags=["helpdesk"])

TICKET_CATEGORIES = ["Portal Issue", "Internet/Connectivity", "Email", "Password Reset", "Cloud Services", "Training", "General ICT", "Other"]


@helpdesk_router.get("", response_class=HTMLResponse)
async def helpdesk_index(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "services/helpdesk/index.html", {
        "request": request, "page": "services", "user": user,
        "categories": TICKET_CATEGORIES
    })


@helpdesk_router.get("/new", response_class=HTMLResponse)
async def helpdesk_new_form(request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    return templates.TemplateResponse(request, "services/helpdesk/new.html", {
        "request": request, "page": "services", "user": user,
        "categories": TICKET_CATEGORIES,
        "priorities": [p.value for p in TicketPriority]
    })


@helpdesk_router.post("/new")
async def helpdesk_new_submit(
    request: Request,
    category: str = Form(...), priority: str = Form(...),
    subject: str = Form(...), description: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await require_login(request, db)
    ref = gen_ref("TKT")
    ticket = Ticket(
        reference=ref, user_id=user.id,
        category=category, priority=TicketPriority(priority),
        subject=subject, description=description,
    )
    db.add(ticket); await db.commit()
    return RedirectResponse(f"/services/helpdesk/ticket/{ref}?success=1", status_code=302)


@helpdesk_router.get("/ticket/{reference}", response_class=HTMLResponse)
async def helpdesk_ticket(reference: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    result = await db.execute(select(Ticket).where(Ticket.reference == reference))
    ticket = result.scalar_one_or_none()
    if not ticket or (ticket.user_id != user.id and user.role not in {UserRole.admin, UserRole.technician}):
        raise HTTPException(404)
    replies = (await db.execute(
        select(TicketReply).where(TicketReply.ticket_id == ticket.id).order_by(TicketReply.created_at)
    )).scalars().all()
    return templates.TemplateResponse(request, "services/helpdesk/ticket.html", {
        "request": request, "page": "services", "user": user,
        "ticket": ticket, "replies": replies, "success": request.query_params.get("success")
    })


@helpdesk_router.post("/ticket/{reference}/reply")
async def helpdesk_reply(
    reference: str, request: Request,
    message: str = Form(...), db: AsyncSession = Depends(get_db),
):
    user = await require_login(request, db)
    result = await db.execute(select(Ticket).where(Ticket.reference == reference))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(404)
    reply = TicketReply(ticket_id=ticket.id, author_id=user.id, message=message)
    ticket.updated_at = datetime.utcnow()
    if ticket.status == TicketStatus.resolved:
        ticket.status = TicketStatus.in_progress
    db.add(reply); await db.commit()
    return RedirectResponse(f"/services/helpdesk/ticket/{reference}", status_code=302)


@helpdesk_router.get("/my", response_class=HTMLResponse)
async def my_tickets(request: Request, db: AsyncSession = Depends(get_db)):
    user = await require_login(request, db)
    tickets = (await db.execute(
        select(Ticket).where(Ticket.user_id == user.id).order_by(Ticket.created_at.desc())
    )).scalars().all()
    return templates.TemplateResponse(request, "services/helpdesk/my.html", {
        "request": request, "page": "services", "user": user, "tickets": tickets
    })


@helpdesk_router.get("/admin", response_class=HTMLResponse)
async def helpdesk_admin(request: Request, page: int = 1, status: str = "", priority: str = "", q: str = "", db: AsyncSession = Depends(get_db)):
    user = await require_admin(request, db)
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    if q:
        query = query.where(or_(Ticket.subject.ilike(f"%{q}%"), Ticket.reference.ilike(f"%{q}%")))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    items = (await db.execute(query.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE))).scalars().all()
    technicians = (await db.execute(
        select(User).where(User.role.in_([UserRole.technician, UserRole.admin]))
    )).scalars().all()
    return templates.TemplateResponse(request, "services/helpdesk/admin.html", {
        "request": request, "page": "admin", "user": user,
        "items": items, "total": total, "current_page": page,
        "total_pages": (total + PAGE_SIZE - 1) // PAGE_SIZE,
        "status_filter": status, "priority_filter": priority, "q": q,
        "statuses": [s.value for s in TicketStatus],
        "priorities": [p.value for p in TicketPriority],
        "technicians": technicians,
    })


@helpdesk_router.post("/admin/ticket/{ticket_id}/update")
async def helpdesk_admin_update(
    ticket_id: str, request: Request,
    status: str = Form(...), assigned_to_id: str = Form(default=""),
    resolution: str = Form(default=""), db: AsyncSession = Depends(get_db),
):
    user = await require_admin(request, db)
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(404)
    ticket.status = TicketStatus(status)
    ticket.assigned_to_id = assigned_to_id or None
    ticket.resolution = resolution or None
    ticket.updated_at = datetime.utcnow()
    if status in ("resolved", "closed"):
        ticket.resolved_at = datetime.utcnow()
    await db.commit()
    return RedirectResponse("/services/helpdesk/admin", status_code=302)


@helpdesk_router.post("/admin/ticket/{ticket_id}/reply")
async def helpdesk_admin_reply(
    ticket_id: str, request: Request,
    message: str = Form(...), is_internal: str = Form(default="false"),
    db: AsyncSession = Depends(get_db),
):
    user = await require_admin(request, db)
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(404)
    reply = TicketReply(
        ticket_id=ticket.id, author_id=user.id,
        message=message, is_internal=is_internal.lower() == "true"
    )
    ticket.updated_at = datetime.utcnow()
    db.add(reply); await db.commit()
    return RedirectResponse("/services/helpdesk/admin", status_code=302)
