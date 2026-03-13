"""SQLAlchemy ORM models for detail_forge."""

import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Template(Base):
    """Stored template metadata."""

    __tablename__ = "templates"

    id = Column(String, primary_key=True)
    section_type = Column(String, nullable=False, default="hero")
    category = Column(String, default="")
    d1000_principles = Column(JSON, default=list)
    html_path = Column(String, default="")
    thumbnail_path = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    def __repr__(self) -> str:
        return f"<Template(id={self.id!r}, section_type={self.section_type!r})>"


class Generation(Base):
    """Record of a page generation run."""

    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String, nullable=False)
    template_ids = Column(JSON, default=list)
    theme_name = Column(String, default="classic_trust")
    quality_score = Column(Float, default=0.0)
    generation_time_ms = Column(Integer, default=0)
    output_path = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Generation(id={self.id!r}, product_name={self.product_name!r})>"


class User(Base):
    """User account (for future multi-user support)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self) -> str:
        return f"<User(id={self.id!r}, email={self.email!r})>"
