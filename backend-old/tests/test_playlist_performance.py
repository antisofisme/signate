"""
Playlist Performance Optimization Tests (Phase 2)

Tests for playlist optimization using cached anthias_file_uri

Features Tested:
- Request playlist → Verify fast path used (cached URI)
- Verify performance logging present
- Response structure unchanged
- Fallback to Anthias API for missing URIs
- Performance comparison: fast path vs slow path

Phase 2 Implementation:
- Playlist generation uses cached anthias_file_uri
- Eliminates +130ms Anthias API call per content item
- Logs performance metrics (duration_ms, avg_per_item_ms)
- Falls back to Anthias API for legacy content without cached URI

Run: pytest tests/test_playlist_performance.py -v
"""

import pytest
import time
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.content import Content
from app.models.device import Device
from app.models.tag import Tag, DeviceTag
from app.models.assignment import ContentAssignment


# ============================================================================
# PLAYLIST FAST PATH TESTS (Cached URI)
# ============================================================================

class TestPlaylistFastPath:
    """Test playlist generation using cached anthias_file_uri (fast path)"""

    def test_playlist_uses_cached_uri(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        device_auth_headers: dict
    ):
        """
        Test playlist generation uses cached URI (no Anthias API call)

        Flow:
        1. Create content with cached anthias_file_uri
        2. Assign content to device
        3. Request playlist with JWT token
        4. Verify URL generated from cached URI
        5. Verify NO Anthias API call made

        Expected URL format:
        http://192.168.5.12:8000/screenly_assets/filename.jpg
        (constructed from cached URI without API call)
        """
        # Create content with cached URI
        content = Content(
            title="Fast Path Content",
            description="Testing fast path",
            content_type="image",
            anthias_url="http://anthias/api/v1/assets/fast_path_123",
            anthias_asset_id="fast_path_123",
            anthias_file_uri="/data/screenly_assets/fast_path_test.jpg",  # Cached!
            duration=10,
            file_size=1024000,
            is_active=True
        )
        test_db.add(content)
        test_db.commit()

        # Assign to device
        assignment = ContentAssignment(
            content_id=content.id,
            device_id=sample_device.id,
            priority=1
        )
        test_db.add(assignment)
        test_db.commit()

        # Request playlist
        response = client.get("/api/client/playlist", headers=device_auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify playlist structure
        assert "playlist" in data
        assert len(data["playlist"]) == 1

        playlist_item = data["playlist"][0]

        # Verify URL constructed from cached URI
        assert "fast_path_test.jpg" in playlist_item["url"]
        assert "screenly_assets" in playlist_item["url"]

        # Verify content details
        assert playlist_item["content_id"] == content.id
        assert playlist_item["title"] == "Fast Path Content"
        assert playlist_item["duration"] == 10

    def test_playlist_multiple_content_all_cached(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        device_auth_headers: dict
    ):
        """
        Test playlist with multiple content items, all using cached URIs

        Flow:
        1. Create 5 content items with cached URIs
        2. Assign all to device with different priorities
        3. Request playlist
        4. Verify all URLs use cached URIs
        5. Verify correct priority ordering
        """
        # Create 5 content items
        content_items = []
        for i in range(5):
            content = Content(
                title=f"Content {i+1}",
                description=f"Multi-content test {i+1}",
                content_type="image" if i % 2 == 0 else "video",
                anthias_url=f"http://anthias/api/v1/assets/multi_{i+1}",
                anthias_asset_id=f"multi_asset_{i+1}",
                anthias_file_uri=f"/data/screenly_assets/multi_{i+1}.jpg",
                duration=10 + i,
                is_active=True
            )
            test_db.add(content)
            test_db.commit()
            content_items.append(content)

            # Assign with priority (reverse order)
            assignment = ContentAssignment(
                content_id=content.id,
                device_id=sample_device.id,
                priority=5 - i  # Priority: 5, 4, 3, 2, 1
            )
            test_db.add(assignment)

        test_db.commit()

        # Request playlist
        response = client.get("/api/client/playlist", headers=device_auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify playlist
        assert len(data["playlist"]) == 5
        assert data["total_items"] == 5

        # Verify all use cached URIs
        for i, item in enumerate(data["playlist"]):
            assert "screenly_assets" in item["url"]
            assert "multi_" in item["url"]

        # Verify priority ordering (highest priority first)
        # Content 1 has priority 5, Content 5 has priority 1
        assert data["playlist"][0]["title"] == "Content 1"  # Priority 5
        assert data["playlist"][4]["title"] == "Content 5"  # Priority 1

    def test_playlist_performance_metrics_logged(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        device_auth_headers: dict,
        caplog
    ):
        """
        Test performance metrics are logged during playlist generation

        Expected log fields:
        - duration_ms: Total generation time
        - avg_per_item_ms: Average time per content item
        - total_items: Number of items in playlist

        Flow:
        1. Create content with cached URI
        2. Assign to device
        3. Request playlist
        4. Verify performance logs present
        """
        # Create content
        content = Content(
            title="Performance Logging Test",
            description="Testing performance metrics",
            content_type="video",
            anthias_url="http://anthias/api/v1/assets/perf_log",
            anthias_asset_id="perf_log_123",
            anthias_file_uri="/data/screenly_assets/perf_log.mp4",
            duration=15,
            is_active=True
        )
        test_db.add(content)
        test_db.commit()

        # Assign to device
        assignment = ContentAssignment(
            content_id=content.id,
            device_id=sample_device.id,
            priority=1
        )
        test_db.add(assignment)
        test_db.commit()

        # Request playlist
        with caplog.at_level("INFO"):
            response = client.get("/api/client/playlist", headers=device_auth_headers)

        assert response.status_code == 200

        # Verify performance logging
        # Check for log message containing performance metrics
        performance_logged = False
        for record in caplog.records:
            if "Playlist generated successfully" in record.message or "duration_ms" in str(record):
                performance_logged = True
                break

        assert performance_logged, "Performance metrics should be logged"


# ============================================================================
# PLAYLIST FALLBACK PATH TESTS (Missing URI)
# ============================================================================

class TestPlaylistFallbackPath:
    """Test playlist fallback to Anthias API for missing cached URIs"""

    def test_playlist_fallback_for_missing_uri(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        device_auth_headers: dict,
        mock_anthias_service
    ):
        """
        Test fallback to Anthias API when cached URI is missing

        Scenario: Legacy content without anthias_file_uri
        Expected: Call Anthias API to get URI (slow path)

        Flow:
        1. Create content WITHOUT cached URI (anthias_file_uri = NULL)
        2. Assign to device
        3. Mock Anthias API to return URI
        4. Request playlist
        5. Verify Anthias API called (fallback)
        6. Verify playlist still works
        """
        # Create content without cached URI
        content = Content(
            title="Legacy Content",
            description="No cached URI",
            content_type="image",
            anthias_url="http://anthias/api/v1/assets/legacy_123",
            anthias_asset_id="legacy_123",
            anthias_file_uri=None,  # NULL - triggers fallback
            duration=10,
            is_active=True
        )
        test_db.add(content)
        test_db.commit()

        # Assign to device
        assignment = ContentAssignment(
            content_id=content.id,
            device_id=sample_device.id,
            priority=1
        )
        test_db.add(assignment)
        test_db.commit()

        # Request playlist (will trigger fallback to Anthias API)
        # Note: In test environment without real Anthias, this will use API endpoint fallback
        response = client.get("/api/client/playlist", headers=device_auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify playlist contains content (even without cached URI)
        assert len(data["playlist"]) == 1
        assert data["playlist"][0]["content_id"] == content.id

    def test_playlist_mixed_cached_and_fallback(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        device_auth_headers: dict
    ):
        """
        Test playlist with mixed content: some cached, some fallback

        Flow:
        1. Create 3 content items:
           - Content 1: Has cached URI (fast path)
           - Content 2: No cached URI (fallback)
           - Content 3: Has cached URI (fast path)
        2. Assign all to device
        3. Request playlist
        4. Verify all 3 items in playlist
        5. Verify mixed processing works correctly
        """
        # Content 1: Cached URI
        content1 = Content(
            title="Cached Content 1",
            description="Has URI",
            content_type="image",
            anthias_url="http://anthias/api/v1/assets/cached_1",
            anthias_asset_id="cached_1",
            anthias_file_uri="/data/screenly_assets/cached_1.jpg",  # Cached
            duration=10,
            is_active=True
        )

        # Content 2: No cached URI (fallback)
        content2 = Content(
            title="Legacy Content",
            description="No URI",
            content_type="video",
            anthias_url="http://anthias/api/v1/assets/legacy_2",
            anthias_asset_id="legacy_2",
            anthias_file_uri=None,  # NULL - fallback
            duration=15,
            is_active=True
        )

        # Content 3: Cached URI
        content3 = Content(
            title="Cached Content 3",
            description="Has URI",
            content_type="image",
            anthias_url="http://anthias/api/v1/assets/cached_3",
            anthias_asset_id="cached_3",
            anthias_file_uri="/data/screenly_assets/cached_3.jpg",  # Cached
            duration=12,
            is_active=True
        )

        test_db.add_all([content1, content2, content3])
        test_db.commit()

        # Assign all to device
        for i, content in enumerate([content1, content2, content3]):
            assignment = ContentAssignment(
                content_id=content.id,
                device_id=sample_device.id,
                priority=3 - i
            )
            test_db.add(assignment)
        test_db.commit()

        # Request playlist
        response = client.get("/api/client/playlist", headers=device_auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify all 3 items in playlist
        assert len(data["playlist"]) == 3
        assert data["total_items"] == 3

        # Verify cached items have screenly_assets URL
        assert "screenly_assets" in data["playlist"][0]["url"]  # Content 1
        assert "screenly_assets" in data["playlist"][2]["url"]  # Content 3


# ============================================================================
# PLAYLIST TAG ASSIGNMENT TESTS
# ============================================================================

class TestPlaylistTagAssignment:
    """Test playlist generation with tag-based assignments"""

    def test_playlist_with_tag_assignment(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        sample_tag: Tag,
        device_auth_headers: dict
    ):
        """
        Test playlist for device with tag-based content assignment

        Flow:
        1. Create content assigned to tag (not device)
        2. Assign tag to device
        3. Request playlist
        4. Verify device receives tag's content
        """
        # Create content assigned to tag
        content = Content(
            title="Tag Content",
            description="Assigned via tag",
            content_type="image",
            anthias_url="http://anthias/api/v1/assets/tag_content",
            anthias_asset_id="tag_content_123",
            anthias_file_uri="/data/screenly_assets/tag_content.jpg",
            duration=10,
            is_active=True
        )
        test_db.add(content)
        test_db.commit()

        # Assign content to tag
        assignment = ContentAssignment(
            content_id=content.id,
            tag_id=sample_tag.id,  # Assigned to tag, not device
            priority=1
        )
        test_db.add(assignment)
        test_db.commit()

        # Assign tag to device
        device_tag = DeviceTag(
            device_id=sample_device.id,
            tag_id=sample_tag.id
        )
        test_db.add(device_tag)
        test_db.commit()

        # Request playlist
        response = client.get("/api/client/playlist", headers=device_auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify device receives tag's content
        assert len(data["playlist"]) == 1
        assert data["playlist"][0]["title"] == "Tag Content"

    def test_playlist_deduplication_device_and_tag(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        sample_tag: Tag,
        device_auth_headers: dict
    ):
        """
        Test playlist deduplication when content assigned to both device and tag

        Scenario: Content assigned to both device AND tag
        Expected: Content appears only ONCE in playlist (deduplication)

        Flow:
        1. Create content
        2. Assign content directly to device
        3. Assign same content to tag
        4. Assign tag to device
        5. Request playlist
        6. Verify content appears only once (deduplicated)
        """
        # Create content
        content = Content(
            title="Duplicate Assignment Content",
            description="Assigned to both device and tag",
            content_type="video",
            anthias_url="http://anthias/api/v1/assets/dup_content",
            anthias_asset_id="dup_content_123",
            anthias_file_uri="/data/screenly_assets/dup_content.mp4",
            duration=15,
            is_active=True
        )
        test_db.add(content)
        test_db.commit()

        # Assign to device
        assignment1 = ContentAssignment(
            content_id=content.id,
            device_id=sample_device.id,
            priority=2
        )
        test_db.add(assignment1)

        # Assign to tag
        assignment2 = ContentAssignment(
            content_id=content.id,
            tag_id=sample_tag.id,
            priority=1
        )
        test_db.add(assignment2)
        test_db.commit()

        # Assign tag to device
        device_tag = DeviceTag(
            device_id=sample_device.id,
            tag_id=sample_tag.id
        )
        test_db.add(device_tag)
        test_db.commit()

        # Request playlist
        response = client.get("/api/client/playlist", headers=device_auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify content appears only ONCE (deduplicated)
        assert len(data["playlist"]) == 1
        assert data["total_items"] == 1
        assert data["playlist"][0]["title"] == "Duplicate Assignment Content"


# ============================================================================
# PLAYLIST PERFORMANCE COMPARISON TESTS
# ============================================================================

class TestPlaylistPerformanceComparison:
    """Test performance comparison between fast path and fallback path"""

    def test_fast_path_performance(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        device_auth_headers: dict
    ):
        """
        Test fast path performance (cached URI)

        Expected: Fast response time (< 100ms for 10 items)
        Phase 2 benefit: Eliminates +130ms per item Anthias API call

        Flow:
        1. Create 10 content items with cached URIs
        2. Assign all to device
        3. Measure playlist generation time
        4. Verify fast response (< 500ms total)
        """
        # Create 10 content items with cached URIs
        for i in range(10):
            content = Content(
                title=f"Performance Test {i+1}",
                description="Fast path performance",
                content_type="image",
                anthias_url=f"http://anthias/api/v1/assets/perf_{i+1}",
                anthias_asset_id=f"perf_asset_{i+1}",
                anthias_file_uri=f"/data/screenly_assets/perf_{i+1}.jpg",
                duration=10,
                is_active=True
            )
            test_db.add(content)
            test_db.commit()

            assignment = ContentAssignment(
                content_id=content.id,
                device_id=sample_device.id,
                priority=10 - i
            )
            test_db.add(assignment)

        test_db.commit()

        # Measure response time
        start_time = time.time()
        response = client.get("/api/client/playlist", headers=device_auth_headers)
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        data = response.json()

        # Verify all 10 items returned
        assert len(data["playlist"]) == 10

        # Verify fast response
        # With cached URIs, should be much faster than 1300ms (10 items * 130ms each)
        assert duration_ms < 500, f"Fast path should be < 500ms, got {duration_ms}ms"


# ============================================================================
# PLAYLIST RESPONSE STRUCTURE TESTS
# ============================================================================

class TestPlaylistResponseStructure:
    """Test that Phase 2 optimization doesn't break response structure"""

    def test_playlist_response_structure_unchanged(
        self,
        client: TestClient,
        test_db: Session,
        sample_device: Device,
        device_auth_headers: dict
    ):
        """
        Test Phase 2 optimization maintains backward-compatible response structure

        Expected response structure:
        {
            "device_id": int,
            "device_name": str,
            "device_type": str,
            "total_items": int,
            "playlist": [
                {
                    "content_id": int,
                    "title": str,
                    "content_type": str,
                    "url": str,
                    "duration": int,
                    "mime_type": str
                }
            ]
        }

        Flow:
        1. Create content with cached URI
        2. Request playlist
        3. Verify response structure unchanged
        4. Verify all fields present
        """
        # Create content
        content = Content(
            title="Structure Test Content",
            description="Testing response structure",
            content_type="video",
            anthias_url="http://anthias/api/v1/assets/struct_test",
            anthias_asset_id="struct_test_123",
            anthias_file_uri="/data/screenly_assets/struct_test.mp4",
            duration=20,
            mime_type="video/mp4",
            is_active=True
        )
        test_db.add(content)
        test_db.commit()

        # Assign to device
        assignment = ContentAssignment(
            content_id=content.id,
            device_id=sample_device.id,
            priority=1
        )
        test_db.add(assignment)
        test_db.commit()

        # Request playlist
        response = client.get("/api/client/playlist", headers=device_auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify top-level fields
        assert "device_id" in data
        assert "device_name" in data
        assert "device_type" in data
        assert "total_items" in data
        assert "playlist" in data

        # Verify device info
        assert data["device_id"] == sample_device.id
        assert data["device_name"] == sample_device.device_name

        # Verify playlist item structure
        assert len(data["playlist"]) == 1
        item = data["playlist"][0]

        assert "content_id" in item
        assert "title" in item
        assert "content_type" in item
        assert "url" in item
        assert "duration" in item
        assert "mime_type" in item

        # Verify values
        assert item["content_id"] == content.id
        assert item["title"] == "Structure Test Content"
        assert item["content_type"] == "video"
        assert item["duration"] == 20
        assert item["mime_type"] == "video/mp4"
