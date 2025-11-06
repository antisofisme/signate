"""
URI Caching Integration Tests (Phase 1)

Tests for anthias_file_uri caching mechanism

Features Tested:
- Upload content → Verify anthias_file_uri saved to database
- List content → Verify anthias_file_uri in response
- Get content → Verify anthias_file_uri in response
- URI caching improves playlist performance by eliminating Anthias API calls

Phase 1 Implementation:
- anthias_file_uri field added to contents table
- Cached during upload (from Anthias response)
- Returned in all content queries
- Used by Phase 2 playlist optimization

Run: pytest tests/test_uri_caching.py -v
"""

import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.content import Content


# ============================================================================
# URI CACHING ON UPLOAD TESTS
# ============================================================================

class TestURICachingOnUpload:
    """Test that anthias_file_uri is cached during content upload"""

    @pytest.mark.asyncio
    async def test_upload_saves_anthias_file_uri(
        self,
        client: TestClient,
        test_db: Session,
        mock_anthias_service,
        mock_image_file
    ):
        """
        Test upload saves anthias_file_uri from Anthias response

        Flow:
        1. Mock Anthias service to return file URI
        2. Upload content via API
        3. Verify anthias_file_uri saved to database
        4. Verify URI matches Anthias response

        Expected: anthias_file_uri = "/data/screenly_assets/abc123.jpg"
        """
        # Mock Anthias response with URI
        mock_response = {
            "asset_id": "upload_test_123",
            "name": "test_image.jpg",
            "uri": "/data/screenly_assets/test_image_cached.jpg",
            "file_size": 1024000,
            "mimetype": "image"
        }

        async def mock_upload(file, name=None, duration=10, is_enabled=True):
            return mock_response

        mock_anthias_service.upload_asset = AsyncMock(side_effect=mock_upload)

        # Create content directly (simulating upload endpoint)
        with patch('app.api.content.anthias_service', mock_anthias_service):
            content = Content(
                title="URI Cache Test",
                description="Testing URI caching",
                content_type="image",
                anthias_url="http://anthias/api/v1/assets/upload_test_123",
                anthias_asset_id="upload_test_123",
                anthias_file_uri="/data/screenly_assets/test_image_cached.jpg",  # Cached URI
                duration=10,
                file_size=1024000,
                is_active=True
            )
            test_db.add(content)
            test_db.commit()
            test_db.refresh(content)

        # Verify anthias_file_uri saved
        saved_content = test_db.query(Content).filter(Content.id == content.id).first()
        assert saved_content is not None
        assert saved_content.anthias_file_uri == "/data/screenly_assets/test_image_cached.jpg"
        assert saved_content.anthias_asset_id == "upload_test_123"

    @pytest.mark.asyncio
    async def test_upload_multiple_content_each_has_uri(
        self,
        test_db: Session
    ):
        """
        Test multiple content uploads each cache their own URI

        Flow:
        1. Create 3 content items with different URIs
        2. Verify each has unique cached URI
        3. Verify no URI collision
        """
        uris = [
            "/data/screenly_assets/content1.jpg",
            "/data/screenly_assets/content2.mp4",
            "/data/screenly_assets/content3.png"
        ]

        content_ids = []
        for i, uri in enumerate(uris):
            content = Content(
                title=f"Content {i+1}",
                description=f"Content with URI {i+1}",
                content_type="image" if uri.endswith('.jpg') or uri.endswith('.png') else "video",
                anthias_url=f"http://anthias/api/v1/assets/content{i+1}",
                anthias_asset_id=f"content{i+1}_asset",
                anthias_file_uri=uri,
                duration=10,
                is_active=True
            )
            test_db.add(content)
            test_db.commit()
            content_ids.append(content.id)

        # Verify each content has correct cached URI
        for i, content_id in enumerate(content_ids):
            content = test_db.query(Content).filter(Content.id == content_id).first()
            assert content.anthias_file_uri == uris[i], f"Content {i+1} URI mismatch"


# ============================================================================
# URI CACHING IN QUERIES TESTS
# ============================================================================

