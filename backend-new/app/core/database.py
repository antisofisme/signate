"""
Database Connection & Session Management
SQLAlchemy setup for PostgreSQL
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# DATABASE ENGINE
# =============================================================================

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,  # Number of permanent connections
    max_overflow=10,  # Max number of temporary connections
    pool_pre_ping=True,  # Test connections before using
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Event listener for connection setup
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Run on every new database connection"""
    logger.debug("New database connection established")


# Event listener for connection checkout
@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Run when connection is retrieved from pool"""
    pass  # Could add ping check here if needed


# =============================================================================
# SESSION FACTORY
# =============================================================================

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# =============================================================================
# BASE CLASS FOR MODELS
# =============================================================================

# Base class for all SQLAlchemy models
Base = declarative_base()

# =============================================================================
# DEPENDENCY FOR FASTAPI
# =============================================================================

def get_db() -> Session:
    """
    Database session dependency for FastAPI

    Usage in FastAPI endpoint:
        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            # Use db here
            pass

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================================================================
# DATABASE UTILITIES
# =============================================================================

def init_db():
    """
    Initialize database - Create all tables
    Should be called on app startup

    Note: In production, use Alembic for migrations instead
    """
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def check_db_connection() -> bool:
    """
    Check if database connection is working

    Returns:
        bool: True if connected, False otherwise
    """
    try:
        # Try to execute a simple query
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


def get_db_info() -> dict:
    """
    Get database information

    Returns:
        dict: Database connection info
    """
    return {
        "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "unknown",
        "pool_size": engine.pool.size(),
        "checked_out_connections": engine.pool.checkedout(),
        "overflow_connections": engine.pool.overflow(),
        "total_connections": engine.pool.size() + engine.pool.overflow(),
    }


# =============================================================================
# CONTEXT MANAGER FOR TRANSACTIONS
# =============================================================================

class DatabaseSession:
    """
    Context manager for database sessions

    Usage:
        with DatabaseSession() as db:
            user = db.query(User).first()
    """

    def __enter__(self) -> Session:
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.db.rollback()
        self.db.close()


# =============================================================================
# ASYNC DATABASE (Optional - for async endpoints)
# =============================================================================

# Uncomment if using async SQLAlchemy
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker

# async_engine = create_async_engine(
#     settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
#     echo=settings.DEBUG,
#     pool_pre_ping=True,
# )

# AsyncSessionLocal = sessionmaker(
#     async_engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
# )

# async def get_async_db() -> AsyncSession:
#     async with AsyncSessionLocal() as session:
#         yield session
