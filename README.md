# Rivers State ICT Department — Official Website

**FastAPI + Jinja2 + SQLite (SQLAlchemy async)**

Refactored version of the Rivers State ICT Department website with a real persistent SQLite database,
fully completed page content (no placeholder Jinja2 text), and clean async database architecture.

---

## What Changed in This Refactor

| Before | After |
|---|---|
| In-memory Python lists (`registrations = []`) | SQLite database via SQLAlchemy async ORM |
| Placeholder Jinja2 text on 6 pages | Real, department-specific content on all pages |
| No data persistence (lost on restart) | Data persists across server restarts |
| No DB schema | Proper tables: `registrations`, `contact_messages`, `newsletter_subscribers` |

---

## Project Structure

```
rs_ict_website/
├── main.py                        # FastAPI app, routes, API endpoints
├── requirements.txt               # Python dependencies
├── rs_ict.db                      # SQLite database (auto-created on first run)
├── app/
│   ├── __init__.py
│   ├── database.py                # Async SQLAlchemy engine & session
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py              # ORM models: Registration, ContactMessage, NewsletterSubscriber
│   ├── static/
│   │   ├── css/main.css
│   │   └── js/main.js
│   └── templates/
│       ├── base.html              # Shared layout (nav, footer, newsletter strip)
│       ├── index.html             # Home page
│       ├── about.html             # About the department
│       ├── services.html          # ICT services (8 service cards — real content)
│       ├── programs.html          # Digital skills programs by tier (real content)
│       ├── training.html          # Training center facilities & schedule (real content)
│       ├── news.html              # News articles & upcoming events (real content)
│       ├── staff.html             # Leadership profiles (real content)
│       ├── gallery.html           # Filterable photo gallery (real content)
│       ├── contact.html           # Contact form (submits to DB)
│       └── register.html          # Program registration form (submits to DB)
```

---

## Setup & Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the development server

```bash
uvicorn main:app --reload
```

The SQLite database (`rs_ict.db`) is created automatically on first startup.

### 3. Open in browser

```
http://localhost:8000
```

---

## Database

**Engine:** SQLite (file: `rs_ict.db`)  
**ORM:** SQLAlchemy 2.x with `asyncio` support (`aiosqlite` driver)

### Tables

#### `registrations`
Stores all program registration form submissions.

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| reference | VARCHAR(20) | Unique ref e.g. RS-ICT-12345 |
| first_name, last_name | VARCHAR | Applicant name |
| email, phone | VARCHAR | Contact details |
| gender, age_group, lga | VARCHAR | Demographics |
| program, schedule | VARCHAR | Chosen program & session |
| occupation, experience, referral | VARCHAR | Background info |
| submitted_at | DATETIME | UTC timestamp |

#### `contact_messages`
Stores all contact form submissions.

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| first_name, last_name, email, phone | VARCHAR | Sender details |
| subject, message | TEXT | Message content |
| submitted_at | DATETIME | UTC timestamp |
| is_read | BOOLEAN | Admin tracking flag |

#### `newsletter_subscribers`
Stores newsletter subscriptions with duplicate-email protection.

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| email | VARCHAR UNIQUE | Subscriber email |
| subscribed_at | DATETIME | UTC timestamp |
| is_active | BOOLEAN | Unsubscribe flag |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Home page |
| GET | `/about` | About the department |
| GET | `/services` | ICT services |
| GET | `/programs` | Digital skills programs |
| GET | `/training` | Training center |
| GET | `/news` | News & events |
| GET | `/gallery` | Photo gallery |
| GET | `/staff` | Leadership & staff |
| GET | `/contact` | Contact page |
| GET | `/register` | Registration form |
| POST | `/api/contact` | Submit contact form → saves to DB |
| POST | `/api/newsletter` | Subscribe to newsletter → saves to DB |
| POST | `/api/register` | Submit program registration → saves to DB |
| GET | `/api/stats` | Live stats including DB registration count |
| GET | `/api/search?q=...` | Site search |
| GET | `/docs` | FastAPI interactive docs (Swagger UI) |

---

## To Switch to PostgreSQL

1. Install `asyncpg`: `pip install asyncpg`
2. In `app/database.py`, change:
   ```python
   DATABASE_URL = "postgresql+asyncpg://user:password@localhost/rs_ict_db"
   ```
3. Remove `aiosqlite` from `requirements.txt`, add `asyncpg`.
4. The rest of the code is identical — SQLAlchemy abstracts the engine.

---

*Rivers State ICT Department · Ministry of Science, Technology & Innovation*  
*ICT House, Trans-Amadi Industrial Layout, Port Harcourt, Rivers State*
