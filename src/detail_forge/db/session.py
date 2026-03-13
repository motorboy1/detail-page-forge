"""Database session management for detail_forge."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from detail_forge.db.models import Base


class DatabaseManager:
    """Manages SQLite database connections and sessions."""

    def __init__(self, db_url: str = "sqlite:///detail_forge.db") -> None:
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Create all tables."""
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def drop_tables(self) -> None:
        """Drop all tables (for testing)."""
        Base.metadata.drop_all(self.engine)
