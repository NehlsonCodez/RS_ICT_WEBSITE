# Rivers State ICT Department — Full E-Government Portal

**FastAPI + SQLAlchemy (async) + SQLite + Jinja2**

A fully functional government services portal with 8 complete service modules, role-based
authentication, citizen/admin dashboards, and persistent database-backed workflows for every
service described in the Ministry's service catalogue.

---

## What This Is

Every service on the `/services` page is now a **real, working application** — not an
informational card. Citizens and agencies can register, log in, submit requests, track status,
and reply to support threads. Admins have dedicated management consoles for every module with
search, filtering, pagination, and status workflows.

---

## Architecture

```
app/
├── database.py              # Async SQLAlchemy engine, session, auto-seed on startup
├── models/
│   └── models.py             # All ORM models (Users + 8 service modules, ~30 tables)
├── schemas/
│   └── schemas.py            # Pydantic request/response schemas
├── dependencies/
│   └── auth.py                # Session auth (bcrypt + itsdangerous signed cookies)
├── routers/
│   ├── auth.py                 # Register / Login / Logout / Profile
│   ├── dashboard.py             # Citizen dashboard + Admin overview
│   ├── portals.py                # Service 1: E-Government Portal Management
│   └── services_all.py            # Services 2–8 (Infra, Cyber, Cloud, Training,
│                                     Policy, Ecosystem, Helpdesk)
├── templates/
│   ├── auth/                  # login.html, register.html, profile.html
│   ├── dashboard/              # citizen.html
│   ├── admin/                   # dashboard.html (admin overview)
│   └── services/
│       ├── portal/               # index, request, track, admin
│       ├── infrastructure/        # index, report, track, admin
│       ├── cybersecurity/          # index, report, track, advisories, admin
│       ├── cloud/                   # index, request, track, admin
│       ├── training/                 # index, course, track, my, admin
│       ├── policy/                    # index, compliance, track, admin
│       ├── ecosystem/                  # index, register, profile, admin
│       └── helpdesk/                    # index, new, ticket, my, admin
└── static/
    ├── css/main.css            # Full design system incl. forms, badges, modals
    ├── js/main.js               # Nav, search, newsletter, counters, reveal
    └── images/                   # Real department photography
```

---

## The 8 Service Modules

| # | Service | Citizen Can | Admin Can |
|---|---|---|---|
| 1 | **E-Government Portal Management** | Browse live portals, request new portal, track approval | Review, approve/reject/deploy, audit log |
| 2 | **ICT Infrastructure & Connectivity** | Report outages, request Wi-Fi/fibre, track status | Assign engineers, update progress, view stats |
| 3 | **Cybersecurity & Data Protection** | Report incidents (phishing, malware, breach...), read advisories | Triage severity, investigate, resolve, publish advisories |
| 4 | **Government Cloud & Data Centre** | Request VMs/storage/DB hosting with specs | Approve, provision, track allocations |
| 5 | **Digital Skills Training** | Browse 8 courses, enrol in sessions, track enrollment | Create courses, manage cohorts, issue certificates |
| 6 | **ICT Policy & Standards** | Browse policies, submit compliance requests | Publish policies, review compliance, issue decisions |
| 7 | **Tech Ecosystem Development** | Register startup/hub, browse public directory | Verify/reject registrations |
| 8 | **Citizen Digital Helpdesk** | Submit tickets, reply, track status | Assign technicians, reply, resolve, escalate |

Every module has: real database persistence, reference-numbered tracking (e.g. `PRT-123456`,
`TKT-789012`), status workflows matching the original spec, and a dedicated admin console with
search + filter + pagination.

---

## Authentication & Roles

Session-based auth using signed cookies (`itsdangerous`) — no JWT complexity needed for a
server-rendered Jinja2 app. Passwords hashed with `bcrypt` directly (not via `passlib`, to avoid
a known passlib/bcrypt version incompatibility).

**Roles:** `citizen`, `agency`, `admin`, `technician`, `analyst`, `engineer`

A default admin account is auto-created on first startup:
```
Email:    admin@ict.riversstate.gov.ng
Password: Admin@2024
```
**Change this password immediately in production.**

---

## Setup & Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

On first run, the app automatically:
1. Creates all ~30 database tables
2. Seeds a default admin account
3. Seeds 8 sample training courses
4. Seeds 1 published security advisory
5. Seeds 3 sample government portals

Visit `http://localhost:8000`.

---

## Database

SQLite via `aiosqlite`, fully async via SQLAlchemy 2.x ORM. ~30 tables covering:

- **Auth:** `users`
- **Service 1:** `portal_requests`, `portals`, `audit_logs`
- **Service 2:** `infrastructure_requests`, `engineer_assignments`
- **Service 3:** `incidents`, `evidence`, `security_advisories`
- **Service 4:** `cloud_requests`, `cloud_allocations`
- **Service 5:** `courses`, `training_sessions`, `enrollments`, `certificates`
- **Service 6:** `policies`, `policy_versions`, `compliance_requests`
- **Service 7:** `startups`, `grant_applications`
- **Service 8:** `tickets`, `ticket_replies`, `ticket_attachments`
- **Legacy:** `registrations`, `contact_messages`, `newsletter_subscribers`

To switch to PostgreSQL: change `DATABASE_URL` in `app/database.py` to a `postgresql+asyncpg://`
connection string and add `asyncpg` to requirements. No other code changes needed — SQLAlchemy
abstracts the engine.

---

## Deployment (Railway / Render)

Same as before — see `railway.json` / `render.yaml`. Set the `DATA_DIR` environment variable to
your persistent volume mount path so `rs_ict.db` survives redeploys.

---

*Rivers State ICT Department · Ministry of Science, Technology & Innovation*
*Aba Expressway, Port Harcourt, Rivers State, Nigeria*
