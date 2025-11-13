"""Database initialization and seeding script.

Creates an SQLite DB called `renewable.db` in the project root, creates tables,
and inserts a few sample regions, projects, measurements, carbon metrics, and targets.
"""
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Base, Region, Project, Measurement, CarbonMetric, Target, Report, User
from werkzeug.security import generate_password_hash


DB_URL = "sqlite:///renewable.db"


def init_db(engine_url: str = DB_URL) -> None:
    engine = create_engine(engine_url, echo=False, future=True)
    Base.metadata.create_all(engine)

    # Ensure new columns exist in SQLite users table (add if missing)
    with engine.connect() as conn:
        try:
            result = conn.exec_driver_sql("PRAGMA table_info('users')")
            cols = [row[1] for row in result.fetchall()]
            if 'email' not in cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN email VARCHAR(200)")
            if 'password_hash' not in cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN password_hash VARCHAR(128)")
        except Exception:
            # If table doesn't exist yet or PRAGMA fails, ignore
            pass

    print("Created tables (if not exist) at", engine_url)


def seed_sample(engine_url: str = DB_URL) -> None:
    engine = create_engine(engine_url, echo=False, future=True)
    with Session(engine) as session:
        # Regions (hierarchy)
        country = Region(name="Exampleland", region_type="national", geo_code="EX")
        state = Region(name="State A", region_type="state", parent=country, geo_code="EX-SA")
        city = Region(name="City One", region_type="local", parent=state, geo_code="EX-SA-CO")
        session.add_all([country, state, city])
        session.flush()

        # Projects
        p1 = Project(
            name="City One Solar Park",
            region=city,
            technology="solar",
            capacity_mw=25.0,
            status="operational",
            commissioning_date=date(2023, 6, 1),
            owner="GreenPower Co",
            latitude=12.34,
            longitude=56.78,
        )

        p2 = Project(
            name="State A Wind Farm",
            region=state,
            technology="wind",
            capacity_mw=100.0,
            status="under_construction",
            owner="WindWorks",
        )

        session.add_all([p1, p2])
        session.flush()

        # Measurements (time-series)
        m1 = Measurement(project=p1, timestamp=datetime(2025, 11, 1, 12, 0), generation_mwh=50.2)
        m2 = Measurement(project=p1, timestamp=datetime(2025, 11, 1, 13, 0), generation_mwh=48.8)
        session.add_all([m1, m2])

        # Carbon metrics
        cm1 = CarbonMetric(project=p1, region=city, period_start=date(2025, 1, 1), period_end=date(2025, 12, 31), metric_type="avoided_emissions_tCO2", value=1200.5, source="estimation")
        session.add(cm1)

        # Targets
        t1 = Target(region=country, year=2030, metric_type="capacity_mw", value=5000.0, status="active")
        t2 = Target(region=state, year=2028, metric_type="share_pct", value=60.0, status="active")
        session.add_all([t1, t2])

        # Report example
        r1 = Report(reporter="Ministry of Energy", region=country, payload='{"notes": "Quarterly update"}')
        session.add(r1)

        session.commit()
        print("Seeded sample data.")
        # Add a sample user (if not exists)
        try:
            user = User(
                name="Sample User",
                phone="9876543210",
                email="sample@example.com",
                password_hash=generate_password_hash("Password1!"),
                pincode="560001",
                address="123 Example Street",
            )
            session.add(user)
            session.commit()
            print("Added sample user.")
        except Exception:
            # ignore if unique constraint fails
            session.rollback()


if __name__ == "__main__":
    init_db()
    seed_sample()
