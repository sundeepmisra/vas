"""SQLAlchemy declarative base shared by authoritative persistence models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all Vasilia relational models."""

    pass
