"""
Pytest Configuration and Shared Fixtures
Provides test database setup, fixtures, and utilities for integration tests
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models.content import Content, ContentType
from app.models.device import Device
from app.models.tag import Tag, DeviceTag
from app.models.assignment import ContentAssignment
from app.models.user import User
from app.core.device_auth import create_device_token
from app.services.anthias_service import AnthiasService


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """
    Create test database with isolated session for each test
    Uses in-memory SQLite database for fast, isolated tests
    """
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """
    Create FastAPI test client with test database
    """
    # Override get_db dependency to use test database
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


# ============================================================================
# ANTHIAS SERVICE MOCKS
# ============================================================================

@pytest.fixture
def mock_anthias_service() -> Mock:
    """
    Mock AnthiasService for testing without actual Anthias server
    """
    service = Mock(spec=AnthiasService)

    # Mock upload_asset (async)
    async def mock_upload(file, name=None, duration=10, is_enabled=True):
        return {
            "asset_id": "test_asset_123",
            "name": name or file.filename,
            "uri": f"/data/screenly_assets/{file.filename}",
            "file_size": 1024000,
            "mimetype": "image" if "image" in file.content_type else "video"
        }

    service.upload_asset = AsyncMock(side_effect=mock_upload)

    # Mock delete_asset (async)
    async def mock_delete(asset_id: str):
        return {"success": True, "asset_id": asset_id}

    service.delete_asset = AsyncMock(side_effect=mock_delete)

    # Mock get_asset (async)
    async def mock_get(asset_id: str):
        return {
            "asset_id": asset_id,
            "uri": f"/data/screenly_assets/test_{asset_id}.jpg",
            "name": f"Test Asset {asset_id}",
            "mimetype": "image"
        }

    service.get_asset = AsyncMock(side_effect=mock_get)

    return service


@pytest.fixture
def mock_anthias_unavailable() -> Mock:
    """
    Mock AnthiasService that simulates server unavailability
    """
    service = Mock(spec=AnthiasService)

    # All methods raise connection error
    async def mock_error(*args, **kwargs):
        raise Exception("Connection to Anthias server failed")

    service.upload_asset = AsyncMock(side_effect=mock_error)
    service.delete_asset = AsyncMock(side_effect=mock_error)
    service.get_asset = AsyncMock(side_effect=mock_error)

    return service


# ============================================================================
# MODEL FIXTURES
# ============================================================================

@pytest.fixture
def sample_content(test_db: Session) -> Content:
    """
    Create sample content in test database
    """
    content = Content(
        title="Test Video",
        description="Test video content",
        content_type=ContentType.VIDEO,
        anthias_url="http://anthias:8000/api/v1/assets/test_asset_123",
        anthias_asset_id="test_asset_123",
        anthias_file_uri="/data/screenly_assets/test_video.mp4",
        duration=15,
        file_size=2048000,
        mime_type="video/mp4",
        resolution="1920x1080",
        width=1920,
        height=1080,
        is_active=True,
        is_template=False
    )
    test_db.add(content)
    test_db.commit()
    test_db.refresh(content)
    return content


@pytest.fixture
def sample_device(test_db: Session) -> Device:
    """
    Create sample device in test database
    """
    device = Device(
        device_name="Test TV 001",
        activation_code="ABC123",
        status="active",
        device_type="webos_tv",
        model_name="LG OLED55",
        screen_resolution="1920x1080"
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    return device


@pytest.fixture
def sample_tag(test_db: Session) -> Tag:
    """
    Create sample tag in test database
    """
    tag = Tag(
        name="Lobby Screens",
        description="All screens in lobby area",
        color="#FF5733"
    )
    test_db.add(tag)
    test_db.commit()
    test_db.refresh(tag)
    return tag


@pytest.fixture
def sample_user(test_db: Session) -> User:
    """
    Create sample user in test database
    """
    from app.core.security import get_password_hash

    user = User(
        username="testadmin",
        email="admin@test.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test Admin",
        is_active=True,
        is_superuser=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def content_with_assignment(test_db: Session, sample_content: Content, sample_device: Device) -> ContentAssignment:
    """
    Create content assignment linking content to device
    """
    assignment = ContentAssignment(
        content_id=sample_content.id,
        device_id=sample_device.id,
        priority=1
    )
    test_db.add(assignment)
    test_db.commit()
    test_db.refresh(assignment)
    return assignment


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture
def device_token(sample_device: Device) -> str:
    """
    Generate valid JWT token for sample device
    """
    return create_device_token(sample_device.id)


@pytest.fixture
def device_auth_headers(device_token: str) -> dict:
    """
    Create Authorization headers with device JWT token
    """
    return {
        "Authorization": f"Bearer {device_token}"
    }


@pytest.fixture
def expired_device_token(sample_device: Device) -> str:
    """
    Generate expired JWT token for testing token expiration
    """
    from datetime import timedelta
    return create_device_token(sample_device.id, expires_delta=timedelta(seconds=-1))


# ============================================================================
# UPLOAD FILE FIXTURES
# ============================================================================

@pytest.fixture
def mock_image_file() -> Mock:
    """
    Mock UploadFile for image testing
    """
    from fastapi import UploadFile
    from io import BytesIO

    file = Mock(spec=UploadFile)
    file.filename = "test_image.jpg"
    file.content_type = "image/jpeg"
    file.read = AsyncMock(return_value=b"fake_image_data" * 1000)
    file.file = BytesIO(b"fake_image_data" * 1000)

    return file


@pytest.fixture
def mock_video_file() -> Mock:
    """
    Mock UploadFile for video testing
    """
    from fastapi import UploadFile
    from io import BytesIO

    file = Mock(spec=UploadFile)
    file.filename = "test_video.mp4"
    file.content_type = "video/mp4"
    file.read = AsyncMock(return_value=b"fake_video_data" * 10000)
    file.file = BytesIO(b"fake_video_data" * 10000)

    return file


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def mock_request() -> Mock:
    """
    Mock FastAPI Request object
    """
    request = Mock()
    request.state.request_id = "test-request-123"
    return request


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_db(test_db: Session):
    """
    Auto-cleanup fixture that runs after each test
    Ensures clean state between tests
    """
    yield
    # Rollback any uncommitted changes
    test_db.rollback()
    # Clear all data
    for table in reversed(Base.metadata.sorted_tables):
        test_db.execute(table.delete())
    test_db.commit()
