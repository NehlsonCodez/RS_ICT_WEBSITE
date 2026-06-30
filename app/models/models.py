"""All SQLAlchemy ORM models for the RS ICT Department portal."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, Enum, Float, BigInteger
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


def gen_uuid() -> str:
    return str(uuid.uuid4())


# ── Enums ─────────────────────────────────────────────────────────────────────
class UserRole(str, enum.Enum):
    citizen = "citizen"; agency = "agency"; admin = "admin"
    technician = "technician"; analyst = "analyst"; engineer = "engineer"

class PortalStatus(str, enum.Enum):
    pending = "pending"; under_review = "under_review"; approved = "approved"
    deployed = "deployed"; rejected = "rejected"

class InfraStatus(str, enum.Enum):
    submitted = "submitted"; assigned = "assigned"
    in_progress = "in_progress"; completed = "completed"

class IncidentSeverity(str, enum.Enum):
    low = "low"; medium = "medium"; high = "high"; critical = "critical"

class IncidentStatus(str, enum.Enum):
    reported = "reported"; investigating = "investigating"
    contained = "contained"; resolved = "resolved"; closed = "closed"

class CloudStatus(str, enum.Enum):
    submitted = "submitted"; approved = "approved"; provisioning = "provisioning"
    active = "active"; suspended = "suspended"; completed = "completed"

class EnrollmentStatus(str, enum.Enum):
    applied = "applied"; shortlisted = "shortlisted"; admitted = "admitted"
    attending = "attending"; completed = "completed"; rejected = "rejected"

class PolicyStatus(str, enum.Enum):
    draft = "draft"; active = "active"; archived = "archived"

class ComplianceStatus(str, enum.Enum):
    submitted = "submitted"; under_review = "under_review"; approved = "approved"
    review_required = "review_required"; rejected = "rejected"

class StartupStatus(str, enum.Enum):
    pending = "pending"; verified = "verified"; rejected = "rejected"

class TicketStatus(str, enum.Enum):
    open = "open"; assigned = "assigned"; pending = "pending"
    in_progress = "in_progress"; resolved = "resolved"; closed = "closed"

class TicketPriority(str, enum.Enum):
    low = "low"; medium = "medium"; high = "high"; critical = "critical"


# ── AUTH ──────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(200), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    phone = Column(String(20))
    hashed_password = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.citizen, nullable=False)
    agency_name = Column(String(200))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    portal_requests = relationship("PortalRequest", back_populates="user")
    infra_requests = relationship("InfrastructureRequest", back_populates="user")
    incidents = relationship("Incident", back_populates="reporter", foreign_keys="Incident.user_id")
    cloud_requests = relationship("CloudRequest", back_populates="user")
    enrollments = relationship("Enrollment", back_populates="user")
    compliance_requests = relationship("ComplianceRequest", back_populates="user")
    startups = relationship("Startup", back_populates="owner")
    tickets = relationship("Ticket", foreign_keys="Ticket.user_id", back_populates="user")


# ── EXISTING ──────────────────────────────────────────────────────────────────
class Registration(Base):
    __tablename__ = "registrations"
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(20), unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    gender = Column(String(20)); age_group = Column(String(20)); lga = Column(String(100))
    program = Column(String(200), nullable=False); schedule = Column(String(50))
    occupation = Column(String(200)); experience = Column(String(50)); referral = Column(String(100))
    submitted_at = Column(DateTime, default=datetime.utcnow)

class ContactMessage(Base):
    __tablename__ = "contact_messages"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False); last_name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False); phone = Column(String(20))
    subject = Column(String(300), nullable=False); message = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow); is_read = Column(Boolean, default=False)

class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, nullable=False)
    subscribed_at = Column(DateTime, default=datetime.utcnow); is_active = Column(Boolean, default=True)


# ── SERVICE 1: E-GOVERNMENT ───────────────────────────────────────────────────
class PortalRequest(Base):
    __tablename__ = "portal_requests"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    reference = Column(String(20), unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    ministry = Column(String(200), nullable=False); portal_name = Column(String(200), nullable=False)
    target_domain = Column(String(200)); description = Column(Text, nullable=False)
    contact_officer = Column(String(200), nullable=False); contact_email = Column(String(200), nullable=False)
    phone = Column(String(20)); purpose = Column(Text, nullable=False)
    status = Column(Enum(PortalStatus), default=PortalStatus.pending)
    admin_notes = Column(Text)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="portal_requests")
    audit_logs = relationship("AuditLog", back_populates="portal_request")

class Portal(Base):
    __tablename__ = "portals"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(200), nullable=False); url = Column(String(300), nullable=False)
    ministry = Column(String(200), nullable=False); description = Column(Text)
    category = Column(String(100)); is_active = Column(Boolean, default=True)
    launched_at = Column(DateTime); created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    portal_request_id = Column(String(36), ForeignKey("portal_requests.id"))
    action = Column(String(100), nullable=False); performed_by = Column(String(200))
    notes = Column(Text); created_at = Column(DateTime, default=datetime.utcnow)
    portal_request = relationship("PortalRequest", back_populates="audit_logs")


# ── SERVICE 2: INFRASTRUCTURE ─────────────────────────────────────────────────
class InfrastructureRequest(Base):
    __tablename__ = "infrastructure_requests"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    reference = Column(String(20), unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    lga = Column(String(100), nullable=False); community = Column(String(200), nullable=False)
    institution = Column(String(200)); gps_lat = Column(Float); gps_lng = Column(Float)
    issue_type = Column(String(100), nullable=False); description = Column(Text, nullable=False)
    status = Column(Enum(InfraStatus), default=InfraStatus.submitted)
    admin_notes = Column(Text)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    user = relationship("User", back_populates="infra_requests")
    assignments = relationship("EngineerAssignment", back_populates="request")

class EngineerAssignment(Base):
    __tablename__ = "engineer_assignments"
    id = Column(Integer, primary_key=True)
    request_id = Column(String(36), ForeignKey("infrastructure_requests.id"))
    engineer_name = Column(String(200), nullable=False); engineer_email = Column(String(200))
    notes = Column(Text); assigned_at = Column(DateTime, default=datetime.utcnow)
    request = relationship("InfrastructureRequest", back_populates="assignments")


# ── SERVICE 3: CYBERSECURITY ──────────────────────────────────────────────────
class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    reference = Column(String(20), unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    incident_type = Column(String(100), nullable=False)
    severity = Column(Enum(IncidentSeverity), default=IncidentSeverity.medium)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.reported)
    title = Column(String(300), nullable=False); description = Column(Text, nullable=False)
    affected_system = Column(String(200)); affected_agency = Column(String(200))
    analyst_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    analyst_notes = Column(Text); reported_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    reporter = relationship("User", foreign_keys=[user_id], back_populates="incidents")
    analyst = relationship("User", foreign_keys=[analyst_id])
    evidence_files = relationship("Evidence", back_populates="incident")

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True)
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False)
    filename = Column(String(300), nullable=False); file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger); uploaded_at = Column(DateTime, default=datetime.utcnow)
    incident = relationship("Incident", back_populates="evidence_files")

class SecurityAdvisory(Base):
    __tablename__ = "security_advisories"
    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=False); content = Column(Text, nullable=False)
    severity = Column(Enum(IncidentSeverity), default=IncidentSeverity.medium)
    is_published = Column(Boolean, default=False); published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow); author = Column(String(200))


# ── SERVICE 4: CLOUD ──────────────────────────────────────────────────────────
class CloudRequest(Base):
    __tablename__ = "cloud_requests"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    reference = Column(String(20), unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    agency_name = Column(String(200), nullable=False); service_type = Column(String(100), nullable=False)
    cpu_cores = Column(Integer); ram_gb = Column(Integer); storage_gb = Column(Integer)
    purpose = Column(Text, nullable=False); expected_users = Column(Integer)
    status = Column(Enum(CloudStatus), default=CloudStatus.submitted)
    admin_notes = Column(Text)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="cloud_requests")
    allocations = relationship("CloudAllocation", back_populates="request")

class CloudAllocation(Base):
    __tablename__ = "cloud_allocations"
    id = Column(Integer, primary_key=True)
    request_id = Column(String(36), ForeignKey("cloud_requests.id"))
    server_id = Column(String(100)); ip_address = Column(String(50))
    notes = Column(Text); allocated_at = Column(DateTime, default=datetime.utcnow)
    request = relationship("CloudRequest", back_populates="allocations")


# ── SERVICE 5: TRAINING ───────────────────────────────────────────────────────
class Course(Base):
    __tablename__ = "courses"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(300), nullable=False); category = Column(String(100), nullable=False)
    description = Column(Text); duration_weeks = Column(Integer)
    fee = Column(Float, default=0.0); is_free = Column(Boolean, default=True)
    level = Column(String(50)); is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sessions = relationship("TrainingSession", back_populates="course")

class TrainingSession(Base):
    __tablename__ = "training_sessions"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=False)
    cohort_name = Column(String(100), nullable=False); start_date = Column(DateTime)
    end_date = Column(DateTime); schedule = Column(String(100))
    venue = Column(String(200)); capacity = Column(Integer, default=30)
    is_open = Column(Boolean, default=True)
    course = relationship("Course", back_populates="sessions")
    enrollments = relationship("Enrollment", back_populates="session")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    reference = Column(String(20), unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("training_sessions.id"), nullable=False)
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.applied)
    admin_notes = Column(Text); applied_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="enrollments")
    session = relationship("TrainingSession", back_populates="enrollments")
    certificate = relationship("Certificate", back_populates="enrollment", uselist=False)

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    enrollment_id = Column(String(36), ForeignKey("enrollments.id"), unique=True)
    certificate_number = Column(String(50), unique=True)
    issued_at = Column(DateTime, default=datetime.utcnow)
    enrollment = relationship("Enrollment", back_populates="certificate")


# ── SERVICE 6: POLICY ─────────────────────────────────────────────────────────
class Policy(Base):
    __tablename__ = "policies"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    title = Column(String(300), nullable=False); category = Column(String(100))
    description = Column(Text); status = Column(Enum(PolicyStatus), default=PolicyStatus.active)
    created_at = Column(DateTime, default=datetime.utcnow)
    versions = relationship("PolicyVersion", back_populates="policy")
    compliance_requests = relationship("ComplianceRequest", back_populates="policy")

class PolicyVersion(Base):
    __tablename__ = "policy_versions"
    id = Column(Integer, primary_key=True)
    policy_id = Column(String(36), ForeignKey("policies.id"), nullable=False)
    version_number = Column(String(20), nullable=False); file_path = Column(String(500))
    file_size = Column(BigInteger); notes = Column(Text)
    published_at = Column(DateTime, default=datetime.utcnow)
    policy = relationship("Policy", back_populates="versions")

class ComplianceRequest(Base):
    __tablename__ = "compliance_requests"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    reference = Column(String(20), unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    policy_id = Column(String(36), ForeignKey("policies.id"), nullable=True)
    agency_name = Column(String(200), nullable=False)
    procurement_title = Column(String(300), nullable=False)
    specifications = Column(Text, nullable=False); estimated_value = Column(Float)
    status = Column(Enum(ComplianceStatus), default=ComplianceStatus.submitted)
    compliance_result = Column(Text); reviewer_notes = Column(Text)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="compliance_requests")
    policy = relationship("Policy", back_populates="compliance_requests")


# ── SERVICE 7: TECH ECOSYSTEM ─────────────────────────────────────────────────
class Startup(Base):
    __tablename__ = "startups"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    company_name = Column(String(200), nullable=False, index=True)
    entity_type = Column(String(50), default="startup"); sector = Column(String(100))
    location = Column(String(200)); lga = Column(String(100))
    founding_year = Column(Integer); website = Column(String(300))
    email = Column(String(200)); phone = Column(String(20)); employees = Column(Integer)
    funding_stage = Column(String(100)); description = Column(Text)
    status = Column(Enum(StartupStatus), default=StartupStatus.pending)
    admin_notes = Column(Text); registered_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime)
    owner = relationship("User", back_populates="startups")
    grant_applications = relationship("GrantApplication", back_populates="startup")

class GrantApplication(Base):
    __tablename__ = "grant_applications"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    startup_id = Column(String(36), ForeignKey("startups.id"), nullable=False)
    grant_name = Column(String(200), nullable=False); amount_requested = Column(Float)
    purpose = Column(Text, nullable=False); status = Column(String(50), default="submitted")
    submitted_at = Column(DateTime, default=datetime.utcnow)
    startup = relationship("Startup", back_populates="grant_applications")


# ── SERVICE 8: HELPDESK ───────────────────────────────────────────────────────
class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(String(36), primary_key=True, default=gen_uuid)
    reference = Column(String(20), unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    category = Column(String(100), nullable=False)
    priority = Column(Enum(TicketPriority), default=TicketPriority.medium)
    status = Column(Enum(TicketStatus), default=TicketStatus.open)
    subject = Column(String(300), nullable=False); description = Column(Text, nullable=False)
    resolution = Column(Text); created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    user = relationship("User", foreign_keys=[user_id], back_populates="tickets")
    assignee = relationship("User", foreign_keys=[assigned_to_id])
    replies = relationship("TicketReply", back_populates="ticket")
    attachments = relationship("TicketAttachment", back_populates="ticket")

class TicketReply(Base):
    __tablename__ = "ticket_replies"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False); is_internal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    ticket = relationship("Ticket", back_populates="replies")
    author = relationship("User")

class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False)
    filename = Column(String(300), nullable=False); file_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    ticket = relationship("Ticket", back_populates="attachments")
