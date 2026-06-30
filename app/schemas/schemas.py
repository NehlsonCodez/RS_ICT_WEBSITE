"""Pydantic v2 schemas for all service modules."""
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
from app.models.models import (
    PortalStatus, InfraStatus, IncidentSeverity, IncidentStatus,
    CloudStatus, EnrollmentStatus, ComplianceStatus, StartupStatus,
    TicketStatus, TicketPriority, UserRole
)


# ── AUTH ──────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    role: UserRole = UserRole.citizen
    agency_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ── SERVICE 1: PORTAL REQUEST ─────────────────────────────────────────────────
class PortalRequestCreate(BaseModel):
    ministry: str
    portal_name: str
    target_domain: Optional[str] = None
    description: str
    contact_officer: str
    contact_email: EmailStr
    phone: Optional[str] = None
    purpose: str


class PortalRequestUpdate(BaseModel):
    status: Optional[PortalStatus] = None
    admin_notes: Optional[str] = None


# ── SERVICE 2: INFRASTRUCTURE ─────────────────────────────────────────────────
class InfraRequestCreate(BaseModel):
    lga: str
    community: str
    institution: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    issue_type: str
    description: str


class InfraRequestUpdate(BaseModel):
    status: Optional[InfraStatus] = None
    admin_notes: Optional[str] = None


class AssignEngineerSchema(BaseModel):
    engineer_name: str
    engineer_email: Optional[str] = None
    notes: Optional[str] = None


# ── SERVICE 3: CYBERSECURITY ──────────────────────────────────────────────────
class IncidentCreate(BaseModel):
    incident_type: str
    severity: IncidentSeverity
    title: str
    description: str
    affected_system: Optional[str] = None
    affected_agency: Optional[str] = None


class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    severity: Optional[IncidentSeverity] = None
    analyst_notes: Optional[str] = None
    analyst_id: Optional[str] = None


class AdvisoryCreate(BaseModel):
    title: str
    content: str
    severity: IncidentSeverity
    author: Optional[str] = None


# ── SERVICE 4: CLOUD ──────────────────────────────────────────────────────────
class CloudRequestCreate(BaseModel):
    agency_name: str
    service_type: str
    cpu_cores: Optional[int] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    purpose: str
    expected_users: Optional[int] = None


class CloudRequestUpdate(BaseModel):
    status: Optional[CloudStatus] = None
    admin_notes: Optional[str] = None


class AllocateResourceSchema(BaseModel):
    server_id: Optional[str] = None
    ip_address: Optional[str] = None
    notes: Optional[str] = None


# ── SERVICE 5: TRAINING ───────────────────────────────────────────────────────
class CourseCreate(BaseModel):
    title: str
    category: str
    description: Optional[str] = None
    duration_weeks: Optional[int] = None
    fee: float = 0.0
    is_free: bool = True
    level: Optional[str] = None


class SessionCreate(BaseModel):
    course_id: str
    cohort_name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    schedule: Optional[str] = None
    venue: Optional[str] = None
    capacity: int = 30


class EnrollCreate(BaseModel):
    session_id: str


class EnrollmentUpdate(BaseModel):
    status: Optional[EnrollmentStatus] = None
    admin_notes: Optional[str] = None


# ── SERVICE 6: POLICY ─────────────────────────────────────────────────────────
class PolicyCreate(BaseModel):
    title: str
    category: Optional[str] = None
    description: Optional[str] = None


class ComplianceRequestCreate(BaseModel):
    agency_name: str
    procurement_title: str
    specifications: str
    estimated_value: Optional[float] = None
    policy_id: Optional[str] = None


class ComplianceUpdate(BaseModel):
    status: Optional[ComplianceStatus] = None
    compliance_result: Optional[str] = None
    reviewer_notes: Optional[str] = None


# ── SERVICE 7: ECOSYSTEM ──────────────────────────────────────────────────────
class StartupCreate(BaseModel):
    company_name: str
    entity_type: str = "startup"
    sector: Optional[str] = None
    location: Optional[str] = None
    lga: Optional[str] = None
    founding_year: Optional[int] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    employees: Optional[int] = None
    funding_stage: Optional[str] = None
    description: Optional[str] = None


class GrantApplicationCreate(BaseModel):
    startup_id: str
    grant_name: str
    amount_requested: Optional[float] = None
    purpose: str


# ── SERVICE 8: HELPDESK ───────────────────────────────────────────────────────
class TicketCreate(BaseModel):
    category: str
    priority: TicketPriority
    subject: str
    description: str


class TicketReplyCreate(BaseModel):
    message: str
    is_internal: bool = False


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    assigned_to_id: Optional[str] = None
    resolution: Optional[str] = None
