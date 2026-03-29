"""Database engine and session helpers."""

from collections.abc import Generator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class DatabaseSessionManager:
    """Manage the application's engine and session factory."""

    def __init__(self, database_url: str) -> None:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, connect_args=connect_args, future=True)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session,
        )

    def create_tables(self) -> None:
        """Create database tables for all registered models."""

        Base.metadata.create_all(bind=self.engine)

    def dispose(self) -> None:
        """Dispose of open engine resources."""

        self.engine.dispose()


def get_db(request: Request) -> Generator[Session, None, None]:
    """Yield a database session tied to the current FastAPI app."""

    with request.app.state.db.session_factory() as session:
        yield session
