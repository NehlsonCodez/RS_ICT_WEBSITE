from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import uvicorn
import random
import string
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import init_db, get_db
from app.models.models import Registration, ContactMessage, NewsletterSubscriber


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Rivers State ICT Department",
    description="Official website of the Rivers State ICT Department, Nigeria",
    version="2.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ─── Pydantic Schemas ──────────────────────────────────────────

class ContactForm(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    subject: str
    message: str


class NewsletterForm(BaseModel):
    email: str


class RegistrationForm(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    gender: str
    age_group: str
    lga: str
    program: str
    schedule: str
    occupation: str
    experience: str
    referral: str


# ─── Page Routes ──────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "page": "home"})


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "page": "about"})


@app.get("/services", response_class=HTMLResponse)
async def services(request: Request):
    return templates.TemplateResponse("services.html", {"request": request, "page": "services"})


@app.get("/programs", response_class=HTMLResponse)
async def programs(request: Request):
    return templates.TemplateResponse("programs.html", {"request": request, "page": "programs"})


@app.get("/training", response_class=HTMLResponse)
async def training(request: Request):
    return templates.TemplateResponse("training.html", {"request": request, "page": "training"})


@app.get("/news", response_class=HTMLResponse)
async def news(request: Request):
    return templates.TemplateResponse("news.html", {"request": request, "page": "news"})


@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request):
    return templates.TemplateResponse("gallery.html", {"request": request, "page": "gallery"})


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request, "page": "contact"})


@app.get("/staff", response_class=HTMLResponse)
async def staff(request: Request):
    return templates.TemplateResponse("staff.html", {"request": request, "page": "staff"})


@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "page": "register"})


# ─── API Endpoints ────────────────────────────────────────────

@app.post("/api/contact")
async def submit_contact(form: ContactForm, db: AsyncSession = Depends(get_db)):
    entry = ContactMessage(
        first_name=form.first_name,
        last_name=form.last_name,
        email=form.email,
        phone=form.phone,
        subject=form.subject,
        message=form.message,
    )
    db.add(entry)
    await db.flush()
    return JSONResponse({
        "success": True,
        "message": "Your message has been received. We'll respond within 1–2 business days.",
    })


@app.post("/api/newsletter")
async def subscribe_newsletter(form: NewsletterForm, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NewsletterSubscriber).where(NewsletterSubscriber.email == form.email)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return JSONResponse({"success": False, "message": "You are already subscribed."})
    sub = NewsletterSubscriber(email=form.email)
    db.add(sub)
    await db.flush()
    return JSONResponse({"success": True, "message": "Successfully subscribed to our newsletter!"})


@app.post("/api/register")
async def submit_registration(form: RegistrationForm, db: AsyncSession = Depends(get_db)):
    ref = "RS-ICT-" + "".join(random.choices(string.digits, k=5))
    entry = Registration(
        reference=ref,
        first_name=form.first_name,
        last_name=form.last_name,
        email=form.email,
        phone=form.phone,
        gender=form.gender,
        age_group=form.age_group,
        lga=form.lga,
        program=form.program,
        schedule=form.schedule,
        occupation=form.occupation,
        experience=form.experience,
        referral=form.referral,
    )
    db.add(entry)
    await db.flush()
    return JSONResponse({
        "success": True,
        "reference": ref,
        "message": f"Application submitted! Reference: {ref}. Confirmation sent to {form.email}.",
    })


@app.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    reg_count_result = await db.execute(select(func.count(Registration.id)))
    reg_count = reg_count_result.scalar_one()
    return {
        "trained": "15,000+",
        "lgas": 23,
        "programs": "40+",
        "instructors": "120+",
        "satisfaction": "98%",
        "registrations_today": reg_count,
    }


@app.get("/api/search")
async def search(q: str):
    results = [
        {"title": "Web Development Program", "url": "/programs", "type": "Program"},
        {"title": "Cybersecurity Basics", "url": "/programs", "type": "Program"},
        {"title": "Data Analysis with Python", "url": "/programs", "type": "Program"},
        {"title": "Cloud Computing Fundamentals", "url": "/programs", "type": "Program"},
        {"title": "AI Tools for Education", "url": "/programs", "type": "Program"},
        {"title": "Contact Us", "url": "/contact", "type": "Page"},
        {"title": "About the ICT Department", "url": "/about", "type": "Page"},
        {"title": "Digital Skills Training", "url": "/training", "type": "Service"},
        {"title": "E-Government Services", "url": "/services", "type": "Service"},
        {"title": "ICT Infrastructure Services", "url": "/services", "type": "Service"},
    ]
    filtered = [r for r in results if q.lower() in r["title"].lower()]
    return {"results": filtered, "query": q, "count": len(filtered)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
