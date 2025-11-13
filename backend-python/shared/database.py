"""
SHARED DATABASE CONNECTION
SQLAlchemy setup untuk semua services
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Check connection health before using
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


# =============================================================================
# DATABASE UTILITIES
# =============================================================================

def get_db():
    """
    Dependency untuk FastAPI routes
    Usage:
        @app.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Check if database connection is healthy"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def init_db():
    """Initialize database - create all tables"""
    # Import all models to register them with SQLAlchemy
    # This ensures relationships are properly configured
    try:
        from services.auth.repositories.models import UserModel, OrganizationModel
        from services.device.repositories.models import DeviceModel, DeviceTagModel, DeviceCommandModel, DeviceHealthMetricModel
        from services.device.repositories.group_models import DeviceGroupModel, DeviceGroupMemberModel
        from services.tag.repositories.models import TagModel
        from services.content.repositories.models import ContentModel
        from services.playlist.repositories.models import PlaylistModel, PlaylistItemModel, PlaylistDeviceModel, PlaylistTagModel
        from services.audit.repositories.models import AuditLogModel
        from services.rbac.repositories.models import RoleModel, PermissionModel, RolePermissionModel
        from services.session.repositories.models import SessionModel
        from services.analytics.repositories.models import AnalyticsEventModel
        from services.pms.repositories.models import PMSConnectionModel, PMSSyncLogModel, PMSRoomMappingModel
        from services.widget.repositories.models import WidgetModel
        from services.template.repositories.models import TemplateModel
        from services.translation.repositories.models import TranslationModel
        from services.schedule.repositories.models import ScheduleModel, ScheduleDeviceModel, ScheduleTagModel
        from services.weather.repositories.models import WeatherLocationModel, WeatherDataModel
    except ImportError as e:
        print(f"⚠ Warning: Could not import some models: {e}")

    Base.metadata.create_all(bind=engine)
    print(" Database tables created")


def get_db_context():
    """
    Context manager for database sessions (for background tasks)
    
    Usage:
        with get_db_context() as db:
            # Use db session
            pass
    """
    from contextlib import contextmanager
    
    @contextmanager
    def db_context():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    return db_context