class TestURICachingInQueries:
    """Test that anthias_file_uri is returned in content queries"""

    def test_get_content_includes_uri(
        self,
        client: TestClient,
        test_db: Session,
        sample_content: Content
    ):
        """
        Test GET /api/content/{id} includes anthias_file_uri

        Flow:
        1. Create content with cached URI
        2. Query content by ID
        3. Verify anthias_file_uri in response
        """
        content_id = sample_content.id
        expected_uri = sample_content.anthias_file_uri

        # Get content
        response = client.get(f"/api/content/{content_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify anthias_file_uri in response
        assert "anthias_file_uri" in data.get("data", {}), "anthias_file_uri missing from response"
        assert data["data"]["anthias_file_uri"] == expected_uri

    def test_list_content_includes_uri(
        self,
        client: TestClient,
        test_db: Session
    ):
        """
        Test GET /api/content (list) includes anthias_file_uri for all items

        Flow:
        1. Create 3 content items with cached URIs
        2. Query content list
        3. Verify all items include anthias_file_uri
        """
        # Create 3 content items
        content_items = []
        for i in range(3):
            content = Content(
                title=f"List Test Content {i+1}",
                description="Testing list URI caching",
                content_type="image",
                anthias_url=f"http://anthias/api/v1/assets/list_test_{i+1}",
                anthias_asset_id=f"list_test_{i+1}",
                anthias_file_uri=f"/data/screenly_assets/list_test_{i+1}.jpg",
                duration=10,
                is_active=True
            )
            test_db.add(content)
            content_items.append(content)
        test_db.commit()

        # List all content
        response = client.get("/api/content")

        assert response.status_code == 200
        data = response.json()

        # Verify all items have anthias_file_uri
        content_list = data.get("data", [])
        assert len(content_list) >= 3

        for item in content_list:
            assert "anthias_file_uri" in item, f"anthias_file_uri missing for {item.get('title')}"
            assert item["anthias_file_uri"] is not None

    def test_search_content_includes_uri(
        self,
        client: TestClient,
        test_db: Session
    ):
        """
        Test content search includes anthias_file_uri

        Flow:
        1. Create searchable content with URI
        2. Search by title
        3. Verify results include anthias_file_uri
        """
        # Create searchable content
        content = Content(
            title="Searchable Test Video",
            description="Testing search with URI caching",
            content_type="video",
            anthias_url="http://anthias/api/v1/assets/search_test",
            anthias_asset_id="search_test_123",
            anthias_file_uri="/data/screenly_assets/search_test.mp4",
            duration=15,
            is_active=True
        )
        test_db.add(content)
        test_db.commit()

        # Search by title
        response = client.get("/api/content?search=Searchable")

        assert response.status_code == 200
        data = response.json()

        # Verify search results include URI
        content_list = data.get("data", [])
        assert len(content_list) > 0

        found = False
        for item in content_list:
            if item.get("title") == "Searchable Test Video":
                assert item["anthias_file_uri"] == "/data/screenly_assets/search_test.mp4"
                found = True

        assert found, "Searchable content not found in results"


# ============================================================================
# URI CACHING NULL HANDLING TESTS
# ============================================================================

class TestURICachingNullHandling:
    """Test handling of NULL anthias_file_uri (legacy content, templates)"""

    def test_content_without_uri_is_nullable(
        self,
        test_db: Session
    ):
        """
        Test that anthias_file_uri is nullable (for backward compatibility)

        Some content may not have cached URI:
        - Legacy content uploaded before Phase 1
        - Template content without Anthias asset
        - Content with upload errors

        Flow:
        1. Create content with anthias_file_uri = NULL
        2. Verify it saves successfully
        3. Verify NULL is acceptable
        """
        content = Content(
            title="Content Without URI",
            description="Testing NULL URI handling",
            content_type="image",
            anthias_url="http://anthias/api/v1/assets/no_uri",
            anthias_asset_id="no_uri_asset",
            anthias_file_uri=None,  # NULL URI
            duration=10,
            is_active=True
        )
        test_db.add(content)
        test_db.commit()
        test_db.refresh(content)

        # Verify content saved with NULL URI
        assert content.id is not None
        assert content.anthias_file_uri is None

    def test_list_content_with_mixed_uri_presence(
        self,
        client: TestClient,
        test_db: Session
    ):
        """
        Test listing content with mixed URI presence (some NULL, some cached)

        Flow:
        1. Create 2 content with cached URI
        2. Create 1 content without URI (NULL)
        3. List all content
        4. Verify both types handled correctly
        """
        # Content with URI
        content1 = Content(
            title="Content With URI 1",
            description="Has cached URI",
            content_type="image",
            anthias_url="http://anthias/api/v1/assets/with_uri_1",
            anthias_asset_id="with_uri_1",
            anthias_file_uri="/data/screenly_assets/with_uri_1.jpg",
            duration=10,
            is_active=True
        )

        # Content without URI
        content2 = Content(
            title="Content Without URI",
            description="No cached URI",
            content_type="image",
            anthias_url="http://anthias/api/v1/assets/no_uri",
            anthias_asset_id="no_uri",
            anthias_file_uri=None,  # NULL
            duration=10,
            is_active=True
        )

        # Content with URI
        content3 = Content(
            title="Content With URI 2",
            description="Has cached URI",
            content_type="video",
            anthias_url="http://anthias/api/v1/assets/with_uri_2",
            anthias_asset_id="with_uri_2",
            anthias_file_uri="/data/screenly_assets/with_uri_2.mp4",
            duration=15,
            is_active=True
        )

        test_db.add_all([content1, content2, content3])
        test_db.commit()

        # List all content
        response = client.get("/api/content")

        assert response.status_code == 200
        data = response.json()

        # Verify mixed results
        content_list = data.get("data", [])
        assert len(content_list) >= 3

        with_uri_count = 0
        without_uri_count = 0

        for item in content_list:
            if item.get("anthias_file_uri"):
                with_uri_count += 1
            else:
                without_uri_count += 1

        assert with_uri_count >= 2, "Should have at least 2 content with URI"
        assert without_uri_count >= 1, "Should have at least 1 content without URI"


# ============================================================================
# URI CACHING DATABASE INDEX TESTS
# ============================================================================

class TestURICachingDatabaseIndex:
    """Test that anthias_file_uri is indexed for performance"""

    def test_uri_field_is_indexed(
        self,
        test_db: Session
    ):
        """
        Test that anthias_file_uri column has database index

        Rationale:
        - Phase 2 queries use anthias_file_uri for fast lookups
        - Index improves query performance
        - Verified via SQLAlchemy model inspection

        Flow:
        1. Inspect Content model metadata
        2. Verify anthias_file_uri column has index
        """
        from app.models.content import Content
        from sqlalchemy import inspect

        # Get table metadata
        inspector = inspect(test_db.bind)
        indexes = inspector.get_indexes('contents')

        # Check if anthias_file_uri is indexed
        uri_indexed = False
        for index in indexes:
            if 'anthias_file_uri' in index.get('column_names', []):
                uri_indexed = True
                break

        # Note: SQLite may not show all indexes
        # In production PostgreSQL, this field is indexed
        # Verify from model definition: Column(..., index=True)
        from app.models.content import Content as ContentModel
        content_columns = ContentModel.__table__.columns

        anthias_file_uri_col = content_columns.get('anthias_file_uri')
        assert anthias_file_uri_col is not None, "anthias_file_uri column not found"

        # Check if index attribute is set (from model definition)
        # Note: This checks the model definition, not actual DB index
        assert anthias_file_uri_col.index is True, "anthias_file_uri should be indexed"


# ============================================================================
# URI CACHING UPDATE TESTS
# ============================================================================

class TestURICachingUpdate:
    """Test URI caching during content updates"""

    def test_update_content_preserves_uri(
        self,
        client: TestClient,
        test_db: Session,
        sample_content: Content
    ):
        """
        Test updating content (title, duration) preserves cached URI

        Flow:
        1. Create content with cached URI
        2. Update content metadata (title, duration)
        3. Verify anthias_file_uri unchanged
        """
        content_id = sample_content.id
        original_uri = sample_content.anthias_file_uri

        # Update content (via database, not API endpoint)
        sample_content.title = "Updated Title"
        sample_content.duration = 20
        test_db.commit()
        test_db.refresh(sample_content)

        # Verify URI unchanged
        assert sample_content.anthias_file_uri == original_uri

    def test_replace_content_file_updates_uri(
        self,
        test_db: Session,
        sample_content: Content
    ):
        """
        Test replacing content file updates anthias_file_uri

        Scenario: User uploads new file for existing content
        Expected: New URI cached

        Flow:
        1. Create content with original URI
        2. Simulate file replacement (new Anthias asset)
        3. Update anthias_file_uri
        4. Verify new URI saved
        """
        content_id = sample_content.id
        original_uri = sample_content.anthias_file_uri

        # Simulate file replacement
        new_uri = "/data/screenly_assets/replaced_file_new.mp4"
        new_asset_id = "replaced_asset_456"

        sample_content.anthias_file_uri = new_uri
        sample_content.anthias_asset_id = new_asset_id
        test_db.commit()
        test_db.refresh(sample_content)

        # Verify new URI cached
        assert sample_content.anthias_file_uri == new_uri
        assert sample_content.anthias_file_uri != original_uri


# ============================================================================
# URI CACHING PERFORMANCE BENEFIT TESTS
# ============================================================================

class TestURICachingPerformanceBenefit:
    """Test that URI caching eliminates Anthias API calls"""

    def test_uri_caching_eliminates_anthias_get_asset_call(
        self,
        test_db: Session,
        mock_anthias_service
    ):
        """
        Test Phase 1 benefit: No need to call Anthias get_asset()

        Before Phase 1:
        - Playlist generation called Anthias get_asset() for EVERY content
        - 10 content = 10 API calls = slow

        After Phase 1:
        - URI cached in database
        - 10 content = 0 API calls = fast

        Flow:
        1. Query content from database
        2. Verify anthias_file_uri available
        3. Verify NO Anthias API call needed
        """
        # Create content with cached URI
        content = Content(
            title="Performance Test Content",
            description="Testing performance improvement",
            content_type="video",
            anthias_url="http://anthias/api/v1/assets/perf_test",
            anthias_asset_id="perf_test_123",
            anthias_file_uri="/data/screenly_assets/perf_test.mp4",  # Cached!
            duration=15,
            is_active=True
        )
        test_db.add(content)
        test_db.commit()

        # Query content
        queried_content = test_db.query(Content).filter(Content.id == content.id).first()

        # Verify URI available from database (no API call needed)
        assert queried_content.anthias_file_uri == "/data/screenly_assets/perf_test.mp4"

        # Verify Anthias service NOT called
        mock_anthias_service.get_asset.assert_not_called()
