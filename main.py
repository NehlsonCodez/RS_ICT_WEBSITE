"""
Rivers State ICT Department — Main FastAPI Application
Full e-government portal with 8 service modules.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uvicorn, random, string
from datetime import datetime

from app.database import init_db, get_db
from app.models.models import Registration, ContactMessage, NewsletterSubscriber

# ── Routers ───────────────────────────────────────────────────────────────────
from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.portals import router as portal_router
from app.routers.services_all import (
    infra_router, cyber_router, cloud_router,
    training_router, policy_router, ecosystem_router, helpdesk_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Rivers State ICT Department",
    description="Official e-government portal — Rivers State ICT Department",
    version="3.0.0",
    lifespan=lifespan,
)

# ── Static files & templates ──────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ── Mount routers ─────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(portal_router)
app.include_router(infra_router)
app.include_router(cyber_router)
app.include_router(cloud_router)
app.include_router(training_router)
app.include_router(policy_router)
app.include_router(ecosystem_router)
app.include_router(helpdesk_router)


# ── Pydantic schemas for API endpoints ───────────────────────────────────────
class ContactForm(BaseModel):
    first_name: str; last_name: str; email: str
    phone: Optional[str] = None; subject: str; message: str

class NewsletterForm(BaseModel):
    email: str

class RegistrationForm(BaseModel):
    first_name: str; last_name: str; email: str; phone: str
    gender: str; age_group: str; lga: str; program: str
    schedule: str; occupation: str; experience: str; referral: str


# ── Public page routes ────────────────────────────────────────────────────────
from app.dependencies.auth import get_current_user

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "index.html", {"request": request, "page": "home", "user": user})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "about.html", {"request": request, "page": "about", "user": user})

@app.get("/services", response_class=HTMLResponse)
async def services(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "services.html", {"request": request, "page": "services", "user": user})

@app.get("/programs", response_class=HTMLResponse)
async def programs(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "programs.html", {"request": request, "page": "programs", "user": user})

@app.get("/training", response_class=HTMLResponse)
async def training_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "training.html", {"request": request, "page": "training", "user": user})

@app.get("/news", response_class=HTMLResponse)
async def news(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "news.html", {"request": request, "page": "news", "user": user})

@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "gallery.html", {"request": request, "page": "gallery", "user": user})

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "contact.html", {"request": request, "page": "contact", "user": user})

@app.get("/staff", response_class=HTMLResponse)
async def staff(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "staff.html", {"request": request, "page": "staff", "user": user})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "register.html", {"request": request, "page": "register", "user": user})

@app.get("/mandate", response_class=HTMLResponse)
async def mandate(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "mandate.html", {"request": request, "page": "mandate", "user": user})

@app.get("/structure", response_class=HTMLResponse)
async def structure(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "structure.html", {"request": request, "page": "structure", "user": user})

@app.get("/resources", response_class=HTMLResponse)
async def resources(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "resources.html", {"request": request, "page": "resources", "user": user})

@app.get("/publications", response_class=HTMLResponse)
async def publications(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "resources.html", {"request": request, "page": "publications", "user": user})

@app.get("/annual-reports", response_class=HTMLResponse)
async def annual_reports(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "resources.html", {"request": request, "page": "annual-reports", "user": user})

@app.get("/transparency", response_class=HTMLResponse)
async def transparency(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "transparency.html", {"request": request, "page": "transparency", "user": user})

@app.get("/procurement", response_class=HTMLResponse)
async def procurement(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "procurement.html", {"request": request, "page": "procurement", "user": user})

@app.get("/performance", response_class=HTMLResponse)
async def performance(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "transparency.html", {"request": request, "page": "performance", "user": user})

@app.get("/foi", response_class=HTMLResponse)
async def foi(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "foi.html", {"request": request, "page": "foi", "user": user})

@app.get("/project-registration", response_class=HTMLResponse)
async def project_registration(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "project_registration.html", {"request": request, "page": "project-reg", "user": user})

@app.get("/vendor-licensing", response_class=HTMLResponse)
async def vendor_licensing(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "vendor_licensing.html", {"request": request, "page": "vendor", "user": user})

@app.get("/sitemap", response_class=HTMLResponse)
async def sitemap(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    return templates.TemplateResponse(request, "sitemap.html", {"request": request, "page": "sitemap", "user": user})


# ── Legacy API endpoints ──────────────────────────────────────────────────────
@app.post("/api/contact")
async def submit_contact(form: ContactForm, db: AsyncSession = Depends(get_db)):
    entry = ContactMessage(first_name=form.first_name, last_name=form.last_name, email=form.email, phone=form.phone, subject=form.subject, message=form.message)
    db.add(entry); await db.flush()
    return JSONResponse({"success": True, "message": "Your message has been received. We'll respond within 1–2 business days."})

@app.post("/api/newsletter")
async def subscribe_newsletter(form: NewsletterForm, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(NewsletterSubscriber).where(NewsletterSubscriber.email == form.email))).scalar_one_or_none()
    if existing:
        return JSONResponse({"success": False, "message": "You are already subscribed."})
    db.add(NewsletterSubscriber(email=form.email)); await db.flush()
    return JSONResponse({"success": True, "message": "Successfully subscribed to our newsletter!"})

@app.post("/api/register")
async def submit_registration(form: RegistrationForm, db: AsyncSession = Depends(get_db)):
    ref = "RS-ICT-" + "".join(random.choices(string.digits, k=5))
    entry = Registration(reference=ref, first_name=form.first_name, last_name=form.last_name, email=form.email, phone=form.phone, gender=form.gender, age_group=form.age_group, lga=form.lga, program=form.program, schedule=form.schedule, occupation=form.occupation, experience=form.experience, referral=form.referral)
    db.add(entry); await db.flush()
    return JSONResponse({"success": True, "reference": ref, "message": f"Application submitted! Reference: {ref}."})

@app.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    reg_count = (await db.execute(select(func.count(Registration.id)))).scalar_one()
    return {"trained": "15,000+", "lgas": 23, "programs": "40+", "instructors": "120+", "satisfaction": "98%", "registrations_today": reg_count}

@app.get("/api/search")
async def search(q: str):
    results = [
        {"title": "E-Government Portal Request", "url": "/services/portal", "type": "Service"},
        {"title": "Report Connectivity Issue", "url": "/services/infrastructure/report", "type": "Service"},
        {"title": "Report Cyber Incident", "url": "/services/cybersecurity/report", "type": "Service"},
        {"title": "Request Cloud Resources", "url": "/services/cloud/request", "type": "Service"},
        {"title": "Digital Skills Training", "url": "/services/training", "type": "Service"},
        {"title": "ICT Policy & Compliance", "url": "/services/policy", "type": "Service"},
        {"title": "Tech Ecosystem Registration", "url": "/services/ecosystem", "type": "Service"},
        {"title": "Submit Helpdesk Ticket", "url": "/services/helpdesk/new", "type": "Service"},
        {"title": "Web Development Program", "url": "/programs", "type": "Program"},
        {"title": "Cybersecurity Fundamentals", "url": "/programs", "type": "Program"},
        {"title": "AI & Machine Learning", "url": "/programs", "type": "Program"},
        {"title": "Budget & Appropriation", "url": "/transparency", "type": "Transparency"},
        {"title": "Procurement Opportunities", "url": "/procurement", "type": "Transparency"},
        {"title": "Freedom of Information FOI", "url": "/foi", "type": "Transparency"},
        {"title": "About the ICT Department", "url": "/about", "type": "Page"},
        {"title": "Contact Us", "url": "/contact", "type": "Page"},
    ]
    filtered = [r for r in results if q.lower() in r["title"].lower()]
    return {"results": filtered, "query": q, "count": len(filtered)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
