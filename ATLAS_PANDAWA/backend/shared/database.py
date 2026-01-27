"""
ATLAS_PANDAWA Backend - Database Configuration
Follows CORE-STD-01 standards (UUID, soft delete, timestamps, audit trail)
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from shared.config import settings

# Database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model for all database models
Base = declarative_base()


def get_db():
    """
    Database session dependency for FastAPI routes

    Usage:
        @router.get("/")
        async def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
