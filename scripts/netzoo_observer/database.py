"""SQLAlchemy metadata and database construction for the observer service."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Shared declarative metadata for observer tables."""


def create_database_engine(database_url: str) -> Engine:
    """Create a production-ready engine without creating schema implicitly."""
    return create_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(engine, expire_on_commit=False)


__all__ = ["Base", "create_database_engine", "create_session_factory"]
