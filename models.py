from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import ( # type: ignore
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, DeclarativeBase # type: ignore


class Base(DeclarativeBase):
    pass


class Region(Base):
    __tablename__ = "regions"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(200), nullable=False)
    region_type: str = Column(String(50), nullable=False)  # national|state|local
    parent_id: Optional[int] = Column(Integer, ForeignKey("regions.id"), nullable=True)
    geo_code: Optional[str] = Column(String(64), nullable=True)

    parent = relationship("Region", remote_side=[id], backref="children")
    projects = relationship("Project", back_populates="region")

    def __repr__(self) -> str:
        return f"<Region id={self.id} name='{self.name}' type={self.region_type}>"


class Project(Base):
    __tablename__ = "projects"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(200), nullable=False)
    region_id: int = Column(Integer, ForeignKey("regions.id"), nullable=False)
    technology: str = Column(String(50), nullable=False)  # solar, wind, hydro, etc.
    capacity_mw: float = Column(Float, nullable=False, default=0.0)
    status: str = Column(String(50), nullable=False, default="planned")
    commissioning_date: Optional[Date] = Column(Date, nullable=True)
    owner: Optional[str] = Column(String(200), nullable=True)
    latitude: Optional[Float] = Column(Float, nullable=True)
    longitude: Optional[Float] = Column(Float, nullable=True)

    region = relationship("Region", back_populates="projects")
    measurements = relationship("Measurement", back_populates="project")
    carbon_metrics = relationship("CarbonMetric", back_populates="project")

    def __repr__(self) -> str:
        return f"<Project id={self.id} name='{self.name}' tech={self.technology} cap={self.capacity_mw}MW>"


class Measurement(Base):
    __tablename__ = "measurements"
    id: int = Column(Integer, primary_key=True)
    project_id: int = Column(Integer, ForeignKey("projects.id"), nullable=False)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    generation_mwh: float = Column(Float, nullable=False, default=0.0)

    project = relationship("Project", back_populates="measurements")

    def __repr__(self) -> str:
        return f"<Measurement project_id={self.project_id} ts={self.timestamp} gen={self.generation_mwh}MWh>"


class CarbonMetric(Base):
    __tablename__ = "carbon_metrics"
    id: int = Column(Integer, primary_key=True)
    project_id: Optional[int] = Column(Integer, ForeignKey("projects.id"), nullable=True)
    region_id: Optional[int] = Column(Integer, ForeignKey("regions.id"), nullable=True)
    period_start: Optional[Date] = Column(Date, nullable=True)
    period_end: Optional[Date] = Column(Date, nullable=True)
    metric_type: str = Column(String(100), nullable=False)  # e.g., avoided_emissions_tCO2
    value: float = Column(Float, nullable=False)
    source: Optional[str] = Column(String(200), nullable=True)
    recorded_at: datetime = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="carbon_metrics")
    region = relationship("Region")

    def __repr__(self) -> str:
        return f"<CarbonMetric type={self.metric_type} value={self.value}>"


class Target(Base):
    __tablename__ = "targets"
    id: int = Column(Integer, primary_key=True)
    region_id: int = Column(Integer, ForeignKey("regions.id"), nullable=False)
    year: int = Column(Integer, nullable=False)
    metric_type: str = Column(String(100), nullable=False)  # e.g., capacity_mw or share_pct
    value: float = Column(Float, nullable=False)
    status: str = Column(String(50), nullable=False, default="active")

    region = relationship("Region")

    __table_args__ = (UniqueConstraint("region_id", "year", "metric_type", name="u_region_year_metric"),)

    def __repr__(self) -> str:
        return f"<Target region={self.region_id} year={self.year} type={self.metric_type} val={self.value}>"


class Report(Base):
    __tablename__ = "reports"
    id: int = Column(Integer, primary_key=True)
    reporter: Optional[str] = Column(String(200), nullable=True)
    region_id: Optional[int] = Column(Integer, ForeignKey("regions.id"), nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    payload: Optional[Text] = Column(Text, nullable=True)  # JSON payload as text

    region = relationship("Region")

    def __repr__(self) -> str:
        return f"<Report id={self.id} reporter={self.reporter} created_at={self.created_at}>"
