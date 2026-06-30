import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.models import Base

_data_dir = os.environ.get("DATA_DIR", ".")
DATABASE_URL = f"sqlite+aiosqlite:///{_data_dir}/rs_ict.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db():
    """Create all tables and seed default admin on first run."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_admin()
    await _seed_demo_data()


async def _seed_admin():
    from sqlalchemy import select
    from app.models.models import User, UserRole
    from app.dependencies.auth import hash_password
    async with AsyncSessionLocal() as db:
        existing = (await db.execute(
            select(User).where(User.email == "admin@ict.riversstate.gov.ng")
        )).scalar_one_or_none()
        if not existing:
            admin = User(
                full_name="ICT Department Admin",
                email="admin@ict.riversstate.gov.ng",
                hashed_password=hash_password("Admin@2024"),
                role=UserRole.admin,
                is_active=True,
                is_verified=True,
            )
            db.add(admin)
            await db.commit()
            print("✅ Default admin created: admin@ict.riversstate.gov.ng / Admin@2024")


async def _seed_demo_data():
    """Seed sample courses and a published advisory if DB is empty."""
    from sqlalchemy import select, func
    from app.models.models import Course, SecurityAdvisory, IncidentSeverity, Portal
    from datetime import datetime
    async with AsyncSessionLocal() as db:
        # Seed courses
        count = (await db.execute(select(func.count(Course.id)))).scalar_one()
        if count == 0:
            courses = [
                Course(title="Computer Appreciation & Office Suite", category="Computer Basics",
                       description="Master Windows OS, Microsoft Office 365, internet basics, and accessing e-government services.", duration_weeks=4, fee=0, is_free=True, level="Beginner"),
                Course(title="Digital Literacy for Everyday Life", category="Digital Literacy",
                       description="Mobile banking, WhatsApp Business, online safety, NIN/BVN registration, and government digital services.", duration_weeks=3, fee=0, is_free=True, level="Beginner"),
                Course(title="Web Development (HTML, CSS & JavaScript)", category="Web Development",
                       description="Build modern responsive websites. Graduate with a portfolio of three live projects.", duration_weeks=8, fee=5000, is_free=False, level="Intermediate"),
                Course(title="Data Analysis with Excel & Power BI", category="Data Science",
                       description="Transform raw data into actionable insights using Excel, Power Query, and Power BI dashboards.", duration_weeks=6, fee=5000, is_free=False, level="Intermediate"),
                Course(title="Graphic Design & Digital Marketing", category="Digital Marketing",
                       description="Design professional graphics and run digital marketing campaigns using Canva, Instagram and Google Ads.", duration_weeks=6, fee=5000, is_free=False, level="Intermediate"),
                Course(title="Cybersecurity Fundamentals", category="Cybersecurity",
                       description="Industry-aligned security training aligned with CompTIA Security+ objectives.", duration_weeks=10, fee=15000, is_free=False, level="Advanced"),
                Course(title="AI & Machine Learning Basics", category="Artificial Intelligence",
                       description="Python for data science, ML fundamentals, and AI productivity tools.", duration_weeks=8, fee=15000, is_free=False, level="Advanced"),
                Course(title="Cloud Computing (AWS & Azure)", category="Cloud Computing",
                       description="Prepare for AWS Cloud Practitioner or Microsoft Azure Fundamentals certification.", duration_weeks=10, fee=20000, is_free=False, level="Advanced"),
            ]
            for c in courses:
                db.add(c)
            await db.commit()
            print(f"✅ Seeded {len(courses)} courses")

        # Seed security advisory
        adv_count = (await db.execute(select(func.count(SecurityAdvisory.id)))).scalar_one()
        if adv_count == 0:
            advisory = SecurityAdvisory(
                title="Advisory: Phishing Campaigns Targeting Government Email Accounts",
                content="The RS ICT Security Operations Centre has detected a wave of sophisticated phishing emails targeting @riversstate.gov.ng accounts. These emails appear to come from trusted internal senders and request credential verification via fake portals. Staff are advised NOT to click links in unsolicited emails, verify sender addresses carefully, and report suspicious emails to cert@ict.riversstate.gov.ng immediately.",
                severity=IncidentSeverity.high,
                is_published=True,
                published_at=datetime.utcnow(),
                author="RS ICT Security Operations Centre",
            )
            db.add(advisory)
            await db.commit()
            print("✅ Seeded security advisory")

        # Seed sample portals
        portal_count = (await db.execute(select(func.count(Portal.id)))).scalar_one()
        if portal_count == 0:
            portals = [
                Portal(name="Rivers State Integrated Payroll System", url="https://ippis.riversstate.gov.ng", ministry="Ministry of Finance", description="Manage civil servant payroll, leave, and HR records.", category="HR & Payroll", is_active=True, launched_at=datetime(2022, 3, 1)),
                Portal(name="Rivers State Land Registry Portal", url="https://lands.riversstate.gov.ng", ministry="Ministry of Lands", description="Search land records, apply for C of O, and track title documentation.", category="Land & Housing", is_active=True, launched_at=datetime(2023, 6, 15)),
                Portal(name="RS Business Registration Portal", url="https://business.riversstate.gov.ng", ministry="Ministry of Commerce", description="Register businesses, obtain permits, and manage compliance online.", category="Business Services", is_active=True, launched_at=datetime(2024, 1, 10)),
            ]
            for p in portals:
                db.add(p)
            await db.commit()
            print(f"✅ Seeded {len(portals)} portals")


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
