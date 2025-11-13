# Renewable DB for scalable, digital renewable deployment tracking

This repository includes a small SQLite-backed database and Python scripts to model and seed a schema focused on accelerating renewable deployment, tracking carbon metrics, and linking national targets to local implementation.

Files added:
- `models.py` : SQLAlchemy ORM models for `Region`, `Project`, `Measurement`, `CarbonMetric`, `Target`, and `Report`.
- `db_init.py` : Creates `renewable.db` and inserts sample data.
- `renewable.py` : Simple CLI to initialize and query the DB.
- `requirements.txt` : minimal Python dependencies.

Quick start

1. Create a virtualenv and install requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Initialize the database and seed sample data:

```bash
python renewable.py init-db
python renewable.py seed
```

3. List regions or projects:

```bash
python renewable.py list-regions
python renewable.py list-projects
```

Schema notes
- Regions are hierarchical so you can represent national -> state -> local.
- Projects are tied to regions and store capacity, technology, status and geo-coordinates.
- Measurements store time-series generation (MWh) per project for real-time tracking.
- CarbonMetric records avoided emissions or other carbon KPIs linked to projects or regions.
- Targets allow storing national/regional targets by year (capacity or share).

Next steps (suggested)
- Add API endpoints (FastAPI) for ingestion and querying real-time measurements.
- Add authentication and an audit trail for reported metrics.
- Add batch or streaming ingestion for measurements (e.g., Kafka or scheduled ETL).
# PTP-GSA

Project:

- Perplexity AI and Google were used to find out the data and analytics related to the problem statement, in order to help understand it better.

- Claude AI used to create the backend for login and credentials

- 