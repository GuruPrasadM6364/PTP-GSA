"""Simple CLI to manage the renewable DB.

Commands:
  init-db    : create database and tables
  seed       : seed sample data
  list-regions: list regions
  list-projects: list projects

This file uses the ORM in `models.py` and the helper in `db_init.py`.
"""
import argparse
from sqlalchemy import create_engine # type: ignore
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]
from models import Region, Project, CarbonMetric, Measurement, Target, Report, Base
import db_init


DB_URL = "sqlite:///renewable.db"


def list_regions(engine_url: str = DB_URL) -> None:
	engine = create_engine(engine_url, future=True)
	with Session(engine) as session:
		rows = session.query(Region).order_by(Region.region_type, Region.name).all()
		for r in rows:
			print(r)


def list_projects(engine_url: str = DB_URL) -> None:
	engine = create_engine(engine_url, future=True)
	with Session(engine) as session:
		rows = session.query(Project).order_by(Project.name).all()
		for p in rows:
			print(p)


def main():
	parser = argparse.ArgumentParser(description="Manage renewable database")
	parser.add_argument("command", choices=["init-db", "seed", "list-regions", "list-projects"], help="command to run")
	args = parser.parse_args()

	if args.command == "init-db":
		db_init.init_db(DB_URL)
	elif args.command == "seed":
		db_init.seed_sample(DB_URL)
	elif args.command == "list-regions":
		list_regions(DB_URL)
	elif args.command == "list-projects":
		list_projects(DB_URL)


if __name__ == "__main__":
	main()

